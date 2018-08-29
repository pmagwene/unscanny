import sys
import time, datetime
import threading, sched
import dataclasses

import click
import toml
import tifffile as TIFF

from util import (HHMMSS, RunSettings, ScannerSettings, PowerSettings, RunData)
import unsane


def power_on(powersettings):
    click.echo("Powering on")
    p = powersettings
    mod = __import__(p.module)
    mgr = mod.__dict__[p.module](p.address, p.username, p.password)
    mgr.power_on(p.outlet)

def power_off(powersettings):
    click.echo("Powering off")
    p = powersettings
    mod = __import__(p.module)
    mgr = mod.__dict__[p.module](p.address, p.username, p.password)
    mgr.power_off(p.outlet)    

def scan(scansettings, rundata, test = False):
    click.echo("Scanning...")
    rundata.nscans_completed += 1
    rundata.t_lastscan = datetime.datetime.now()
    if rundata.t_start is None:
        rundata.t_start =  rundata.t_lastscan 
    if test:
        img = unsane.scan("test", unsane.test_settings)
    else:
        devs = unsane.get_scanners()
        img = unsane.scan(devs[0], scansettings.settings)
    TIFF.imsave(rundata.current_fname() + ".tiff", img)
    click.echo("Scan completed at: {}".format(rundata.t_lastscan.strftime("%H:%M:%S")))
    click.echo("File saved as: {}".format(rundata.current_fname() + ".tiff"))

def no_op(*args, **kw):
    return None


def all_settings(run, scan, power):
    s = "\nSETTINGS:\n\n"
    s += "Run settings\n"
    s += "============\n"
    s += str(run) + "\n"
    s += "Scanner settings\n"
    s += "================\n"
    s += str(scan) + "\n"
    s += "Power settings\n"
    s += "==============\n"
    s += str(power) + "\n"
    return s


@click.command()
@click.option("-d", "--delay",
              help = "Delay before first scan (mins)",
              type=click.IntRange(0, 9999),
              prompt = True,
              default=0)
@click.option("--test/", 
              is_flag = True,
              help = "Whether to use scanimage test scanner",
              prompt = False,
              default = False)
@click.argument("settings_file", 
                type = click.Path(exists=True, dir_okay=False))
def cli(settings_file, delay, test):
    settings = toml.load(settings_file)

    run = RunSettings.fromdict(settings["run"])
    run.delay = delay
    scanner = ScannerSettings(settings["scanner"])
    power = PowerSettings.fromdict(settings["power"])

    rundata = RunData(run, scanner, power)

    # Confirm settings are correct
    click.echo("\n" + rundata.settings_str() + "\n")
    if not click.confirm("Are these settings correct?", default=True):
        click.echo("Exiting: User indicated incorrect settings.")
        rundata.log("Aborted: incorrect run/scanner settings.")
        return rundata


    scheduler = sched.scheduler(time.time, time.sleep)

    for i in range(run.nscans):
        if i == 0:
            scheduler.enter(run.delay * 60, 1, no_op)
            t = threading.Thread(target = scheduler.run)
            t.start()
        while not(scheduler.empty()):
            tnext = scheduler.queue[0][0]
            tdelta = datetime.timedelta(seconds = tnext - time.time())
            click.echo("Time until next scan cycle: {}".format(HHMMSS(tdelta)))
            sys.stdout.write("\033[F")
            time.sleep(1)
        if (i + 1) < run.nscans:
            scheduler.enter(run.interval * 60, 1, no_op)
            t = threading.Thread(target=scheduler.run)
            t.start()
        click.echo()
        click.echo("\nCycle {}".format(i+1))
        power_on(power)
        time.sleep(30)  # allow scanner to complete its boot cycle
        scan(scanner, rundata, test = test)
        time.sleep(30)  # allow scanner to reset
        power_off(power) 
        click.echo()

    rundata.t_end = datetime.datetime.now()
    rundata.successful = True

    logfile = rundata.base_fname() + ".log"
    with open(logfile, 'w') as f:
        f.write(rundata.generate_report())

    click.echo("Log file saved as: {}".format(logfile))


if __name__ == "__main__":
    cli()






