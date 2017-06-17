#!/usr/bin/env python

from __future__ import print_function, division
import sys
import threading
import time, datetime
import textwrap
import uuid
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
    Depth: {}"""
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
    # of Scans: {} """
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
    

def delay_loop(screen, delay_in_mins):
    """ A curses loop for a delay screen.
    """
    screen.clear()
    curses.curs_set(0)
    screen.nodelay(1)

    txt = """Waiting to begin first scan.\n"""\
          """Press capital "Q" to cancel wait and abort scanning run."""
    uncursed.add_multiline_str(screen,
            uncursed.centered_ycoord(screen, txt),
            uncursed.centered_xcoord(screen, txt),
            txt)

    delay_in_seconds = delay_in_mins * 60
    waitstr = str(datetime.timedelta(0, delay_in_seconds))
    uncursed.set_status_bar(screen,
            "Time until first scan: {}".format(waitstr))
    screen.refresh()

    # delay loop
    while delay_in_seconds > 0:
        time.sleep(1)
        delay_in_seconds -= 1
        waitstr = str(datetime.timedelta(0, delay_in_seconds))
        uncursed.set_status_bar(screen,
                "Time until first scan: {}".format(waitstr))
        screen.refresh()
        c = screen.getch()
        if c == ord("Q"):
            return False

    return True
    
    
def run_scanner_loop(screen, scanner, run_data, scan_func = scanfunctions.scan):
    """ Generate scans at given intervals -> boolean indicating success/failure.

    A useful informational display is provided in a curses window to provide
    details on scans completed and time until next scan.
    """
    screen.clear()              # clear screen
    curses.curs_set(0)          # make cursor invisible
    screen.nodelay(1)           # make getch() non-blocking

    # Setup screen dispaly
    txt = """Collecting {} scans at {} minute intervals.\n""".format(
        run_data.nscans, run_data.interval)
    txt += """Press capital "Q" to abort."""
    uncursed.add_multiline_str(screen,
                               uncursed.centered_ycoord(screen, txt),
                               uncursed.centered_xcoord(screen, txt),
                               txt)
    uncursed.set_status_bar(screen, "Running first scan...")
    screen.refresh()

    # Run first scan 
    run_data.t_start = datetime.datetime.now()
    run_data.t_lastscan = None
    run_data.ct_nextscan = 0
    run_data = scan_func(scanner, run_data)

    # Update status bar
    uncursed.set_status_bar(screen,
        "Scan {} at {}".format(run_data.ct_nextscan - 1,
                               run_data.t_lastscan.ctime()))
    screen.refresh()

    # Run loop for remaining scans
    while run_data.ct_nextscan < run_data.nscans:

        delay_in_seconds = run_data.interval * 60

        # run tasks in interval between scans
        while delay_in_seconds > 0:
            time.sleep(1)
            delay_in_seconds -= 1

            # update status bar
            waitstr = str(datetime.timedelta(0, delay_in_seconds))
            uncursed.set_status_bar(screen,
                "Scan {} completed at {}. Next scan in {}".format(
                    run_data.ct_nextscan - 1,
                    run_data.t_lastscan.ctime(),
                    waitstr))
            screen.refresh()

            # did we get the abort signal?
            c = screen.getch()
            if c == ord("Q"):
                return False

        # interval completed, update status bar to indicate scanning has begun
        uncursed.set_status_bar("Scanning...")
        screen.refresh()

        # carry out scan
        scan_func(scanner, run_data)
        
        # scan now completed, update status bar again
        uncursed.set_status_bar(screen,
            "Scan {} completed at {}. Next scan in {}".format(
            run_data.ct_nextscan - 1,
            run_data.t_lastscan.ctime(),
            waitstr))
        screen.refresh()
        
    return True  
                
                                
        
class RunData(object):
    def __init__(self, run_settings, scanner_settings):
        for (key,val) in run_settings.iteritems():
            self.__dict__[key] = val
        self.scanner_settings = scanner_settings
        self.ct_nextscan = 0
        self._log = []
        self.t_start = None
        self.t_lastscan = None
        self.successful = False
        self.scanner_settings_file = None
        self.run_settings_file = None
        self.basedir = "."
        self.succeeded = False
        self.UID = self.generate_id()

    def log(self, entry):
        self._log.append(entry)

    def generate_id(self):
        UUID = str(uuid.uuid4())
        return UUID.split('-')[0]

    def generate_report(self):
        idstr = "UID: {}".format(self.ID)
        scanset = scanner_settings_str(self.scanner_settings)
        runset = run_settings_str(self)
        startstr = "Start time:"
        if self.t_start is not None:
            startstr = "Start time: {}".format(self.t_start.isoformat())
        endstr = "End time:"
        if self.t_lastscan is not None:
            endstr = "End time: {}".format(self.t_lastscan.isoformat()) 
        totalstr = "Total scans: {}".format(self.ct_nextscan)
        logstr = "Log:\n\t{}".format("\n\t".join(self._log))
        parts = [idstr, scanset, runset, startstr, endstr, totalstr, logstr]
        reportstr = "\n\n".join(parts)
        return reportstr
        
        
def _runit(scanner_file, run_file):
    """Given scanner and run settings file, initiate scanning run.
    """
    # Load settings files
    scanner_settings = settings.load_config(scanner_file, "scanner")
    run_settings = settings.load_config(run_file, "run")

    # Create run data object
    run_data = RunData(run_settings, scanner_settings)
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
            "\n Are you ready to begin scanning?".format(device_info[0]),
            default = True):
        click.echo("Exiting: User exited before scanning.")
        run_data.log("Aborted: user exited before scanning")
        return run_data

    # get delay time
    init_delay = click.prompt(
        "Delay (in minutes) before first scan (0 = start immediately)?",
                              type = click.IntRange(0, 24*60),
                              default = 0)
    run_data.initial_delay = init_delay

    # run delay loop
    if init_delay > 0:
        finished_delay = curses.wrapper(delay_loop, init_delay)
        if not finished_delay:
            run_data.log("Aborted: user cancelled during initial delay.")
            return run_data
    

    # enter scanner loop
    run_data.succeeded = curses.wrapper(run_scanner_loop,
                                        scanner, run_data)
    return run_data



@click.group()
def cli():
    pass

@click.command()
@click.argument("scanner_file", type = click.Path(exists=True))
@click.argument("run_file", type = click.Path(exists=True))
def runit(scanner_file, run_file):
    _runit(scanner_file, run_file)
    
cli.add_command(unsettings.setrun)
cli.add_command(unsettings.setscanner)
cli.add_command(runit)

if __name__ == "__main__":
    cli()
