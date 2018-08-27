

"""
Last name of investigator (text box)
Experiment name (text box)
Interval between scans (integer)
Num of scans (integer)
Outfile (text)

Scan mode (gray/color)
Source (TPU8x10, flatbed)
DPI resolution (integer: 150, 300, 600)
Bit depth (integer: 8, 16)


scanning cycle
    power on
    run scan
    power off



"""



import sys
import time, datetime
import threading
import sched

from string import Formatter
from dataclasses import dataclass

from PyQt5.QtWidgets import * #(QWidget, QLabel, QLineEdit, QTextEdit, QGridLayout, QApplication, QComboBox, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox)
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import schedule


@dataclass
class RunSettings:
    user: str
    expt: str
    interval: int
    nscans: int
    delay: int

@dataclass
class ScannerSettings:
    mode: str
    source: str
    dpi: int
    depth: int

@dataclass
class PowerSettings:
    manager: int
    address: str
    username: str
    password: str
    outlet: int





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

def time_until(t_end, t_now = None):
    if t_now is None:
        t_now = datetime.datetime.now()
    return t_end - t_now




class RunData(object):
    """ A class to represent information associated with a run.
    """
    def __init__(self, run_settings, scanner_settings, power_settings):
        self.run_settings = run_settings
        self.scanner_settings = scanner_settings
        self.power_settings = power_settings
        self._log = []
        self.t_start = None
        self.t_end = None
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
            self.user, self.experiment, self.UID)

    def current_fname(self, timept = None):
        """ Appropriate filename for current stage of run.
        """
        if timept is None:
            timept = datetime.datetime.now()
        timestr = timept.strftime("%Y%m%dT%H%M%S")
        return "{}-{:04d}-{}".format(self.base_fname(),
                                     self.ct_nextscan,
                                     timestr)

    def generate_report(self):
        idstr = "UID: {}".format(self.UID)
        scanset = settings.formatted_settings_str(self.scanner_settings,
                                                  "Scanner Settings")
        runset = settings.formatted_settings_str(self.run_settings,
                                                 "Run Settings")
        startstr = "Start time:"
        if self.t_start is not None:
            startstr = "Start time: {}".format(self.t_start.isoformat())
        endstr = "End time:"
        if self.t_lastscan is not None:
            endstr = "End time: {}".format(self.t_lastscan.isoformat()) 
        totalstr = "Completed scans: {}".format(self.ct_nextscan)
        succstr = "Run successful: {}".format(str(self.successful))
        logstr = "Log:\n\t{}".format("\n\t".join(self._log))
        parts = [idstr, scanset, runset, startstr, endstr,
                 totalstr, succstr, logstr]
        reportstr = "\n\n".join(parts)
        return reportstr


class MaxScheduler(schedule.Scheduler):
    def __init__(self, maxruns = 0):
        super().__init__()
        self.maxruns = maxruns
        self.nruns = 0

    def _run_job(self, job):
        if self.nruns < self.maxruns:
            self.nruns += 1
            super()._run_job(job)
        else:
            self.clear()



def job():
    print("Powering on...")
    time.sleep(10)
    print("Scanning")
    time.sleep(10)
    # oldmin, oldmax = dlg.minimum(), dlg.maximum()
    # dlg.setRange(0, 2)
    # dlg.setLabelText("Powering on...")
    # qApp.processEvents()
    # time.sleep(10)
    # dlg.setValue(1)
    # dlg.setLabelText("Scanning...")
    # time.sleep(10)
    # dlg.setValue(2)
    # dlg.setRange(oldmin, oldmax)



class CountdownDialog(QProgressDialog):
    def __init__(self):
        super().__init__("Waiting...", "Abort", 0, 0)
        self.setWindowModality(Qt.WindowModal)


    def start(self, delay, nscans):
        self.setRange(0, delay)
        scheduler = sched.scheduler(time.time, time.sleep)

        for i in range(nscans):
            if self.wasCanceled():
                return 0
            e = scheduler.enter(delay, 1, job)
            t = threading.Thread(target=scheduler.run)
            t.start()
            while not(scheduler.empty()):
                tnext = scheduler.queue[0][0]
                if tnext <= time.time():
                    continue
                self.setLabelText("  Time until next job: {}  ".format(tnext - time.time()))
                self.setValue(delay - tnext)
                time.sleep(0.5)
        print("DONE")


        # scheduler = MaxScheduler(nscans)
        # scheduler.every(delay).seconds.do(job, self)
        
        # while scheduler.nruns < scheduler.maxruns:
        #     if self.wasCanceled():
        #         return 0
        #     tdelta = scheduler.next_run - datetime.datetime.now()
        #     timestr = u"   Job {} of {}. Time until next job: {}   ".format(scheduler.nruns + 1, scheduler.maxruns,
        #                                                              HHMMSS(tdelta))
        #     self.setLabelText(timestr)
        #     self.setValue(delay - scheduler.idle_seconds)
        #     self.adjustSize()
        #     scheduler.run_pending()
        #     time.sleep(1)

        # return 1



class ComboBox(QComboBox):
    def __init__(self, items, editable = False):
        super().__init__()
        self.addItems(items)
        self.setEditable(editable)


class QtUnscanny(QWidget):
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def run_delay(self):
        self.record_settings()
        self.btn_start.setEnabled(False)
        d = CountdownDialog()
        d.show()
        d.start(int(self.combo_interval.currentText()), int(self.edit_nscans.text()))
        self.btn_start.setEnabled(False)

    def check_required(self):
        if len(self.edit_user.text()) > 0 and len(self.edit_expt.text()) > 0:
            if len(self.edit_nscans.text()) > 0 and int(self.edit_nscans.text()) > 0:
                self.btn_start.setEnabled(True)



    def record_settings(self):
        self.run_settings = RunSettings(user = self.edit_user.text(),
                                        expt = self.edit_expt.text(),
                                        interval = int(self.combo_interval.currentText()),
                                        nscans = int(self.edit_nscans.text()),
                                        delay = int(self.combo_delay.currentText()))
        self.scanner_settings = ScannerSettings(mode = self.combo_mode.currentText(),
                                                source = self.combo_src.currentText(),
                                                dpi = self.combo_resolution.currentText(),
                                                depth = self.combo_depth.currentText())
        self.power_settings = PowerSettings(manager = self.edit_pwrmodule.text(),
                                            address = self.edit_pwraddress.text(),
                                            username = self.edit_pwrusername.text(),
                                            password = self.edit_pwrpassword.text(),
                                            outlet = self.combo_pwroutlet.currentText())

        
        
    def init_ui(self):
        
        self.edit_user = QLineEdit()
        self.edit_user.editingFinished.connect(self.check_required)
        alpha_regex = QRegExp("[a-z-A-Z_]+")
        self.edit_user.setValidator(QRegExpValidator(alpha_regex, self.edit_user))

        self.edit_expt = QLineEdit()
        self.edit_expt.editingFinished.connect(self.check_required)
        word_regex = QRegExp(r"\w+")
        self.edit_expt.setValidator(QRegExpValidator(word_regex, self.edit_expt))
        

        self.combo_interval = ComboBox(["10", "15", "30", "60", "90", "120", "240", "480"], editable = True)
        self.combo_interval.setValidator(QIntValidator())

        self.edit_nscans = QLineEdit("1")
        self.edit_nscans.setValidator(QIntValidator())   
        self.edit_nscans.editingFinished.connect(self.check_required)

        self.combo_delay = ComboBox(["0","5","10","15","30"], editable = True)
        self.combo_delay.setValidator(QIntValidator())

        form1 = QFormLayout()
        form1.addRow(QLabel('Investigator Last Name:'), self.edit_user)
        form1.addRow(QLabel('Experiment Name:'), self.edit_expt)
        form1.addRow(QLabel('Interval Between Scans (mins):'), self.combo_interval)
        form1.addRow(QLabel('Number of Scans:'), self.edit_nscans)
        form1.addRow(QLabel("Delay before first scan (mins):"), self.combo_delay)

        group1 = QGroupBox("Run settings")
        group1.setLayout(form1)
        
        self.combo_mode = ComboBox(["gray", "color"])

        self.combo_src = ComboBox(["TPU8x10","flatbed"])
        self.combo_src.setCurrentIndex(0)

        self.combo_resolution = ComboBox(["75", "150", "300", "600"], editable = True)
        self.combo_resolution.setValidator(QIntValidator())
        self.combo_resolution.setCurrentIndex(2)

        self.combo_depth = ComboBox(["8", "16"], editable = True)
        self.combo_depth.setValidator(QIntValidator())
        self.combo_depth.setCurrentIndex(1)

        form2 = QFormLayout()
        form2.addRow(QLabel("Scan mode:"), self.combo_mode)
        form2.addRow(QLabel("Scan source:"), self.combo_src)
        form2.addRow(QLabel("Resolution (dpi):"), self.combo_resolution)
        form2.addRow(QLabel("Bit depth:"), self.combo_depth)

        group2 = QGroupBox("Scanner settings")
        group2.setLayout(form2)


        self.edit_pwrmodule = QLineEdit("np05b")
        self.edit_pwraddress = QLineEdit("192.168.1.100")
        self.edit_pwrusername = QLineEdit("admin")
        self.edit_pwrpassword = QLineEdit("admin")
        self.combo_pwroutlet = ComboBox([str(i) for i in range(1,6)], editable = True)
        self.combo_pwroutlet.setValidator(QIntValidator())


        form3 = QFormLayout()
        form3.addRow(QLabel("Power manager:"), self.edit_pwrmodule)
        form3.addRow(QLabel("Power, IP address:"), self.edit_pwraddress)
        form3.addRow(QLabel("Power, username:"), self.edit_pwrusername)
        form3.addRow(QLabel("Power, password:"), self.edit_pwrpassword)
        form3.addRow(QLabel("Power, outlet #:"), self.combo_pwroutlet)
        
        group3 = QGroupBox("Power manager settings")
        group3.setLayout(form3)

        self.text_log = QPlainTextEdit()

        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.run_delay)
        self.btn_start.setEnabled(False)

        vbox = QVBoxLayout()
        vbox.addWidget(self.text_log)
        vbox.addWidget(self.btn_start)
        vbox.setAlignment(self.btn_start, Qt.AlignCenter)
        group4 = QGroupBox("Logging")
        group4.setLayout(vbox)




        layout = QGridLayout()
        layout.addWidget(group1, 0, 0)
        layout.addWidget(group2, 0, 1)
        layout.addWidget(group3, 1, 0)
        layout.addWidget(group4, 1, 1)

        #vbox = QVBoxLayout()
        #vbox.addLayout(hbox1)
        #vbox.addLayout(hbox2)
        #vbox.addWidget(btn_start)
        #vbox.setAlignment(btn_start, Qt.AlignHCenter)

        self.setLayout(layout) 
        
        self.setGeometry(300, 300, 640, 480)
        self.setWindowTitle('Unscanny')    
        self.show()
        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = QtUnscanny()
    sys.exit(app.exec_())
