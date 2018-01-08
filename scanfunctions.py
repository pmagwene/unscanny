from __future__ import print_function
import time, datetime


import sane
import numpy as np
import tifffile as TIFF


def initialize_driver():
    """Initialize the scanner driver.
    """
    return sane.init()


def get_scanners(localOnly=True, test = False):
    """Get list of available scanners.
    """
    if test:
        return [("test", "SANE", "SANE", "SANE")]
    return sane.get_devices(localOnly)


def open_scanner(device_name):
    """Prepare scanner for scanning.
    """
    return sane.open(device_name)



def apply_scanner_settings(scanner, settings_dict):
    """Apply info from Settings object to scanner object.
    """
    # mode should always be set first to insure options are active
    if "mode" in settings_dict:
        setattr(scanner, key, settings_dict["mode"])
    for (key, value) in settings_dict.iteritems():
        setattr(scanner, key, value)
    return scanner


def fake_scan(scanner, run_data):
    """A function for testing program logic w/out actually scanning.
    """
    t_now = datetime.datetime.now()
    print("Scanning at {}".format(t_now.ctime()))
    run_data.t_lastscan = t_now()
    run_data.ct_nextscan += 1
    return run_data


def scan(scanner, run_data):
    """Scan and save image based on run settings.
    """
    # get current time
    t_scan = datetime.datetime.now()
    
    # get current filename, with tif extension
    fname = run_data.current_fname(t_scan) + ".tif"
    
    # run scan and save image
    imgarray = scanner.arr_scan()
    beginstr = run_data.t_start.strftime("%Y-%m-%d")
    TIFF.imsave(fname, imgarray,
        description="Run Date: {}; Run UID: {}".format(beginstr,
                                                       run_data.UID))

    # update run variables
    run_data.t_lastscan = t_scan
    run_data.ct_nextscan += 1
    return run_data


def do_scanning(device_name, settings_dict):
    initialize_driver()
    scanner = open_scanner(device_name)
    apply_scanner_settings(scanner, settings_dict)
    imgarray = scanner.arr_scan()
    scanner.close()
    return imgarray

