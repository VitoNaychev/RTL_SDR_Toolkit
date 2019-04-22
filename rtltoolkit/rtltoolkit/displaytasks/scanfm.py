import asyncio
import os
import numpy as np
import scipy

from rtlsdr import RtlSdr

from rtltoolkit.basetasks.displaytask import DisplayTask
from rtltoolkit.helpers import ffthelpers

# 1. Refactor code
# 2. Add the power of the detected signal
#    next to its frequency

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

    def find_and_remove_station(self, fft_arr):
        # Array containing the frequencies represented by the FFT
        # It is used to convert between FFT indexes and frequencies
        freq_translate = np.linspace(-self.samp_rate / 2, self.samp_rate / 2, self.samp_size)

        # Translate function for conversion between frequencies and FFT indixes
        index_translate = scipy.interpolate.interp1d([-self.samp_rate / 2, self.samp_rate / 2],\
                [0, self.samp_size])

        # Get index of current max value from FFT
        station_index = np.where(fft_arr == max(fft_arr))[0][0]
        station_power = fft_arr[station_index]

        # Calculate(approximate) upper and lower band of station
        # Having the bandwidth of the signal in Hertz we
        # calculate the indices of the FFT corresponding
        # to those frequencies

        # Check if left limit of the FM signal is inside
        # the array containing the FFT
        if -100e3 + freq_translate[station_index] < self.samp_rate / 2:
            # If not set it to the lowest index in the array
            lower_band = 0
        else:
            # Else translate the left limit frequency in the
            # corresponding array index of the FFT
            lower_band = int(index_translate(-100e3 + freq_translate[station_index]))

        # Check if right limit of the FM signal is inside
        # the array containing the FFT
        if 100e3 + freq_translate[station_index] > self.samp_rate / 2:
            # If not set it to the max index in the array
            upper_band = len(fft_arr)
        else:
            # Else translate the right limit frequency in the
            # corresponding array index of the FFT
            upper_band = int(index_translate(100e3 + freq_translate[station_index]))

        # Practicaly remove station by giving it the lowest value
        # from the FFT so that it won't be detected in the next
        # iteration of the loop
        fft_arr[lower_band:upper_band] = min(fft_arr)

        # Return the found station
        return (freq_translate[station_index], station_power)

    def execute(self, samples):
        # Array of stations to listen to
        stations = []

        # Calculate the FFT at current frequency
        fft_arr = ffthelpers.calc_fft(samples, self.samp_rate, len(samples), True)


        while max(fft_arr) > min(fft_arr) + 20:
            # Get frequency and power of the station
            freq, power = self.find_and_remove_station(fft_arr)
            freq = round((freq + self._sdr.center_freq) / 1e6, 1)
            power = int(round(power))

            # Pack the values in a dictionary representing the
            # station and append them to the list
            station = {
                'freq' : freq,
                'power' : power
            }
            stations.append(station)

        return stations

    async def run(self, time = 0):
        time_pass = 0

        while True:
            stations = []

            # Set the SDR's center frequency so that it
            # encompasses the begining of the FM band
            self._sdr.center_freq = ScanFm.FM_BEGIN_FREQ + self.samp_rate / 2

            # Cycle through the whole band until you reach the end
            # of the FM band
            while self._sdr.center_freq < ScanFm.FM_END_FREQ:
                # Read samples from SDR
                samples = self._sdr.read_samples(self.samp_size)

                # Append the returned stations from 'execute'
                # to the rest
                stations += self.execute(samples)

                # Increment center frequency so that in covers
                # the adjacent frequency band
                self._sdr.center_freq += self.samp_rate

                # Timer for the elapsed time since the start
                if time:
                    time_pass += samp_size

                if time_pass / self.samp_rate >= time and time:
                    break

            os.system('clear')

            # Print the new station info on the terminal
            print('Frequency\t\tPower')
            print('---------\t\t-----')

            for station in stations:
                station_str = str(station['freq']) + ' MHz\t\t' + str(station['power']) + ' dBm'
                print(station_str)

