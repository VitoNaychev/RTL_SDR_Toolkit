import numpy as np
from datetime import datetime

from rtltoolkit.basetasks.demodtask import DemodTask


class TempDemod(DemodTask):
    defaults = {
            'samp_rate': 1e6,
            'center_freq': 433.7e6,
            'gain': 40.2,
            'samp_size': 2**19
            }

    def __init__(self, samp_rate, center_freq, gain, samp_size, verbose=True, file_name=''):
        super().__init__(samp_rate, center_freq, gain, samp_size,  verbose, file_name)
        self.dig_data = []
        self.prev_switch = []

    def calc_magnitude(samples):
        mag = samples.real ** 2 + samples.imag ** 2
        TempDemod.calc_mean_ampl(mag)
        return mag

    def calc_mean_ampl(samp_ampl):
        # return sum(samp_ampl) / len(samp_ampl)
        return (max(samp_ampl) + min(samp_ampl)) / 2

    def calc_offswitchings(self, samp_ampl):
        j = 0
        off_count = [0]  # number of samples in each off-switching
        samp_ampl = np.concatenate([self.prev_switch, samp_ampl])

        ampl_mean = TempDemod.calc_mean_ampl(samp_ampl)

        for i in range(1, len(samp_ampl)):
            if samp_ampl[i] < ampl_mean and samp_ampl[i - 1] < ampl_mean:
                off_count[j] += 1
                self.prev_switch.append(samp_ampl[i])
            elif samp_ampl[i] > ampl_mean and samp_ampl[i - 1] < ampl_mean:
                j += 1
                off_count.append(0)
                self.prev_switch.clear()

        if self.prev_switch:
            off_count.pop()

        return off_count

    def digitize_signal(off_count):
        dig_data = [0] * len(off_count)

        for i in range(0, len(off_count)):
            if off_count[i] < 3000 and off_count[i] > 1000:
                dig_data[i] = 0
            elif off_count[i] > 3000 and off_count[i] < 6000:
                dig_data[i] = 1
            elif off_count[i] > 6000:
                dig_data[i] = 2

        return dig_data

    def get_humidity(sens_data):
        humid_int = 0
        humid_bin = sens_data[28:36]
        for bin_num in humid_bin:
            humid_int = (humid_int << 1) | bin_num
        return humid_int

    def get_temp(sens_data):
        temp_int = 0
        temp_bin = sens_data[16:28]
        for bin_num in temp_bin:
            temp_int = (temp_int << 1) | bin_num
        return temp_int / 10

    def get_channel(sens_data):
        chan_int = 0
        chan_bin = sens_data[14:16]
        for bin_num in chan_bin:
            chan_int = (chan_int << 1) | bin_num
        return chan_int + 1

    def decode_data(self):
        str_data = []
        while True:
            try:
                beg = self.dig_data.index(2) + 1
                end = self.dig_data[beg:].index(2) + beg
                sens_data = list(self.dig_data[beg:end])
                self.dig_data = self.dig_data[end:]

                if len(sens_data) != 36:
                    continue

                print(sens_data)
                humid_int = TempDemod.get_humidity(sens_data)
                temp_int = TempDemod.get_temp(sens_data)
                chan_int = TempDemod.get_channel(sens_data)

                str_data.append("Temperature: " + str(temp_int) + "°C " + "Humidity: "
                                 + str(humid_int) + "% " + "Channel: " + str(chan_int))
            except ValueError:
                break

        return str_data

    def execute(self, samples):
        mag = TempDemod.calc_magnitude(samples)
        off_switch = self.calc_offswitchings(mag)
        new_data = TempDemod.digitize_signal(off_switch)
        if not np.any(new_data):
            return

        self.dig_data += new_data
        str_data = self.decode_data()

        for string in str_data:
            if self.verbose:
                print(string)

        if self.file_name:
            with open(self.file_name, 'a+') as f:
                for string in str_data:
                    f.write('{time}\n{value}\n'.format(time=datetime.now(), value=string))
