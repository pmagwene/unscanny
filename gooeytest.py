import argparse
import sys, time
from gooey import Gooey


import sane


def get_scanners():
    sane.init()
    devices = sane.get_devices(True)
    names = [dev[0] for dev in devices] + ["test"]
    return names


@Gooey
def main():

    scanners = get_scanners()
    
    parser = argparse.ArgumentParser(description="BSA mapping from high-throughput sequencing")

    parser.add_argument('-L','--low', nargs='*', required=True, 
            help="one or more files giving allele freqs in low bulk")
    parser.add_argument('-H','--high',nargs='*', required=True,
            help="one or more files giving allele freqs in high bulk")
    parser.add_argument('-k','--kernel', type=str, default="tricube", 
            choices=['uniform','tricube','triweight','quartic','savgol'], 
            help='smoothing kernel (default=tricube)')   
    parser.add_argument('--scanner', type=str, choices = scanners,
            help="scanner to use")          
    parser.add_argument('-w','--width', type=int, default=100, 
            help='smoothing kernel half-width in # of points (default=100)')     

    args = parser.parse_args()

    print "next scan in two minutes..."
    time.sleep(10)
    print "next scan in three minutes..."



if __name__ == "__main__":
    main()