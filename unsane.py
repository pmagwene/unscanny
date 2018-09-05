import io

import sarge
import tifffile as TIFF



test_settings = {"format":"tiff",
                 "test-picture":"Color pattern",
                 "resolution":300,
                 "depth":16}

def get_scanners():
    scanners = str(sarge.get_stdout("scanimage -f '%d%n'")).splitlines()
    return scanners


def settings2options(settingsdict):
    options = [sarge.shell_format("--{} {}", key, val) for (key,val) in settingsdict.items()]
    return " ".join(options)


def build_commandline(scanner, settings) -> str:
    return "scanimage -d {} {} ".format(scanner, settings2options(settings))

def scan(device, settings):
    command = build_commandline(device, settings)
    c = sarge.capture_stdout(command)
    return TIFF.imread(io.BytesIO(c.stdout.read()))



