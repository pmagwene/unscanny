from __future__ import print_function
import textwrap

import yaml
import click


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
@click.argument("outfile",
                type=click.File("w"),
                default="-")
def setrun(user, experiment, interval, nscans, outfile):
    """Write run settings to a config file (stdout).
    """
    rdict = {"run":
             {"user": user,
              "experiment": experiment,
              "interval": int(interval),
              "nscans": int(nscans)}}
    yaml.safe_dump(rdict, outfile,
                   default_flow_style = False,
                   encoding = "utf-8")


    
@click.command()
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
@click.option("-d", "--depth",
              help = "Bit depth per pixel",
              type=click.Choice(["8", "16"]),
              prompt = True,
              default="16")
@click.argument("outfile",
                type=click.File('w'),
                default='-')
def setscanner(mode, source, resolution, depth, outfile):
    """Write scanner settings to a config file (stdout).
    """
    sdict = {"scanner":
             {"mode": mode,
              "source": source,
              "resolution": int(resolution),
              "depth": int(depth)}}
    yaml.safe_dump(sdict, outfile,
                   default_flow_style = False,
                   encoding = "utf-8")


