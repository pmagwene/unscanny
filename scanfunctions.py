from __future__ import print_function
import time, datetime
import threading

import sane
import numpy as np
import tifffile as TIFF


def initialize_driver():
    """Initialize the scanner driver.
    """
    return sane.init()

def get_scanners(localOnly=True):
    """Get list of available scanners.
    """
    return sane.get_devices(localOnly)

def open_scanner(device_name):
    """Prepare scanner for scanning.
    """
    return sane.open(device_name)

def apply_scanner_settings(scanner, settings):
    """Apply info from Settings object to scanner object.
    """
    scanner.mode = settings.mode
    scanner.source = settings.source
    scanner.resolution = settings.resolution
    scanner.depth = settings.depth
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
    t_scan = datetime.datetime.now()

    # base directory name
    basename = construct_base_name(run_data.t_start,
                                   run_data.user,
                                   run_data.experiment,
                                   run_data.ID)

    # specific filename
    fname = construct_image_name(run_data.t_start,
                                 run_data.user,
                                 run_data.experiment,
                                 run_data.ct_nextscan,
                                 t_scan)
    
    # run scan and save image
    imgarray = scanner.arr_scan()
    TIFF.imsave(imgarray, fname, description="Run UID: {}".format(run.ID))

    # update run variables
    run_settings.t_lastscan = t_scan
    run_settings.ct_nextscan += 1
    return run_data



def construct_base_name(begintime, investigator, experiment, UID):
    beginstr = begintime.strftime("%Y-%m-%d")
    return "{}-{}-{}-{}".format(beginstr, investigator, experiment, UID)


def construct_image_name(begintime, investigator, experiment, UID,
                         ninterval, timept=None):
    basestr = construct_base_name(begintime, investigator, experiment, UID)
    if timept is None:
        timept = datetime.datetime.now()
    timestr = timept.strftime("%Y%m%dT%H%M%S")
    return "{}-{}-{}-{:04d}-{}.tif".format(basestr, ninterval, timestr)
