from __future__ import print_function, division
import sys
import threading
import time, datetime
import textwrap
import curses

import click                   # library for building CLIs
import pick                    # curses library for picking from lists

import scanfunctions
import uncursed
import unsettings
import settings



def scanner_settings_str(settings):
    s = """\
    Scanner Settings
    ----------------
    Source: {}
    Mode: {}
    Resolution: {}
    Depth: {}
    """
    s = textwrap.dedent(s)
    return s.format(settings.source, settings.mode,
                    settings.resolution, settings.depth)
    
    
def run_settings_str(settings):
    s = """\
    Run Settings
    ------------
    User: {}
    Experiment: {}
    Interval: {}
    # of Scans: {}
    """
    s = textwrap.dedent(s)
    return s.format(settings.user, settings.experiment,
                    settings.interval, settings.nscans)

def choose_scanner(testing=False):
    """Query for available scanners and return users choice.
    """
    if testing:
        return "test driver", dict()
    scanfunctions.initialize_driver()
    scanners = scanfunctions.get_scanners()
    if not len(scanners):
        return None, None
    title = """Pick the scanner to use."""\
            """Up/Down arrow keys to select, Enter to accept."""
    choice, index = pick.pick(scanners, title)
    device_name = choice[0]
    return choice, scanfunctions.open_scanner(device_name)
    
    
def run_scanner_loop(screen, scanner, run_data, scan_func = scanfunctions.scan):
    screen.clear()
    screen.nodelay(1)  # make getch() non-blocking

    # Setup screen
    nrow, ncol = screen.getmaxyx()
    txt = """Scanning initiated.\n"""\
          """Press Capital <Q> to abort."""
    uncursed.add_multiline_str(screen,
                               uncursed.centered_ycoord(screen, txt),
                               uncursed.centered_xcoord(screen, txt),
                               txt)
    curses.curs_set(0)
    screen.refresh()

    # Run first scan 
    run_data.t_start = datetime.datetime.now()
    run_data.t_lastscan = None
    run_data.ct_nextscan = 0
    run_data = scan_func(scanner, run_data)

    # Update status bar
    uncursed.set_status_bar(screen,
        "Scan {} at {}".format(run_settings.ct_nextscan - 1,
                               run_settings.t_lastscan.ctime()))

    # Run loop for remaining scans
    while run_data.ct_nextscan < run_data.nscans:

        # threading.Timer wants interval in secs, run_settings.interval in mins
        timer = threading.Timer(run_data.interval * 60, 
                                scan_func,
                                [scanner, run_data])
        timer.start()

        # while waiting for next scan, poll for abort key press
        while timer.is_alive():
            c = screen.getch()
            if c == ord("Q"):
                timer.cancel()
                return False
            else:
                time.sleep(1)
                screen.refresh()
                continue

        # update status bar after each scan
        uncursed.set_status_bar(screen,
            "Scan {} at {}".format(run_data.ct_nextscan - 1,
                                   run_data.t_lastscan.ctime()))
    return True
                
                                
        
class RunData(object):
    def __init__(self, run_settings):
        for (key,val) in run_settings.iteritems():
            self.__dict__[key] = val
        self.ct_nextscan = 0
        self._log = []
        self.t_start = None
        self.t_lastscan = None
        self.successful = False
        self.scanner_settings_file = None
        self.run_settings_file = None

    def log(self, entry):
        self._log.append(entry)
            


@click.command()
@click.argument("scanner_file", type = click.Path(exists=True))
@click.argument("run_file", type = click.Path(exists=True))
def runit(scanner_file, run_file):
    """Given scanner and run settings file, initiate scanning run.
    """
    # Load settings files
    scanner_settings = settings.load_config(scanner_file, "scanner")
    run_settings = settings.load_config(run_file, "run")

    # Create run data object
    run_data = RunData(run_settings)
    run_data.scanner_settings_file = scanner_file
    run_data.run_settings_file = run_file

    # Clear screen and show settings
    click.clear()
    print("Welcome to Unscanny -- A program for time series scanner imaging")
    print()
    print("Current settings")
    print("================")
    print()
    print(run_settings_str(run_settings))
    print()
    print(scanner_settings_str(scanner_settings))
    print()
    
    # Confirm settings are correct
    if not click.confirm("Are these settings correct?", default=True):
        click.echo("Exiting: User indicated incorrect settings.")
        run_data.log("Aborted: incorrect run/scanner settings.")
        return run_data

    # Create run data object
    run_data = RunData(run_settings)

    # Pick scanner from list of discovered scanners
    while True:
        click.pause("Press any key to continue to scanner menu...")
        device_info, scanner = choose_scanner()
        if scanner is None:
            if not click.confirm("No scanner found. Retry?"):
                click.echo("Exiting: no scanner found")
                run_data.log("Aborted: no scanner found")
                return run_data
            continue
        break

    # Apply settings to device
    scanner_settings.device_info = device_info
    scanfunctions.apply_scanner_settings(scanner, scanner_settings)

    # Confirm begin scanning
    if not click.confirm(
            "\nUsing scanner at {}. Begin scanning?".format(device_info[0]),
            default = True):
        click.echo("Exiting: User exited before scanning.")
        run_data.log("Aborted: user exited before scanning")
        return run_data

    # enter scanner loop
    run_data = curses.wrapper(run_scanner_loop,
                              scanner,
                              scanner_settings, run_settings)



@click.group()
def cli():
    pass

cli.add_command(unsettings.setrun)
cli.add_command(unsettings.setscanner)
cli.add_command(runit)

if __name__ == "__main__":
    cli()
