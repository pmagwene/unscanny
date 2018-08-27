from dataclasses import dataclass, fields

import sarge
#import tifffile as TIFF


@dataclass
class ScannerSettings(object):
    format: str = "tiff"
    mode: str = "Gray"
    resolution: int = 300
    depth: int = 16

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


@dataclass
class EpsonV800(ScannerSettings):
    source: str = "TPU8x10"


def scanimage_str(devicestr, settings) -> str:
    return "scanimage -d {} {} ".format(devicestr, settings.options_str())


def scanimage(devicestr, settings):
    callstr = scanimage_str(devicestr, settings)
    c = sarge.capture_stdout(callstr)

def get_scanners():
    devices = str(sarge.get_stdout("scanimage -f '%d%n'")).splitlines()
    return devices


s = ScannerSettings()
print(scanimage_str("test", TestScanner()))
