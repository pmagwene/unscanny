from __future__ import print_function
import collections

import yaml

class Settings(collections.MutableMapping):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return str(self.__dict__)

    def __iter__(self):
        return self.__dict__.__iter__()

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]

        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]



def load_config(fname, section):
    """YAML file name, section string -> Settings object.
    """
    with open(fname, "r") as f:
        config = yaml.safe_load(f)
        return Settings(**config[section])


def formatted_settings_str(settings, headerstr):
    s = "{}\n".format(headerstr)
    s += "{}\n".format("-" * len(headerstr))
    for (key, val) in settings.iteritems():
        s += "{}: {}\n".format(key, str(val))
    return s
