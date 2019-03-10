import asyncio
import helpers
import numpy as np
import scipy
from rtlsdr import RtlSdr
from displaytask import DisplayTask

FM_BEGIN_FREQ = 87.5e6
FM_END_FREQ = 108e6

class ScanFm(DisplayTask):
    def __init__(self, samp_rate):
        super().__init__(samp_rate)

    def find_and_remove_station(self, samp_fft, x, translate):
        # Get index of current max value from FFT
        max_index = np.where(samp_fft == max(samp_fft))[0][0]
        # Calculate(approximate) upper and lower band of station
        #   Having the bandwidth of the signal in Hertz we
        #   calculate the indices of the FFT corresponding
        #   to those frequencies

        if -100e3 + x[max_index] < self.samp_rate / 2:
            lower_band = 0
        else:
            lower_band = int(translate(-100e3 + x[max_index]))

        if 100e3 + x[max_index] > self.samp_rate / 2:
            upper_band = len(samp_fft)
        else:
            upper_band = int(translate(100e3 + x[max_index]))
        # Practicaly remove station by giving it the lowest value
        # from the FFT so that it won't be detected in the next
        # iteration of the FFT
        samp_fft[lower_band:upper_band] = min(samp_fft)
 
        # Return the station corresponding to the max value
        return x[max_index]

    def execute(self, samples):
        # Array of stations to listen to
        stations = []
        # Calculate the FFT at current frequency
        samp_fft = helpers.calc_fft(samples, self.samp_rate, len(samples), True)
        
        # Array containing the frequencies represented by the FFT
        x = np.linspace(-self.samp_rate / 2, self.samp_rate / 2, len(samples))
        
        # Translate function for conversion between frequencies and FFT indices
        translate = scipy.interpolate.interp1d([-self.samp_rate / 2, self.samp_rate / 2],[0, len(samp_fft)])

        while max(samp_fft) > min(samp_fft) + 15:
            new_station = self.find_and_remove_station(samp_fft, x, translate)
            stations.append(new_station)
            
        return np.array(stations)
    
    async def run(self, sdr, time = 0, samp_size = RtlSdr.DEFAULT_READ_SIZE):
        time_pass = 0
        sdr.center_freq = FM_BEGIN_FREQ + self.samp_rate / 2
        
        while sdr.center_freq < FM_END_FREQ:
            samples = sdr.read_samples(samp_size)
            ret = self.execute(samples)
            print(np.around((ret + sdr.center_freq) / 1e6, decimals = 1))
            sdr.center_freq += self.samp_rate

            if time:
                time_pass += samp_size

            if time_pass / self.samp_rate >= time and time:
                break

