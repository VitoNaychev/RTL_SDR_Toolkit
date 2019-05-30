import os
import sys
import numpy as np
import scipy

from rtltoolkit.basetasks.displaytask import DisplayTask
from rtltoolkit.helpers import ffthelpers


class ScanFm(DisplayTask):
    FM_BEGIN_FREQ = 87.5e6
    FM_END_FREQ = 108e6

    defaults = {
            'samp_rate': 2e6,
            'center_freq': FM_BEGIN_FREQ + 1e6,
            'gain': 40.2,
            'samp_size': 2**18
            }

    def __init__(self, samp_rate, center_freq, gain, samp_size):
        super().__init__(samp_rate, center_freq, gain, samp_size)

    def find_and_remove_station(self, fft_arr):
        # Array containing the frequencies represented by the FFT
        # It is used to convert between FFT indexes and frequencies
        freq_translate = np.linspace(-self.samp_rate / 2,
                                     self.samp_rate / 2,
                                     self.samp_size)

        # Translate function for conversion between frequencies and FFT indixes
        index_translate = scipy.interpolate.interp1d([-self.samp_rate / 2,
                                                      self.samp_rate / 2],
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
            lower_band = int(index_translate(-100e3 +
                                             freq_translate[station_index]))

        # Check if right limit of the FM signal is inside
        # the array containing the FFT
        if 100e3 + freq_translate[station_index] > self.samp_rate / 2:
            # If not set it to the max index in the array
            upper_band = len(fft_arr)
        else:
            # Else translate the right limit frequency in the
            # corresponding array index of the FFT
            upper_band = int(index_translate(100e3 +
                                             freq_translate[station_index]))

        # Practicaly remove station by giving it the lowest value
        # from the FFT so that it won't be detected in the next
        # iteration of the loop
        fft_arr[lower_band:upper_band] = min(fft_arr)

        # Return the found station
        return (freq_translate[station_index], station_power)

    def update_station_dict(self, stations, new_stations):
        # Compare the new found stations and the old ones
        # and remove those that are missing from the old ones
        old_stations = []
        for station in stations:
            if -self.samp_rate/2 + self.center_freq < station * 1e6\
               and station * 1e6 < self.samp_rate/2 + self.center_freq\
               and station not in new_stations:
                old_stations.append(station)

        for station in old_stations:
            del stations[station]

        return stations

    def execute(self, samples):
        # Array of stations to listen to
        stations = dict()

        # Calculate the FFT at current frequency
        fft_arr = ffthelpers.calc_fft(samples, self.samp_rate,
                                      len(samples), True)

        while max(fft_arr) > min(fft_arr) + 22:
            # Get frequency and power of the station
            freq, power = self.find_and_remove_station(fft_arr)
            freq = round((freq + self.center_freq) / 1e6, 1)
            power = int(round(power))

            # Pack the values in a dictionary representing the
            # station and append them to the list
            station = {
                freq: power
            }
            stations.update(station)

        return stations

    def run(self):
        self.print_info()

        stations = dict()
        r, w = os.pipe()
        os.set_inheritable(r, True)
        os.set_inheritable(w, True)

        r = os.fdopen(r, 'rb')

        while True:

            # Set the SDR's center frequency so that it
            # encompasses the begining of the FM band
            self.center_freq = ScanFm.FM_BEGIN_FREQ + self.samp_rate // 2

            # Cycle through the whole band until you reach the end
            # of the FM band
            while self.center_freq < ScanFm.FM_END_FREQ:
                # Fork process
                pid = os.fork()

                if pid == 0:
                    # Close the reading end of the pipe
                    r.close()
                    # Redirect the stdin of the new process to the
                    # writting end of the pipe
                    os.dup2(w, sys.stdout.fileno())

                    # Redirect the stderr of the new process to
                    # /dev/null. Done because the programe 'rtl_sdr'
                    # starts printing info about the SDR to the
                    # stderr, which pollutes the terminal
                    err = os.open('/dev/null', os.O_WRONLY)
                    os.dup2(err, sys.stderr.fileno())

                    # Build the argument array for 'rtl_sdr'
                    # Argument descriptions can be found with
                    # 'rtl_sdr --help'
                    cmd_args = ['rtl_sdr', '-', '-f', str(self.center_freq),
                                '-s', str(self.samp_rate), '-g',
                                str(self.gain), '-b', str(self.samp_size*2),
                                '-n', str(self.samp_size)]

                    os.execvp('rtl_sdr', cmd_args)

                data = []
                # Wait for the child process to write data
                # in the pipe
                while len(data) == 0:
                    data = list(r.read(int(self.samp_size) * 2))

                # Because 'rtl_sdr' serves data byte by byte, meaning
                # that the even bytes will be the In-phase component
                # and the odd ones - the Quadrature or vice-versa
                # Thus we need to split them in order to get complex
                # numbers and normalise them between [1 + 1j] and [-1 + -1j]
                samples = ScanFm.normalise_samples(data)

                # Get the new found stations
                new_stations = self.execute(samples)

                stations = self.update_station_dict(stations, new_stations)

                # Append the returned stations from 'execute'
                # to the rest
                stations.update(new_stations)

                # Increment center frequency so that in covers
                # the adjacent frequency band
                self.center_freq += self.samp_rate

                os.system('clear')

                # Print the new station info on the terminal
                print('Frequency\t\tPower')
                print('---------\t\t-----')

                for station in stations:
                    station_str = str(station) + ' MHz\t\t' +\
                                  str(stations[station]) + ' dBm'

                    print(station_str)
