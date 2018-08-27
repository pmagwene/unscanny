import time, datetime
import uuid
from string import Formatter

import dataclasses
from dataclasses import dataclass

import sane


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


def strfdelta(tdelta, fmt):
    """ string representation of timedelta object.

    Code from: https://stackoverflow.com/a/17847006
    """
    f = Formatter()
    d = {}
    l = {"D": 86400, "H": 3600, "M": 60, "S": 1}
    k = [x[1] for x in list(f.parse(fmt))]
    rem = int(tdelta.total_seconds())

    for i in ('D', 'H', 'M', 'S'):
        if i in k and i in l.keys():
            d[i], rem = divmod(rem, l[i])
    
    return f.format(fmt, **d)


def HHMMSS(tdelta):
    return strfdelta(tdelta, "{H:02}:{M:02}:{S:02}")



@dataclass
class Settings:
    def __str__(self):
        s = ""
        for (key,val) in dataclasses.asdict(self).items():
            s += "{} = {}\n".format(key, val)
        return s    

@dataclass
class RunSettings(Settings):
    user: str
    experiment: str
    interval: int
    nscans: int
    delay: int

@dataclass
class ScannerSettings(Settings):
    mode: str
    source: str
    resolution: int
    depth: int

@dataclass
class PowerSettings(Settings):
    module: int
    address: str
    username: str
    password: str
    outlet: int

class RunData(object):
    """ A class to represent information associated with a run.
    """
    def __init__(self, run_settings, scanner_settings, power_settings):
        self.run_settings = run_settings
        self.scanner_settings = scanner_settings
        self.power_settings = power_settings
        self._log = []
        self.t_start = None
        self.t_lastscan = None
        self.t_end = None
        self.nscans_completed = 0
        self.successful = False
        self.basedir = "."
        self.UID = self._generate_id()

    def log(self, entry):
        self._log.append(entry)

    def _generate_id(self):
        UUID = str(uuid.uuid4())
        return UUID.split('-')[0]

    def base_fname(self):
        """ Base filename for run.
        """
        return "{}-{}-{}-{}".format(
            self.t_start.strftime("%Y-%m-%d"),
            self.run_settings.user, self.run_settings.experiment, self.UID)

    def current_fname(self, timept = None):
        """ Appropriate filename for current stage of run.
        """
        if timept is None:
            timept = datetime.datetime.now()
        timestr = timept.strftime("%Y%m%dT%H%M%S")
        return "{}-{:04d}-{}".format(self.base_fname(),
                                     self.nscans_completed,
                                     timestr)

    def settings_str(self):
        run, scan, power = self.run_settings, self.scanner_settings, self.power_settings
        s = "SETTINGS:\n\n"
        s += "Run settings\n"
        s += "============\n"
        s += str(run) + "\n"
        s += "Scanner settings\n"
        s += "================\n"
        s += str(scan) + "\n"
        s += "Power settings\n"
        s += "==============\n"
        s += str(power)
        return s        

    def generate_report(self):
        title = "RUN REPORT\n"
        idstr = "UID: {}".format(self.UID)
        setstr = self.settings_str()

        startstr = "Start time:"
        if self.t_start is not None:
            startstr = "Start time: {}".format(self.t_start.isoformat())
        endstr = "End time:"
        if self.t_lastscan is not None:
            endstr = "End time: {}".format(self.t_lastscan.isoformat()) 
        totalstr = "Completed scans: {}".format(self.nscans_completed)
        succstr = "Run successful: {}".format(str(self.successful))
        logstr = "Log:\n\t{}".format("\n\t".join(self._log))
        parts = [title, idstr, setstr, startstr, endstr,
                 totalstr, succstr, logstr]
        reportstr = "\n\n".join(parts)
        return reportstr