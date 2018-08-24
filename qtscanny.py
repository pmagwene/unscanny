

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
from string import Formatter

from PyQt5.QtWidgets import * #(QWidget, QLabel, QLineEdit, QTextEdit, QGridLayout, QApplication, QComboBox, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox)
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import schedule






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
    print("I'm working...")

class CountdownDialog(QProgressDialog):
    def __init__(self):
        super().__init__("Waiting...", "Abort", 0, 0)
        self.setWindowModality(Qt.WindowModal)

    def startX(self, delay):
        t_now = datetime.datetime.now()
        t_end = t_now + datetime.timedelta(seconds = delay)
        self.setRange(0, delay)
        for i in range(delay):
            if self.wasCanceled():
                return 0
            else:
                timestr = "Time remaining: {}".format(HHMMSS(time_until(t_end)))
                self.setLabelText(timestr)
                time.sleep(1)
                self.setValue(i)

    def start(self, delay, nscans):
        self.setRange(0, delay)

        scheduler = MaxScheduler(nscans)
        scheduler.every(delay).seconds.do(job)
        
        while scheduler.nruns < scheduler.maxruns:
            if self.wasCanceled():
                return 0
            scheduler.run_pending()
            tdelta = scheduler.next_run - datetime.datetime.now()
            timestr = u"   Job {} of {}. Time until next job: {}   ".format(scheduler.nruns + 1, scheduler.maxruns,
                                                                     HHMMSS(tdelta))
            self.setLabelText(timestr)
            self.setValue(delay - scheduler.idle_seconds)
            self.adjustSize()
            time.sleep(1)




class ComboBox(QComboBox):
    def __init__(self, items, editable = False):
        super().__init__()
        self.addItems(items)
        self.setEditable(editable)


class Example(QWidget):
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def run_delay(self):
        d = CountdownDialog()
        d.show()
        d.start(int(self.combo_interval.currentText()), int(self.edit_nscans.text()))
        
        
    def init_ui(self):
        
        self.edit_name = QLineEdit()
        self.edit_expt = QLineEdit()

        self.combo_interval = ComboBox(["10", "15", "30", "60", "90", "120", "240", "480"], editable = True)
        self.combo_interval.setValidator(QIntValidator())

        self.edit_nscans = QLineEdit("1")
        self.edit_nscans.setValidator(QIntValidator())   

        self.combo_delay = ComboBox(["0","5","10","15","30"], editable = True)
        self.combo_delay.setValidator(QIntValidator())

        form1 = QFormLayout()
        form1.addRow(QLabel('Investigator Last Name:'), self.edit_name)
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

        btn_start = QPushButton("Start")
        btn_start.clicked.connect(self.run_delay)



        layout = QGridLayout()
        layout.addWidget(group1, 0, 0)
        layout.addWidget(group2, 0, 1)
        layout.addWidget(group3, 1, 0)
        layout.addWidget(btn_start, 1, 1)
        layout.setAlignment(btn_start, Qt.AlignCenter)

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
    ex = Example()
    sys.exit(app.exec_())
