import sys
import requests


class np05(object):
    def __init__(self, address, username = "admin", password = "admin"):
        self.address = address
        self.username = username
        self.password = password
        self.url = "http://{}/cmd.cgi?".format(address)

    def _run_command(self, cmd, args=[]):
        argstr = " ".join([str(i) for i in args])
        fullurl = "{}{} {}".format(self.url, cmd, argstr)
        try:
            r = requests.post(fullurl, auth=(self.username, self.password), timeout=10)
        except requests.exceptions.ConnectTimeout:
            print("ERROR: Unable to connect to NP05b power manager.")
            sys.exit(1)
        return r

    def all_on(self):
        cmd = "$A7"
        args = [1]
        return self._run_command(cmd, args).status_code != 200

    def all_off(self):       
        cmd = "$A7"
        args = [0]
        return self._run_command(cmd, args).status_code != 200

    def power_on(self, outlet):
        cmd = "$A3"
        args = [outlet, 1]
        return self._run_command(cmd, args).status_code != 200

    def power_off(self, outlet):
        cmd = "$A3"
        args = [outlet, 0]
        return self._run_command(cmd, args).status_code != 200

    def is_on(self, outlet):
        return self.status()[outlet - 1] == 1

    def status(self):
        cmd = "$A5"
        status_str = self._run_command(cmd).content
        return [i for i in reversed([int(c) for c in status_str])]
