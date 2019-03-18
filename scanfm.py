import asyncio
import helpers
import numpy as np
import scipy
from rtlsdr import RtlSdr
from displaytask import DisplayTask


class ScanFm(DisplayTask):
    FM_BEGIN_FREQ = 87.5e6
    FM_END_FREQ = 108e6
    
    defaults = {
            'samp_rate' : 2e6,
            'center_freq': FM_BEGIN_FREQ + 1e6,
            'gain' : 40.2,
            'samp_size' : 2**18
            }

    def __init__(self, samp_rate, center_freq, gain, samp_size):
        super().__init__(samp_rate, center_freq, gain, samp_size)

    def find_and_remove_station(samp_rate, samp_len, samp_fft):
        # Array containing the frequencies represented by the FFT
        x = np.linspace(-samp_rate / 2, samp_rate / 2, samp_len)
        
        # Translate function for conversion between frequencies and FFT indices
        translate = scipy.interpolate.interp1d([-samp_rate / 2, samp_rate / 2],[0, len(samp_fft)])
        
        # Get index of current max value from FFT
        max_index = np.where(samp_fft == max(samp_fft))[0][0]
        # Calculate(approximate) upper and lower band of station
        # Having the bandwidth of the signal in Hertz we
        # calculate the indices of the FFT corresponding
        # to those frequencies

        if -100e3 + x[max_index] < samp_rate / 2:
            lower_band = 0
        else:
            lower_band = int(translate(-100e3 + x[max_index]))

        if 100e3 + x[max_index] > samp_rate / 2:
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
        

        while max(samp_fft) > min(samp_fft) + 15:
            new_station = ScanFm.find_and_remove_station(self.samp_rate, len(samples), samp_fft)
            stations.append(new_station)
            
        return np.array(stations)
    
    async def run(self, time = 0):
        time_pass = 0
        
        while self._sdr.center_freq < ScanFm.FM_END_FREQ:
            samples = self._sdr.read_samples(self.samp_size)
            ret = self.execute(samples)
            print(np.around((ret + self._sdr.center_freq) / 1e6, decimals = 1))
            self._sdr.center_freq += self.samp_rate

            if time:
                time_pass += samp_size

            if time_pass / self.samp_rate >= time and time:
                break

