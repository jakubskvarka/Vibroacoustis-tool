import sys
import threading
import numpy as np
import  requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg
from HelpFunctions.lanxi import LanXI
from HelpFunctions.Stream import streamHandler
from HelpFunctions.Buffer import DataBuffer
import HelpFunctions.utility as utility

class FigHandler(QMainWindow):
    #musi tu byt parameter lanxi a streamer, vytvoreni noveho OBJEKTU z CLASS sa tam
    #zadaju hodnoty potrebne na funkciu, tym je lanxi a streamer z HelpFuntions
    def __init__(self, lanxi, streamer):
        super().__init__()

        self.lanxi = lanxi
        self.streamer = streamer
        self.ChunkToShow = 2**12
        self.fftSize = self.ChunkToShow
        self.old = 0
        self.oldold = 0

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)


        self.plot1 = pg.PlotWidget(title="Time Domain")
        self.plot1.setBackground('white')
        self.plot1.setLabel('left', 'Amplitude')
        self.plot1.setLabel('bottom', 'Time [s]')
        self.curve1 = self.plot1.plot()
        self.layout.addWidget(self.plot1)

        self.plot2 = pg.PlotWidget(title="Frequency Domain")
        self.plot1.setBackground('white')
        self.plot2.setLabel('left', 'Amplitude [dB SPL]')
        self.plot2.setLabel('bottom', 'Frequency [Hz]')
        self.curve2 = self.plot2.plot()
        self.layout.addWidget(self.plot2)

        self.startAnimation()


    def _update(self):
        axis = np.arange(self.ChunkToShow)
        axis = np.flip(axis * -1 / self.lanxi.sample_rate)
        self.curve1.setData(x=axis, y=DataBuffer.getPart(self.ChunkToShow))

        freq, s_dbfs = utility.dbfft(DataBuffer.getPart(self.fftSize), self.lanxi.sample_rate, np.hamming(self.fftSize), ref=20 * 10**(-6))
        self.curve2.setData(x=freq, y=s_dbfs / 3 + self.old / 3 + self.oldold / 3)
        self.oldold = self.old
        self.old = s_dbfs
        #na zistenie sample rate, teray je 131072 a je to asi zbytozne vela,
        # nastavit to manualne, nech si uzivatel vyberie
        print(self.lanxi.sample_rate)

    def startAnimation(self):
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(100)  # Set the update interval in milliseconds

    def closeEvent(self, event):
        print('Closed Figure!')
        self.streamer.stopStream()
        event.accept()

class StreamThread(threading.Thread):
    def __init__(self, lanxi):
        super(StreamThread, self).__init__()
        self.lanxi = lanxi
        self.ip= lanxi.ip
        self.host = "http://" + self.ip

    def run(self):
        streamer = streamHandler(self.lanxi)
        streamer.startStream()

    def stopStream(self):
        requests.put(self.host + "/rest/rec/measurements/stop")
        requests.put(self.host + "/rest/rec/finish")
        requests.put(self.host + "/rest/rec/close")



#
# if __name__ == "__main__":
#     try:
#         lanxi = LanXI("169.254.170.20")
#         lanxi.setup_stream()
#
#         streamer = StreamThread(lanxi)
#         streamer.start()
#
#         app = QApplication(sys.argv)
#         fig = FigHandler(lanxi, streamer)
#         fig.show()
#         sys.exit(app.exec())
#     except:
#         streamer.stopStream()