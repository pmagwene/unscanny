import sys, time
import argparse

import sane
from gooey import Gooey



def get_scanners():
    sane.init()
    devices = sane.get_devices(True)
    names = [dev[0] for dev in devices] + ["test"]
    return names


@Gooey
def main():

    scanners = get_scanners()
    
    parser = argparse.ArgumentParser(description="Time series imaging with flatbed scanners.")
    
    parser.add_argument('--scanner', type=str, choices = scanners,
            help="Scanner to use")  
    parser.add_argument('--delay', type=int, default = 0,
            help="Delay (in mins) before first scan")  


 

    args = parser.parse_args()

    print "next scan in two minutes..."
    time.sleep(10)
    print "next scan in three minutes..."



if __name__ == "__main__":
    main()