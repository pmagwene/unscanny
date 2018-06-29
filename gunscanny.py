import sys, time
import subprocess
import argparse

from gooey import Gooey




@Gooey
def main():


    parser = argparse.ArgumentParser(description="Time series imaging with flatbed scanners.")
    
    parser.add_argument('scansettings', type=argparse.FileType('r'),
                        help="TOML formatted file with scanner settings")  
    parser.add_argument('powersettings', type=argparse.FileType('r'),
                        help="TOML formatted file with power settings")  

    parser.add_argument("--powercmd", type=str, default = "np05b.py",
                        help = "Program to control power manager")
    parser.add_argument("--scancmd", type = str, default = "scanit.py",
                        help = "Program to run scanner")


    parser.add_argument('--delay', type=int, default = 5,
                        help="Delay (in mins) before first scan")  
    parser.add_argument("--interval", type=int, default = 30,
                        help="Interval (in mins) between scans")
    parser.add_argument('--nscans', type=int, default = 1,
                        help = "Number of scans to collect")


    args = parser.parse_args()




if __name__ == "__main__":
    main()