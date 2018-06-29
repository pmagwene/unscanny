from __future__ import print_function

import yaml
import click
import threading
import time
import sys

def wait_nsecs(n):
    try:
        s = ""
        for i in range(n):
            time.sleep(1)
            print(' '*len(s), end="\r")
            s = "Time remaining: {}".format(n-i)
            print(s, end="\r")
            sys.stdout.flush()
        print("")
    except KeyboardInterrupt:
        print("Interrupting")
        sys.stdout.flush()
        raise KeyboardInterrupt

def scan():
    print("Scanning...")
    




@click.command()
@click.option("-u", "--user",
              help = "Last name of investigator",
              type = str,
              prompt = "User's last name")
@click.option("-e", "--experiment",
              help = "Name of experiment",
              type = str,
              prompt = "Experiment name")
@click.option("-i", "--interval",
              help = "Interval between scans (mins)",
              type = click.IntRange(1, 2880),
              prompt = "Interval (mins)",
              default = 30)
@click.option("-n", "--nscans",
              help = "Total number of scans",
              type=click.IntRange(0, 9999),
              prompt = "# of scans",
              default=1)
@click.argument("outfile",
                type=click.File("w"),
                default="-")
@click.option("-m", "--mode",
              help = 'Scan mode',
              type = click.Choice(["Gray","Color"]),
              prompt = "Scan mode",
              default = "Gray")
@click.option("-s", "--source",
              help = 'Scan source',
              type = click.Choice(["TPU8x10", "Flatbed"]),
              prompt = "Scan source",
              default = "TPU8x10")
@click.option("-r", "--resolution",
              help = "Scanner resolution (dpi)",
              type = int,
              prompt = "Scanner resolution (dpi)",
              default = 300)
@click.option("-d", "--depth",
              help = "Bit depth per pixel",
              type=click.Choice(["8", "16"]),
              prompt = "Scanner bit depth",
              default="16")
@click.argument("outfile",
                type=click.File('w'),
                default='-')
def runit(**kwargs):
    #threads = []
    #threads.append(threading.Thread(target = wait_nsecs, args=(10,)))
    #threads.append(threading.Thread(target = scan))
    #threads.append(threading.Thread(target = wait_nsecs, args=(10,)))
    #threads.append(threading.Thread(target = scan))
    #for thread in threads:
    #    thread.start()
    q = []
    q.append((wait_nsecs, (10,)))
    q.append((scan, ()))
    q.append((wait_nsecs, (10,)))
    q.append((scan, ()))
    for task, args in q:    
        try:
            task(*args)
        except KeyboardInterrupt:
            print("Exiting due to interrupt")
            sys.exit(1)




    # print("Hi!")
    # t = threading.Thread(target = wait_nsecs, args = (10,))
    # try:
    #     t.start()
    # except KeyboardInterrupt:


@click.group()
def cli():
    pass


cli.add_command(runit)

if __name__ == "__main__":
    cli()
