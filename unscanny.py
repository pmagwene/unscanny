#!/usr/bin/env python
"""
unscanny.py -- a Python program for time series imaging using scanners

(c) 2017, Paul M. Magwene

Flow of logic for core scanning routines:

runit ->
  _runit ->
    choose_scanner
    delay_loop
    scanner_loop
"""

from __future__ import print_function, division
import sys
import threading
import time, datetime
import textwrap
import uuid
import curses
from string import Formatter

import click                   # library for building CLIs
import pick                    # curses library for picking from lists

import settings
import scanfunctions
import uncursed
import unsettings


def strfdelta(tdelta, fmt):
    """ string representation of timedelta object.

    Code from: https://stackoverflow.com/a/17847006
    """
    f = Formatter()
    d = {}
    l = {'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    k = map( lambda x: x[1], list(f.parse(fmt)))
    rem = int(tdelta.total_seconds())

    for i in ('D', 'H', 'M', 'S'):
        if i in k and i in l.keys():
            d[i], rem = divmod(rem, l[i])

    return f.format(fmt, **d)

def HHMMSS(tdelta):
    return strfdelta(tdelta, "{H:02}:{M:02}:{S:02}")

def time_until(t_end, t_now = None):
    if t_now is None:
        t_now = datetime.datetime.now()
    return t_end - t_now



class RunData(object):
    """ A class to represent information associated with a run.
    """
    def __init__(self, run_settings, scanner_settings):
        for (key,val) in run_settings.iteritems():
            self.__dict__[key] = val
        self.run_settings = run_settings
        self.scanner_settings = scanner_settings
        self.ct_nextscan = 0
        self._log = []
        self.t_start = None
        self.t_lastscan = None
        self.successful = False
        self.scanner_settings_file = None
        self.run_settings_file = None
        self.basedir = "."
        self.initial_delay = 0
        self.succesful = False
        self.UID = self.generate_id()

    def log(self, entry):
        self._log.append(entry)

    def generate_id(self):
        UUID = str(uuid.uuid4())
        return UUID.split('-')[0]

    def base_fname(self):
        """ Base filename for run.
        """
        return "{}-{}-{}-{}".format(
            self.t_start.strftime("%Y-%m-%d"),
            self.user, self.experiment, self.UID)

    def current_fname(self, timept = None):
        """ Appropriate filename for current stage of run.
        """
        if timept is None:
            timept = datetime.datetime.now()
        timestr = timept.strftime("%Y%m%dT%H%M%S")
        return "{}-{:04d}-{}".format(self.base_fname(),
                                     self.ct_nextscan,
                                     timestr)

    def generate_report(self):
        idstr = "UID: {}".format(self.ID)
        scanset = settings.formatted_settings_str(self.scanner_settings,
                                                  "Scanner Settings")
        runset = settings.formatted_settings_str(self.run_settings,
                                                 "Run Settings")
        startstr = "Start time:"
        if self.t_start is not None:
            startstr = "Start time: {}".format(self.t_start.isoformat())
        endstr = "End time:"
        if self.t_lastscan is not None:
            endstr = "End time: {}".format(self.t_lastscan.isoformat()) 
        totalstr = "Completed scans: {}".format(self.ct_nextscan)
        succstr = "Run successful: {}".format(self.successful)
        logstr = "Log:\n\t{}".format("\n\t".join(self._log))
        parts = [idstr, scanset, runset, startstr, endstr,
                 totalstr, succstr, logstr]
        reportstr = "\n\n".join(parts)
        return reportstr



#  _   _ ___                   _    ____                 _                _      
# | | | |_ _|   __ _ _ __   __| |  / ___|___  _ __ ___  | |    ___   __ _(_) ___ 
# | | | || |   / _` | '_ \ / _` | | |   / _ \| '__/ _ \ | |   / _ \ / _` | |/ __|
# | |_| || |  | (_| | | | | (_| | | |__| (_) | | |  __/ | |__| (_) | (_| | | (__ 
#  \___/|___|  \__,_|_| |_|\__,_|  \____\___/|_|  \___| |_____\___/ \__, |_|\___|
#                                                                   |___/        


def choose_scanner():
    """Query for available scanners and return users choice.
    """
    # initialize driver and get list of available scanners
    scanfunctions.initialize_driver()
    scanners = scanfunctions.get_scanners()
    if not len(scanners):
        return None, None

    # pick scanner using curses interface
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

    # figure out end time
    t_now = datetime.datetime.now()
    t_end = t_now + datetime.timedelta(minutes = delay_in_mins)
    waitstr = HHMMSS(t_end - t_now)
    
    # set status bar
    uncursed.set_status_bar(screen,
            "Time until first scan: {}".format(waitstr))
    screen.refresh()

    # delay loop
    while datetime.datetime.now() < t_end:
        time.sleep(1)

        # update status bar
        waitstr = HHMMSS(time_until(t_end))
        uncursed.set_status_bar(screen,
                "Time until first scan: {}".format(waitstr))
        screen.refresh()

        # check for abort key
        c = screen.getch()
        if c == ord("Q"):
            return False

    return True
    
    
def scanner_loop(screen, scanner, run_data, scan_func = scanfunctions.scan):
    """ Generate scans at given intervals -> boolean indicating success/failure.

    A useful informational display is provided in a curses window to provide
    details on scans completed and time until next scan.
    """
    screen.clear()              # clear screen
    curses.curs_set(0)          # make cursor invisible
    screen.nodelay(1)           # make getch() non-blocking

    # Setup screen display
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
        t_nextscan = run_data.t_lastscan + \
                     datetime.timedelta(minutes=run_data.interval)

        # run tasks in interval between scans
        while datetime.datetime.now() < t_nextscan:
            time.sleep(1)

            # update status bar
            waitstr = HHMMSS(t_nextscan)
            uncursed.set_status_bar(screen,
                "Scan {} was run at {}. Next scan in {}".format(
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
        
    return True  
                

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
    print(settings.formatted_settings_str(run_settings, "Run Settings"))
    print()
    print(settings.formatted_settings_str(scanner_settings, "Scanner Settings"))
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
    run_data.successful = curses.wrapper(scanner_loop,
                                         scanner, run_data)

    # generate log file
    log_file_name = RunData.base_fname() + ".log"
    with open(log_file_name, "w") as f:
        f.write(RunData.generate_report())

    return run_data



#   ____                                          _       _     _            
#  / ___|___  _ __ ___  _ __ ___   __ _ _ __   __| |     | |   (_)_ __   ___ 
# | |   / _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` |_____| |   | | '_ \ / _ \
# | |__| (_) | | | | | | | | | | | (_| | | | | (_| |_____| |___| | | | |  __/
#  \____\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_|     |_____|_|_| |_|\___|
                                                                           
#  ___       _             __                
# |_ _|_ __ | |_ ___ _ __ / _| __ _  ___ ___ 
#  | || '_ \| __/ _ \ '__| |_ / _` |/ __/ _ \
#  | || | | | ||  __/ |  |  _| (_| | (_|  __/
# |___|_| |_|\__\___|_|  |_|  \__,_|\___\___|
                                           


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
