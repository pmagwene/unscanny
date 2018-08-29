from dataclasses import dataclass, fields
import io

import sarge
import tifffile as TIFF

@dataclass
class ScannerSettings(object):
    format: str = "tiff"
    mode: str = "Gray"
    resolution: int = 300

    def options_str(self) -> str:
        options = []
        for field in fields(self):
            namestr = field.name.replace("_", "-")
            optionstr = sarge.shell_format("--{} {}", namestr, self.__dict__[field.name])
            options.append(optionstr)
        return " ".join(options)


@dataclass
class TestScanner(ScannerSettings):
    test_picture: str = "Color pattern"
    depth: int = 8

@dataclass
class EpsonV800(ScannerSettings):
    source: str = "TPU8x10"
    depth: int = 16
    
@dataclass
class Pixma04A91731(ScannerSettings):
    source: str = "Flatbed"

def settings2options(settingsdict):
    options = [sarge.shell_format("--{} {}", key, val) for (key,val) in settingsdict.items()]
    return " ".join(options)


def get_scanners():
    scanners = str(sarge.get_stdout("scanimage -f '%d%n'")).splitlines()
    return scanners

def scanimage_command(scanner, settings) -> str:
    return "scanimage -d {} {} ".format(scanner, settings2options(settings))


def scanimage(device, settings):
    command = scanimage_command(device, settings)
    c = sarge.capture_stdout(command)
    return TIFF.imread(io.BytesIO(c.stdout.read()))



