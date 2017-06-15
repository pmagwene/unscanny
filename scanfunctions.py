from __future__ import print_function
import time, datetime
import threading

import sane
import numpy as np
from libtiff import TIFF


def initialize_driver():
    return sane.init()

def get_scanners(localOnly=True):
    return sane.get_devices(localOnly)

def open_scanner(device_name):
    return sane.open(device_name)

    
def apply_scanner_settings(scanner, settings):
    scanner.mode = settings.mode
    scanner.source = settings.source
    scanner.resolution = settings.resolution
    scanner.depth = settings.depth
    return scanner

def scan_at_interval(scanner, runsettings):
    ct = 0
    while ct < runsettings.nscans:
        timer = threading.Timer(runsettings["interval"],
                                scan, runsettings, ct)
        timer.start()
        while timer.is_alive():
            continue
        ct += 1
    

def fake_scan(scanner, run_settings):
    """A function for testing program logic w/out actually scanning.
    """
    t_now = datetime.datetime.now()
    print("Scanning at {}".format(t_now.ctime()))
    run_settings.t_lastscan = t_now()
    run_settings.ct_nextscan += 1
    return run_settings


def scan(scanner, run_settings):
    t_scan = datetime.datetime.now()
    fname = construct_image_name(run_settings.t_start,
                                 run_settings.user,
                                 run_settings.experiment,
                                 run_settings.ct_nextscan,
                                 t_scan)

    # run scan and save image
    imgarray = scanner.arr_scan()
    write_array_to_TIFF(imgarray, fname)

    # update run variables
    run_settings.t_lastscan = t_scan
    run_settings.ct_nextscan += 1
    return run_settings
    


def write_array_to_TIFF(arr, name):
    tiff = TIFF.open(name, mode="w")
    tiff.write_image(np.squeeze(arr))
    tiff.close()



def construct_image_name(begintime, investigator, experiment,
                         ninterval, timept=None):
    if timept is None:
        timept = datetime.datetime.now()
    beginstr = begintime.strftime("%Y-%m-%d")
    timestr = timept.strftime("%Y%m%dT%H%M%S")
    return "{}-{}-{}-{:04d}-{}.tif".format(beginstr, investigator, experiment,
                                           ninterval, timestr)
