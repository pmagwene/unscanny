import sys
import time, datetime
import threading, sched
import dataclasses


import click

from util import (HHMMSS, RunSettings, ScannerSettings, PowerSettings, RunData, quick_scan)
import tifffile as TIFF


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
      img = quick_scan({},test=True)
    else:
      print(dataclasses.asdict(scansettings))
      img = quick_scan(dataclasses.asdict(scansettings))
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
@click.option("-u", "--user",
              help = "Last name of investigator",
              type = str,
              prompt = True)
@click.option("-e", "--experiment",
              help = "Name of experiment",
              type = str,
              prompt = True)
@click.option("-i", "--interval",
              help = "Interval between scans (mins)",
              type = click.IntRange(1, 2880),
              prompt = True,
              default = 30)
@click.option("-n", "--nscans",
              help = "Total number of scans",
              type=click.IntRange(0, 9999),
              prompt = True,
              default=1)
@click.option("-d", "--delay",
              help = "Delay before first scan (mins)",
              type=click.IntRange(0, 9999),
              prompt = True,
              default=0)
@click.option("-m", "--mode",
              help = 'Scan mode',
              type = click.Choice(["Gray","Color"]),
              prompt = True,
              default = "Gray")
@click.option("-s", "--source",
              help = 'Scan source',
              type = click.Choice(["TPU8x10", "Flatbed"]),
              prompt = True,
              default = "TPU8x10")
@click.option("-r", "--resolution",
              help = "Scanner resolution (dpi)",
              type = int,
              prompt = True,
              default = 300)
@click.option("-b", "--bit-depth",
              help = "Bit depth per pixel",
              type=click.Choice(([8,16])),
              prompt = True,
              default=16)
@click.option("--powermodule",
              help = "Module name of power manager",
              type = str,
              prompt = True,
              default = "nullpower")
@click.option("--powerip",
              help = "IP address of power manager",
              type = str,
              prompt = True,
              default = "192.168.1.100")
@click.option("--poweruser",
              help = "Username for power manager",
              type = str,
              prompt = True,
              default = "admin")
@click.option("--powerpass",
              help = "Password of power manager",
              type = str,
              prompt = True,
              default = "admin")
@click.option("--outlet",
              help = "Outlet # of power manager",
              type=click.IntRange(1, 16),
              prompt = True,
              default = 1)
def cli(user, experiment, interval, nscans, delay,
                       mode, source, resolution, bit_depth,
                       powermodule, powerip, poweruser, powerpass, outlet):
    run = RunSettings(user = user, experiment = experiment,
                     interval = interval, nscans = nscans, delay = delay)
    scanner = ScannerSettings(mode = mode, source = source, resolution = resolution,
                         depth = bit_depth)
    power = PowerSettings(module = powermodule, address = powerip, 
                       username = poweruser, password = powerpass, outlet = outlet)

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
        scan(scanner, rundata)
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






