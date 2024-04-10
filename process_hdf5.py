import h5py
import numpy as np
from scipy.signal import hilbert
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget,QVBoxLayout

class process_data():
    def __init__(self,path):
        self.path=path
        # self.name_of_dataset=name_of_dataset
        self.dataset=None
        self.alldata=None
        self.hdf5_file=h5py.File(self.path,'r')
        self.group=self.hdf5_file['Table1']

    def get_data(self,name_of_dataset,print_all_names=True):
        if print_all_names:
            dataset_names= list(self.group.keys())
            print(f"All datasets in 'Table1': {dataset_names}")
        if name_of_dataset in self.group:
            self.dataset = self.group[name_of_dataset]
            print(f"Dataset '{name_of_dataset}' opened successfully.")
        else:
            print(f"Dataset '{name_of_dataset}' does not exist.")

        if self.dataset is not None:
            data=np.array(self.dataset)
            return data
        else:
            print('"Dataset is not available."')

    def get_group_keys(self):
        list = []
        for i in self.group.keys():
            list.append(i)
        return list

    def get_attribute(self,name_of_attr):
        if self.dataset is not None:
            attribute=self.dataset.attrs.get(name_of_attr)
            return attribute
        else:
            print('"Dataset is not available. Call open_dataset first."')
    def get_all_attributes(self):
        if self.dataset is not None:
            attributes=self.dataset.attrs.keys()
            return attributes
        else:
            print('Dataset is not available.Call open_dataset first')

    def get_fs(self):
        if self.dataset is not None:
            sampling_period=self.dataset.attrs.get('ChannelInformationSamplingPeriod')

            return 1/sampling_period
        else:
            print('"Dataset is not available. Call open_dataset first."')

    def get_RPM(self):
        #if self.dataset is not None:
        tacho="Ds02-TACHO"
        time="Ds01-Time"
        dataset = self.group[tacho]
        time=self.group[time]
        yvalues=np.array(dataset)
        xvalues=np.array(time)
        # Identify indices where y values meet criteria
        period_indices = []
        reference_point = yvalues[1]
        print(f'This is refference value {reference_point}')
        for i in range(len(yvalues) - 1):
            current = yvalues[i]
            prev = yvalues[i - 1]
            refdiff = abs(reference_point - current)
            rozdiel = abs(prev - current)
            if refdiff > 0.4:
                if rozdiel > 0.15:
                    period_indices.append(i)
            if len(period_indices) >= 3:
                break
        # Retrieve corresponding x values
        period_x_values = xvalues[period_indices]
        perioda = period_x_values[2] - period_x_values[0]

        return 1/perioda

        # else:
        #     print('"Dataset in get_fault_freq is not available. Call open_dataset first."')
    
    def get_multispectrum(self,name_of_dataset,upper_limit=None,lower_limit=None,freq_resolution=10):
        signal = self.group[name_of_dataset]
        fs=self.get_fs()
        fig, (ax2) = plt.subplots(nrows=1)
        # ax1.plot(time, x)
        #calculate number of point for FFT - according that is set frequency resolution
        NFFT = int(fs[0])/int(freq_resolution)

        Pxx, freqs, bins, im = ax2.specgram(signal, NFFT=int(NFFT), Fs=fs, noverlap=int(NFFT/2), cmap='rainbow')

        plt.ylim(lower_limit, upper_limit)

        plt.show()
        
    def get_fault_freq(self,D11,D12,z1,z2,n1,beta1=0):
        #NU 215 ECML
        BETA = beta1  # Angle of
        n = n1  # Number of rolling elements original 18
        D1 = D11
        D2 = D12
        # n = 16  # Number of rolling elements
        # D1 = 112
        # D2 = 88.5
        # n = 24  # Number of rolling elements
        # D1 = 245
        # D2 = 270

        z1=z1 # pocet zubov
        z2=z2 # pocet zubov
        RD = (D1 - D2) / 2
        PD = (D1 + D2) / 2
        x = RD / PD
        fi = self.get_RPM()
        print(fi)
        f0 = 0
        fGear=fi*z1 #zubova frekvencia
        print(fGear)

        fBPFO = n / 2 * (fi - f0) * (1 - x)
        BPFO = (n / 2) * fi * (1 - (RD / PD) * np.cos(BETA))

        fBPFI = fi * n / 2 * (1 + x)
        BPFI = fi * (n / 2) * (1 + (RD / PD) * np.cos(BETA))

        fc = 0.5 * fi * (1 - x)
        FTF = fi * 0.5 * (1 - x)

        BSF = 0.5 * fi * (PD / RD) * (1 - ((RD / PD) * np.cos(BETA)) ** 2)

        fBSF = 0.5 * fi * ((1 - (x * x)) / x)

        # # QJ 215 N2MA
        # n = n2  # Number of rolling elements original 16
        # D1 = D21
        # D2 = D22
        # BETA=beta2
        # fBPFO = n / 2 * (fi - f0) * (1 - x)
        # BPFO2 = (n / 2) * fi * (1 - (RD / PD) * np.cos(BETA))
        #
        # fBPFI = fi * n / 2 * (1 + x)
        # BPFI2 = fi * (n / 2) * (1 + (RD / PD) * np.cos(BETA))
        #
        # fc = 0.5 * fi * (1 - x)
        # FTF2 = fi * 0.5 * (1 - x)
        #
        # BSF2 = 0.5 * fi * (PD / RD) * (1 - ((RD / PD) * np.cos(BETA)) ** 2)
        #
        # fBSF = 0.5 * fi * ((1 - (x * x)) / x)
        # n = n3  # Number of rolling elements
        # D1 = D31
        # D2 = D32
        # BETA = beta3-180
        # i=z2/z1
        # n=n/i
        # RD = (D1 - D2) / 2
        # PD = (D1 + D2) / 2
        # x = RD / PD
        #
        # fBPFO = n / 2 * (fi - f0) * (1 - x)
        # BPFO3 = (n / 2) * fi * (1 - (RD / PD) * np.cos(BETA))
        #
        # fBPFI = fi * n / 2 * (1 + x)
        # BPFI3 = fi * (n / 2) * (1 + (RD / PD) * np.cos(BETA))
        #
        # fc = 0.5 * fi * (1 - x)
        # FTF3 = fi * 0.5 * (1 - x)
        #
        # BSF3 = 0.5 * fi * (PD / RD) * (1 - ((RD / PD) * np.cos(BETA)) ** 2)
        #
        # fBSF = 0.5 * fi * ((1 - (x * x)) / x)
        #
        # # BPFO2=BPFO*2
        # # BPFI2 = BPFI * 2
        # # FTF2=FTF*2
        # # BSF2=BSF*2
        # values=[('BPFO',BPFO),('BPFI',BPFI),('FTF',FTF),('BSF',BSF),('fGear',fGear),
        #         ('BPFO2',BPFO2),('BPFI2',BPFI2),('FTF2',FTF2),('BSF2',BSF2),
        #         ('BPFO3',BPFO3),('BPFI3',BPFI3),('FTF3',FTF3),('BSF3',BSF3)]
        values = [('BPFO', BPFO), ('BPFI', BPFI), ('FTF', FTF), ('BSF', BSF), ('fGear', fGear)]
        freqencies=dict(values)
        return freqencies

    def get_hilbert_signal(self,name_of_dataset):
        signal = self.group[name_of_dataset]
        hilbert_signal=hilbert(signal)
        envelope= np.abs(hilbert_signal)

        return envelope

    # ref je refenrencny tlak nastaveny na 20 mikropascalov
    def get_dbfft(self,input_vec,fs,ref=0.000020):
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
        window = np.hamming(len(input_vec))
        input_vec = input_vec * window
        spec = np.fft.rfft(input_vec)
        spec_mag = (np.abs(spec) * np.sqrt(2)) / np.sum(window)
        spec_db = 20 * np.log10(spec_mag / ref)
        # Generate frequency vector
        freq_vec = np.arange((len(input_vec) / 2) + 1) / (float(len(input_vec)) / fs)

        return freq_vec, spec_mag

    def create_app(self):
        # Create a QWidget to hold the main layout
        print("PLOTING")
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        main_widget.show()
        main_widget.showMaximized()
        print("Plotted")


