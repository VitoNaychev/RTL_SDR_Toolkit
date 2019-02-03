import helpers
import numpy as np
import scipy
from displaytask import DisplayTask

class ScanFm(DisplayTask):
    def __init__(self, samp_rate):
        super().__init__(samp_rate)

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
            # Get index of current max value from FFT
            max_index = np.where(samp_fft == max(samp_fft))[0][0]
            # Append the station corresponding to the max value
            stations.append(x[max_index])
            # Calculate(approximate) upper and lower band of station
            #   Having the bandwidth of the signal in Hertz we
            #   calculate the indices of the FFT corresponding
            #   to those frequencies
            lower_band = int(translate(-100e3 + x[max_index]))

            if 100e3 + x[max_index] > self.samp_rate / 2:
                upper_band = len(samp_fft)
            else:
                upper_band = int(translate(100e3 + x[max_index]))
            # Practicaly remove station by giving it the lowest value
            # from the FFT so that it won't be detected in the next
            # iteration of the FFT
            samp_fft[lower_band:upper_band] = min(samp_fft)
            
        return np.array(stations)
        
            
