from __future__ import print_function
import time, datetime
import textwrap

import serial
from serial.tools import list_ports

import pick
import yaml
import click




def list_power_devices(type='serial'):
    if type == "serial":
        return list_serial_devices()
    else:
        return []

def list_serial_devices():
    return [port.device for port in list_ports.comports()]


class PowerManager:
    def __init__(self, portname):
        self.portname = portname

    def all_on(self):
        pass

    def all_off(self):
        pass

    def power_on(self, outlet):
        pass

    def power_off(self, outlet):
        pass


class NP05B(PowerManager):
    def __init__(self, portname):
        PowerManager.__init__(self, portname)
        self.serial = serial.Serial()
        self.serial.port = portname
        self.serial.baudrate = 9600
        self.serial.timeout = 3
        self.serial.bytesize = serial.EIGHTBITS
        self.serial.parity = serial.PARITY_NONE
        self.serial.stopbits = serial.STOPBITS_ONE
        self.serial.xonxoff = 0

    def open(self):
        self.serial.open()

    def close(self):
        self.serial.close()

    def reset_buffers(self):
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    def all_on(self):
        self.open()
        self.reset_buffers()
        self.serial.write(b"\nps 1\n")
        self.close()

    def all_off(self):
        self.open()
        self.reset_buffers()
        self.serial.write(b"\nps 0\n")
        self.close()     

    def power_on(self, outlet):
        outlet = int(outlet)
        if outlet < 1 or outlet > 5:
            return None
        self.open()
        self.reset_buffers()
        self.serial.write(b"\npset {} 1\n".format(outlet))
        self.close()

    def power_off(self, outlet):
        outlet = int(outlet)
        if outlet < 1 or outlet > 5:
            return None
        self.open()
        self.reset_buffers()
        self.serial.write(b"\npset {} 0\n".format(outlet))
        self.close()        


POWER_DICT= {"Generic": PowerManager, 
            "Synaccess NP-05B": NP05B}

def create_powermanager(name, port):
    return POWER_DICT[name](port)


def choose_power_model():
    title = """Pick the model of power manager device.\n"""\
            """Up/Down arrow keys to select, Enter to accept."""
    choice, index = pick.pick(POWER_DICT.keys(), title)
    return choice   


def choose_power_interface(type="serial"):
    """Query for available interfaces for power mangers
    """
    devices = list_power_devices(type)
    if not len(devices):
        return None

    # pick power manager interface
    title = """Pick the port/name of the interface for the power manager device.\n"""\
            """Up/Down arrow keys to select, Enter to accept."""
    choice, index = pick.pick(devices, title)
    return choice

def choose_power_outlet():
    outlets = [1, 2, 3, 4, 5]
    # pick outlet on power manager
    title = """Pick the outlet of the power manager device.\n"""\
            """Up/Down arrow keys to select, Enter to accept."""
    choice, index = pick.pick(outlets, title)
    return outlets[index]    

def choose_poweron_delay():
    delays = [60, 120]
    # pick outlet on power manager
    title = """Pick the delay time (secs) after power-on before scanning starts.\n"""\
            """Up/Down arrow keys to select, Enter to accept."""
    choice, index = pick.pick(delays, title)
    return delays[index]    

def choose_poweroff_delay():
    delays = [60, 120]
    # pick outlet on power manager
    title = """Pick the delay time (secs) after scanning before power-off.\n"""\
            """Up/Down arrow keys to select, Enter to accept."""
    choice, index = pick.pick(delays, title)
    return delays[index]    



@click.command()
@click.argument("outfile",
                type=click.File('w'),
                default='-')
def setpower(outfile):
    """Write power manager settings to a config file (stdout).
    """
    model = choose_power_model()
    port = choose_power_interface()
    outlet = choose_power_outlet()
    on_delay = choose_poweron_delay()
    off_delay = choose_poweroff_delay()

    rdict = {"power":
             {"model": model,
              "port": port,
              "outlet": outlet,
              "on_delay": on_delay,
              "off_delay": off_delay}}
    yaml.safe_dump(rdict, outfile,
                   default_flow_style = False,
                   encoding = "utf-8")


if __name__ == "__main__":
    setpower()





