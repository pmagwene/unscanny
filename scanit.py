#!/usr/bin/env python

import sys
import argparse
import collections

import numpy as np
import tifffile as TIFF
import sane
import click
import toml




def quick_scan(settings = {}, test = False):
    """Make scan using first scanning device found by SANE driver.
    """
    # init and find devices
    sane.init()
    devices = sane.get_devices(localOnly = True)

    if test:
        devices = [("test", "SANE", "SANE", "SANE")]
        settings["source"]= "Flatbed"
        settings["test_picture"] = "Color pattern"
        settings["mode"] = "Color"
        settings["resolution"] = 75
        settings["depth"] = 8

    if not len(devices):
        return None
    dev_name = devices[0][0]

    # open scanner
    scanner = sane.open(dev_name)

    # set options
    if "mode" in settings:
        scanner.mode = settings["mode"]
    for (key, value) in settings.items():
        setattr(scanner, key, value)

    img = scanner.arr_scan()
    scanner.close()
    sane.exit()
    return img    




@click.command()
@click.option("--test/--no-test", default=False, show_default = True,
              help = "Use 'test' scanner backend.")
@click.argument("scanner_file", 
                type = click.Path(exists=True, dir_okay=False))
@click.argument("out_file", 
                type = click.Path(exists=False, dir_okay=False))
def main(scanner_file, out_file, test):
    scanner_settings = toml.load(scanner_file)
    if "scanner" not in scanner_settings:
        print("Scanner info missing from settings file")
        sys.exit(1)
    img = quick_scan(scanner_settings["scanner"], test = test)
    if img is None:
        sys.exit(1)
    TIFF.imsave(out_file, img)



if __name__ == "__main__":
    main()




