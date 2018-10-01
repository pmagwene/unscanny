
class nullpower(object):
    def __init__(self, address, username = "admin", password = "admin"):
        self.address = address
        self.username = username
        self.password = password

    def all_on(self):
        return 0

    def all_off(self):       
        return 0

    def power_on(self, outlet):
        return 0

    def power_off(self, outlet):
        return 0

    def is_on(self, outlet):
        return True

    def wake_up(self):
        return 0
