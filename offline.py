import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QSplitter,QMainWindow,QLabel
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from process_hdf5 import process_data
import pandas as pd
from scipy import signal

# Create LinearRegionItem for selecting region

class Analyser(QWidget):
    def __init__(self,path,channel,resolution,cmap,logScale=False,Time=False,FFT=False,Spectrogram=False):
        super().__init__()
        self.setWindowTitle(channel)
        self.layout=QVBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumSize(100,100)

        self.accuracy=2
        self.logScale=logScale
        self.cmap=cmap
        self.resolution=resolution
        self.path=path
        self.channel=channel
        self.load_data()
        self.frekvencie=[]
        # self.freq_vec,self.spec_mag=self.dbfft(self.x, self.fs)
        #plot time doamin
        self.plot_time=pg.PlotWidget()
        label_style = {'color': 'black', 'font-size': '12pt', "weight": "bold"}
        self.plot_time.setLabel('left', f'Amplitude[{self.unit_}] ', **label_style)
        self.plot_time.setLabel('bottom', 'Time', **label_style,units= 's')
        # Set font for Time domain
        self.plot_time.getAxis('left').setTextPen('black')
        self.plot_time.getAxis('bottom').setTextPen('black')
        self.plot_time.setTitle('Time Domain', color='black', size="14pt")
        # Set limits for x axis in Time domain
        self.plot_time.setLimits(xMin=self.t[0] - 1, xMax=self.t[-1] + 1)
        #self.plot_time.plot(self.t, self.x, pen='b')
        self.plot_time.setBackground((255,255,255))

        #plot FFT
        self.plot_fft = pg.PlotWidget()
        self.plot_fft.setLabel('left', f'Amplitude[{self.unit_}] ', **label_style)
        self.plot_fft.setLabel('bottom', 'Frequency', **label_style, units= 'Hz')
        # Set font for Time domain
        self.plot_fft.getAxis('left').setTextPen('black')
        self.plot_fft.getAxis('bottom').setTextPen('black')
        self.plot_fft.setTitle('Frequency Domain', color='black', size="14pt")
        # Set limits for x axis in Time domain
        self.plot_fft.setLimits(xMin=0, xMax=self.fs[0]/8) # limit na cca 4000
        #self.plot_fft.plot(self.freq_vec, self.spec_mag, pen='b')
        self.plot_fft.setBackground((255, 255, 255))



        #plot spectrogram
        self.plot_spec=pg.GraphicsLayoutWidget()
        self.plot_spec.setBackground("white")

        self.spectrogram=self.plot_spec.addPlot()

        # Limit panning/zooming to the spectrogram

        # Add labels to the axis
        self.spectrogram.setLabel('bottom', "Time", **label_style, units='s')
        # If you include the units, Pyqtgraph automatically scales the axis and adjusts the SI prefix (in this case kHz)
        self.spectrogram.setLabel('left', "Frequency", **label_style, units='Hz')


        # self.plot_spec.setLabel('left', f'Frequency [Hz] ', **label_style)
        # self.plot_spec.setLabel('bottom', 'Time[s]', **label_style)
        # self.plot_spec.getAxis('left').setTextPen('black')
        # self.plot_spec.getAxis('bottom').setTextPen('black')
        # self.plot_spec.setTitle('Spectrogram', color='black', size="14pt")


        #add grid
        self.plot_time.showGrid(x=True, y=True, alpha=90)
        self.plot_fft.showGrid(x=True, y=True, alpha=90)
        if self.logScale:
            self.plot_fft.setLogMode(y=True)
        else:
            pass

        # Create LinearRegionItem for selecting region
        self.region = pg.LinearRegionItem(pen='red')
        self.plot_time.addItem(self.region)
        # Set the initial region to cover the full range of the time axis
        self.region.setRegion([self.t[0], self.t[-1]])
        # Set the boundaries for region selection
        self.region.setBounds([self.t[0], self.t[-1]])

        self.updateRegion(self.region.getRegion(),self.t)
        self.region.sigRegionChanged.connect(self.handle_region)

        self.plot_time.plot(self.t, self.x, pen='b')

        self.splitter_time_fft_spec = QSplitter(pg.QtCore.Qt.Orientation.Vertical)
        if Time:
            self.splitter_time_fft_spec.addWidget(self.plot_time)
        if FFT:
            self.splitter_time_fft_spec.addWidget(self.plot_fft)
        if Spectrogram:
            self.splitter_time_fft_spec.addWidget(self.plot_spec)
            self.plot_spectrogram_pyqt()
        else:
            pass

        # Create a QSplitter for all three windows
        self.splitter_all = QSplitter(pg.QtCore.Qt.Orientation.Vertical)
        self.splitter_all.addWidget(self.splitter_time_fft_spec)  # Add the first two windows splitter

        # Create a widget for the third window where the Matplotlib plot is displayed
        # self.mpl_widget = QWidget()
        # self.mpl_layout = QVBoxLayout()
        # self.mpl_layout.setContentsMargins(0, 0, 0, -1)
        # self.mpl_canvas=FigureCanvas(Figure())
        # self.mpl_layout.addWidget(self.mpl_canvas)

        # Adding navigation toolbar
        #self.toolbar = NavigationToolbar(self.mpl_canvas, self.mpl_widget)

        #self.mpl_layout.addWidget(self.toolbar)

        # Get the Matplotlib axes for plotting
        #self.ax = self.mpl_canvas.figure.add_axes([0.05, 0.15, 1.05, 0.72])
        # self.ax = self.mpl_canvas.figure.add_axes([0.12, 0.25, 0.88, 0.62])
        # self.ax.set_xlabel('Time [s]')
        # self.ax.set_ylabel('Frequency [Hz]')
        # self.ax.set_title('Spectrogram')

        # Plot the spectrogram
        #self.plot_spectrogram(self.ax)

        #self.mpl_widget.setLayout(self.mpl_layout)

        # Add Matplotlib plot widget to the third window
        #self.splitter_all.addWidget(self.mpl_widget)

        self.layout.addWidget(self.splitter_all)
        #self.layout.addWidget(self.splitter_time_fft)
        #self.layout.addWidget(self.mpl_widget)
        #self.plot_spectrogram_pyqt()

    def load_data(self):
        # Load data from HDF5 file
        self.dataset = process_data(self.path)
        self.t = self.dataset.get_data("Ds01-Time")
        self.x = self.dataset.get_data(self.channel)  #######Priestor na automatizaciu
        self.fs = self.dataset.get_fs()
        self.unit_ = self.dataset.get_attribute("InterpretationUnit")
        #self.unit_ = self.dataset.get_attribute("InterpretationUnit")[0].replace("1", " ")

    def dbfft(self,input_vec, fs, ref=0.000020):
        """
        Calculate spectrum on dB scale relative to specified reference.
        Args:
            input_vec: vector containing input signal
            fs: sampling frequency
            ref: reference value used for dB calculation
        Returns:
            freq_vec: frequency vector
            spec_db: spectrum in dB scale
        """
        # Calculate windowed/scaled FFT and convert to dB relative to full-scale
        #window = np.hamming(len(input_vec))
        #input_vec = input_vec
        spec = np.fft.rfft(input_vec)
        #self.spec_mag = (np.abs(spec) * np.sqrt(2)) / np.sum(window)
        self.spec_mag = (np.abs(spec) /len(input_vec)*2)
        spec_db20_SPL = 20 * np.log10(self.spec_mag / ref)
        spec_db10 = 10 * np.log10(self.spec_mag)
        # Generate frequency vector
        self.freq_vec = np.fft.rfftfreq(len(input_vec), d=1 / fs)
        print("Computed")
        return self.freq_vec, self.spec_mag
# stary skript s matplotlib
    # # Function to calculate and plot the spectrogram
    # def plot_spectrogram(self,ax):
    #     freq_resolution = 1  #######Priestor na automatizaciu
    #     NFFT = int(self.fs[0]) // freq_resolution  # Adjust NFFT as needed
    #     Pxx, freqs, bins, im = ax.specgram(self.x, NFFT=NFFT, Fs=self.fs, noverlap=NFFT // 2, cmap='rainbow', mode='magnitude',
    #                                        scale='dB')
    #     plt.colorbar(mappable=im, label="Amplitude [dB]",pad=0.01)
    #     print(f"spectrogram done from file{self.path,self.channel} ")
    #     return im, Pxx, freqs, bins

    def plot_spectrogram_pyqt(self):
        #Počet vzoriek pre FFT - kontroluje sa tým frekvenčné rozlíšenie
        nfft=self.fs[0]/self.resolution
        #Výpočet STFT pre spektrogram
        f,t,Sxx = signal.spectrogram(x=self.x,fs=self.fs,window=np.hanning(nfft),nfft=nfft,noverlap=nfft/2,mode="magnitude")
        # Interpretácia obrazových údajov ako riadkových namiesto stĺpcových
        pg.setConfigOptions(imageAxisOrder='row-major')
        # Vloženie obrazu do grafického okna
        img = pg.ImageItem()
        self.spectrogram.addItem(img)
        # Pridanie histogramu kvoli farebnej mape
        hist = pg.HistogramLUTItem()
        # Spojenie histogramu s obrazom
        hist.setImageItem(img)
        #cmap = "viridis"
        hist.gradient.loadPreset(self.cmap)

        # Nastavenie pisma
        label_style = {'color': 'black', 'font-size': '12pt', "weight": "bold"}
        self.spectrogram.getAxis("bottom").setTextPen((0, 0, 0))
        self.spectrogram.getAxis("left").setTextPen((0, 0, 0))
        self.spectrogram.setTitle("Spectrogram", color='black', size="14pt")


        #self.plot_spec.addItem(hist)
        # Viridis colormap set as default
        #hist.gradient.restoreState({'mode': 'rgb',
        #'ticks': [(0.0, (68, 1, 84, 255)), (0.25, (58, 82, 139, 255)), (0.5, (32, 144, 140, 255)), (0.75, (94, 201, 97, 255)), (1.0, (253, 231, 36, 255))]})
        # Sxx contains the amplitude for each pixel
        if 'MIC' in self.channel:
            ref=0.00002 # referenčná hladina 20 μPa
            splScale = 20 * np.log10(Sxx / ref)
            # Filter the values to keep only where Sxx is greater than 0
            splScale_filtered = np.where(splScale > 0, splScale, 0)
            #max_value = np.max(splScale_filtered)
            img.setImage(splScale)
            #hist.region.setMovable(False)
            barSPL = pg.ColorBarItem(values=[np.min(splScale), np.max(splScale)],
                                         colorMap=self.cmap,interactive=False)
            barSPL.getAxis("right").setTextPen((0, 0, 0))
            barSPL.setLabel('left', 'SPL[dB]', **label_style)

            self.plot_spec.addItem(barSPL)
            print("SPL")
        else:
            minSxx=np.min(Sxx)
            #logScale=10*np.log10(Sxx/minSxx)
            logScale = 10 * np.log10(Sxx)
            barLOG=pg.ColorBarItem(values=[np.min(logScale), np.max(logScale)],
                                         colorMap=self.cmap,interactive=False)
            barLOG.setLabel('left', "Intensity [dB]", **label_style)
            barLOG.getAxis("right").setTextPen((0, 0, 0))
            img.setImage(logScale)
            self.plot_spec.addItem(barLOG)
            print("log10")
        # Scale the X and Y Axis to time and frequency (standard is pixels)
        img.setRect(0, 0, t[-1], f[-1])  # Set the rectangle to match the time and frequency dimensions
        self.spectrogram.setLimits(xMin=0, xMax=t[-1], yMin=0, yMax=f[-1])

    def updateRegion(self,region_values, t):
        start_idx = np.argmax(t >= region_values[0])
        end_idx = np.argmax(t >= region_values[1])
        selected_data = self.x[start_idx:end_idx]
        # Now you can perform FFT on the selected data
        self.freq_vec_now, self.spec_mag_now = self.dbfft(selected_data, fs=self.fs)
        # Plot the FFT result
        self.plot_fft.plot( self.freq_vec_now, self.spec_mag_now, clear=True, pen="black")

        print(self.frekvencie)
        #time.sleep(2)
        if self.frekvencie != []:
            for i in self.frekvencie:
                self.plot_fft.addItem(i)


    def handle_region(self,region_object):
        self.updateRegion(region_object.getRegion(),self.t)


    def handle_lines(self,funkcie_ciar):
        self.dictionary = funkcie_ciar
        for n, i in enumerate(self.dictionary): # i predstavuje key a n je pocet iteracii
            self.frekvencia = pg.InfiniteLine(pos=self.dictionary[str(i)], angle=90,pen=pg.mkPen('pink', width=1.5),label=str(i) )
            self.frekvencia.label.setColor('red')
            self.frekvencia.label.setAngle(90)
            self.plot_fft.addItem(self.frekvencia)
            self.frekvencie.append(self.frekvencia)

    def filter_freq(self):
        # Printing indexes of values higher than
        max_val = np.max(self.spec_mag_now)
        percentage = 0.01

        dataframe = pd.read_excel("eigenxls.xlsx")

        housing = dataframe.iloc[:, [1]].dropna().astype(int).squeeze().tolist()
        out = dataframe.iloc[:, [3]].dropna().astype(int).squeeze().tolist()
        pinion = dataframe.iloc[:, [5]].dropna().astype(int).squeeze().tolist()

        max_percentage = percentage * max_val
        indexes = np.where(self.spec_mag_now > max_percentage)[0]
        indexes = indexes.tolist()
        freq_higher_than = self.freq_vec_now[indexes]
        print(f"Indexes of values higher than {max_percentage} :", indexes)
        print(freq_higher_than)

        similar_freq = {}
        for i, item1 in enumerate(housing):
            for item2 in freq_higher_than:
                if 1 <= abs(item1 - item2) <= self.accuracy: # nastavenie cistlivosti v akom rozmedzi bude brat frekvencie okolo
                    dict1 = {f'H_eigen_{i+1}': int(item2)}
                    similar_freq.update(dict1)

        for i, item1 in enumerate(out):
            for item2 in freq_higher_than:
                if 1 <= abs(item1 - item2) <= self.accuracy:
                    dict1 = {f'O_eigen_{i+1}': int(item2)}
                    similar_freq.update(dict1)

        for i, item1 in enumerate(pinion):
            for item2 in freq_higher_than:
                if 1 <= abs(item1 - item2) <= self.accuracy:
                    dict1 = {f'P_eigen_{i+1}': int(item2)}
                    similar_freq.update(dict1)

        return similar_freq

    def clear_lines(self):
        self.plot_fft.clear()
        self.plot_fft.plot(self.freq_vec_now, self.spec_mag_now, clear=True, pen="blue")





















