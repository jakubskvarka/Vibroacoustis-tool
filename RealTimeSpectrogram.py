####Import Lib###
from matplotlib.mlab import window_hanning,specgram
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LogNorm
import numpy as np
import threading
import requests
###import modules###
from HelpFunctions.lanxi import LanXI
from HelpFunctions.Stream import streamHandler
from HelpFunctions import Buffer
import HelpFunctions.utility as utility

###Constants###
SAMPLES_PER_FRAME=20
CHUNK_SIZE= 2**12 # number of samples to take per read


###Initialize conncetion with LanXI###

class StreamThreadS(threading.Thread):
    def __init__(self,lanxi):
        super(StreamThreadS, self).__init__()
        self.lanxi=lanxi
        self.ip=lanxi.ip
        self.host="http://"+self.ip
        self.fftSize=CHUNK_SIZE
    def run(self):
        streamer=streamHandler(self.lanxi)
        streamer.startStream()

    def stopStream(self):
        requests.put(self.host+"/rest/rec/measurements/stop")
        requests.put(self.host + "/rest/rec/finish")
        requests.put(self.host + "/rest/rec/close")

    def get_signal(self):
        data=Buffer.DataBuffer.getPart(self.fftSize)
        return data

class Spectrogram(threading.Thread):
    def __init__(self,lanxi):
        super(Spectrogram, self).__init__()
        self.lanxi = lanxi
        self.ip = lanxi.ip
        self.host = "http://" + self.ip
        self.fftSize = CHUNK_SIZE


    def get_spectrogram(self,signal,rate):
        arr2D,freqs,bins = specgram(signal,window=window_hanning,
                                    Fs=rate,NFFT=1024,noverlap=int(1024*0.7))
        return arr2D,freqs,bins
    def update_fig(self,n,im):
        data=StreamThreadS.get_signal(self)
        arr2D,freqs,bins= self.get_spectrogram(data,self.lanxi.GetFs())
        im_data= im.get_array()
        if n < SAMPLES_PER_FRAME:
            im_data= np.hstack((im_data,arr2D))
            im.set_array(im_data,)
        else:
            keep_block= arr2D.shape[1]*(SAMPLES_PER_FRAME-1)
            im_data= np.delete(im_data,np.s_[:-keep_block],1)
            im_data=np.hstack((im_data,arr2D))
            im.set_array(im_data,)
        return [im]

def main():
    fig= plt.figure()

    lanxi= LanXI("169.254.170.20")
    lanxi.setup_stream()
    streamer=StreamThreadS(lanxi)
    streamer.start()

    spec=Spectrogram(lanxi)

    data= streamer.get_signal()
    arr2D, freqs, bins = spec.get_spectrogram(data,lanxi.sample_rate)

    extent = (bins[0], bins[-1] * SAMPLES_PER_FRAME, freqs[-1], freqs[0])
    im = plt.imshow(arr2D, aspect='auto', extent=extent, interpolation="none",
                    cmap='rainbow', norm=LogNorm(vmin=.01, vmax=1))
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Real-Time Spectrogram')
    plt.gca().invert_yaxis()
    plt.colorbar()

############### Animate ###############
    anim = animation.FuncAnimation(fig, spec.update_fig, fargs=(im,), blit=False,
                                   interval=CHUNK_SIZE/1000, frames=1000)

    try:
        plt.show()
    except:
        print("Plot Closed")
    # Ensure that the StreamThread is stopped when the plot is closed
    finally:
        streamer.stopStream()

if __name__ == "__main__":
    main()








