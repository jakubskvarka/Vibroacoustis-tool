from PyQt6.QtWidgets import QMainWindow,QApplication, QPushButton,QComboBox,QLabel,QCheckBox,QFileDialog,QLineEdit,QVBoxLayout, QWidget, QSplitter
from PyQt6 import uic
import sys

import interpretation_to_HDF
import offline
import recorder
from process_hdf5 import process_data
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import matplotlib.animation as animation
import numpy as np
import pyqtgraph as pg
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from offline import Analyser
from  RealTimePyQt import FigHandler, StreamThread
from  RealTimeSpectrogram import Spectrogram,StreamThreadS
from HelpFunctions.lanxi import LanXI
import requests


class UI(QMainWindow):
    def __init__(self):
        super(UI,self).__init__()
        #Load USER INTERFACE .ui
        self.graphwindow = None
        self.dataset=None
        uic.loadUi('UserInt.ui',self)
        #Define QWidgets
        #BUTTONS

        self.button=self.findChild(QPushButton,"pushButton")
        self.button2 = self.findChild(QPushButton, "pushButton_2")
        self.button3 = self.findChild(QPushButton, "pushButton_3")
        self.button4 = self.findChild(QPushButton, "pushButton_4")
        self.button5 = self.findChild(QPushButton, "pushButton_5")
        self.button6 = self.findChild(QPushButton, "pushButton_6")
        self.button7 = self.findChild(QPushButton, "pushButton_7")
        self.button8 = self.findChild(QPushButton, "pushButton_8")
        #LABELS
        self.label=self.findChild(QLabel,'label')
        self.label2 = self.findChild(QLabel, 'label2')
        self.label3= self.findChild(QLabel,'label3')
        #COMOBOBOX
        self.combobox=self.findChild(QComboBox,'comboBox')
        self.combobox2 = self.findChild(QComboBox, 'comboBox_2')
        self.combobox3 = self.findChild(QComboBox, 'comboBox_3')
        self.combobox4 = self.findChild(QComboBox, 'comboBox_4')

        # LINE EDIT
        self.line = self.findChild(QLineEdit, "lineEdit")
        self.line2 = self.findChild(QLineEdit, "lineEdit_2")
        self.line3 = self.findChild(QLineEdit, "lineEdit_3")
        self.line4 = self.findChild(QLineEdit, "lineEdit_4")
        self.line5 = self.findChild(QLineEdit, "lineEdit_5")
        self.line6 = self.findChild(QLineEdit, "lineEdit_6")
        self.line7 = self.findChild(QLineEdit, "lineEdit_7")
        self.line8 = self.findChild(QLineEdit, "lineEdit_8")
        self.line9 = self.findChild(QLineEdit, "lineEdit_9")
        self.line10 = self.findChild(QLineEdit, "lineEdit_10")


        self.checkbox=self.findChild(QCheckBox, 'checkBox')
        self.checkbox2 = self.findChild(QCheckBox, 'checkBox_2')
        self.checkbox3 = self.findChild(QCheckBox, 'checkBox_3')
        self.checkbox4 = self.findChild(QCheckBox, 'checkBox_4')

        self.button.clicked.connect(self.select_file_and_combobox) #
        self.button2.clicked.connect(self.apply_channel)#
        self.button3.clicked.connect(self.start_analyser) # plot
        self.button4.clicked.connect(self.dostanem_list_s_funkciami_ciar)
        self.button5.clicked.connect(self.liveFFT)
        self.button6.clicked.connect(self.startRecorder)
        self.button7.clicked.connect(self.stopStream)
        self.button8.clicked.connect(self.remove_freq)




    def select_file_and_combobox(self):
        # open file dialog
        self.filename, _ = QFileDialog.getOpenFileName(self, 'Open File', '', "HDF5 (*.h5)")
        print(self.filename)
        self.path = self.filename
        self.combobox.clear()
        # output
        if self.filename:
            self.label.setText(f"Selected file path: {str(self.filename)}")
            self.dataset = process_data(self.path)
            self.list_of_data = self.dataset.get_group_keys()
            self.combobox.addItems(self.list_of_data)
        return self.path

    def apply_channel(self):
        self.currentText = self.combobox.currentText()
        self.label2.setText(f"Selected channel:{self.currentText}")

        return self.currentText

    def dostanem_dict_s_freq(self):

        self.list_of_values = []
        self.d1=int(self.line.text())
        self.d2=int(self.line2.text())
        self.z1 = int(self.line3.text())
        self.z2 = int(self.line4.text())
        self.beta=int(self.line5.text())
        self.n = int(self.line6.text())
        #self.list_of_values.extend([self.d1,self.d2,self.z1,self.z2,self.beta,self.n] )
        #print(self.list_of_values)
        self.freq=self.dataset.get_fault_freq(self.d1,self.d2,self.z1,self.z2,self.n,self.beta)
        dict1 = self.graphwindow.filter_freq()
        self.freq.update(dict1)
        print(self.freq)

        return self.freq


    def dostanem_list_s_funkciami_ciar(self):
        self.graphwindow.handle_lines(self.dostanem_dict_s_freq())


    def start_analyser(self):
        self.graphwindow=Analyser(self.path,self.currentText,cmap=self.combobox4.currentText(),
                                  resolution=float(self.combobox3.currentText()),Time=self.checkbox.isChecked(),
                                  FFT=self.checkbox2.isChecked(),Spectrogram=self.checkbox3.isChecked(),logScale=self.checkbox4.isChecked())
        self.graphwindow.show()

    def remove_freq(self):
        self.graphwindow.clear_lines()
        print("Cleared")

    def liveFFT(self):
        self.IP=self.line7.text()
        lanxi = LanXI(self.IP)
        lanxi.setup_stream()
        streamer = StreamThread(lanxi)
        streamer.start()

        self.live = FigHandler(lanxi, streamer)
        self.live.show()

    def startRecorder(self):
        name_of_file=self.line8.text()
        record_time = int(self.line9.text())
        sampling_freq = self.combobox2.currentText()
        ip_adress = self.line7.text()
        recorder.Recorder(name_of_file=name_of_file,record_time=record_time,sampling_freq=sampling_freq,ip_adress=ip_adress)
        interpretation_to_HDF.Parser(name_of_file=f"{name_of_file}{sampling_freq}.stream")

    def stopStream(self):
        self.script_config=recorder.Recorder.get_config()
        baseURL=f"http://{'[' + self.script_config['addr'] + ']'}" if addr_family == socket.AF_INET6 else f"http://{self.script_config['addr']}"
        requests.put(baseURL+ '/measurements/stop')

app=QApplication(sys.argv)
window=UI()
window.show()
app.exec()