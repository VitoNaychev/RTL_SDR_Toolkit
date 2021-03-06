import numpy as np
import pprint
from datetime import datetime

from rtltoolkit.basetasks.demodtask import DemodTask


class TempDemod(DemodTask):
    defaults = {
            'samp_rate': 1e6,
            'center_freq': 433.7e6,
            'gain': 40.2,
            'samp_size': 2**19
            }

    STAT_MSG_BITS = 36
    DIV_LEN = 0.5e-3
    ZERO_LEN = 2e-3
    ONE_LEN = 4e-3
    STOP_LEN = 8e-3

    def __init__(self, samp_rate, center_freq, gain, samp_size,
                 verbose=True, file_name=''):
        super().__init__(samp_rate, center_freq, gain, samp_size,
                         verbose, file_name)
        self.dig_data = []
        self.prev_switch = []

    def calc_magnitude(samples):
        mag = samples.real ** 2 + samples.imag ** 2
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

        if len(off_count) == 1:
            self.prev_switch.clear()

        if self.prev_switch:
            off_count.pop()

        return off_count

    def digitize_signal(off_count, samp_rate):
        dig_data = [0] * len(off_count)

        for i in range(0, len(off_count)):
            if (TempDemod.ZERO_LEN - 0.25e-3) * samp_rate < off_count[i] and\
               off_count[i] < (TempDemod.ZERO_LEN + 0.25e-3) * samp_rate:
                dig_data[i] = 0
            elif (TempDemod.ONE_LEN - 0.25e-3) * samp_rate < off_count[i] and\
                 off_count[i] < (TempDemod.ONE_LEN + 0.25e-3) * samp_rate:
                dig_data[i] = 1
            elif off_count[i] > (TempDemod.STOP_LEN - 0.25e-3) * samp_rate:
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
        msg_fields = dict()
        while True:
            beg, end = None, None

            try:
                beg = self.dig_data.index(2) + 1
            except ValueError:
                self.dig_data.clear()
                break

            try:
                end = self.dig_data[beg:].index(2) + beg
            except ValueError:
                if len(self.dig_data) - beg > TempDemod.STAT_MSG_BITS:
                    self.dig_data.clear()

                break

            sens_data = list(self.dig_data[beg:end])
            self.dig_data = self.dig_data[end:]

            if len(sens_data) != TempDemod.STAT_MSG_BITS:
                continue

            print(sens_data)
            msg_fields['HUMID'] = TempDemod.get_humidity(sens_data)
            msg_fields['TEMP'] = TempDemod.get_temp(sens_data)
            msg_fields['CHAN'] = TempDemod.get_channel(sens_data)

        return msg_fields

    def execute(self, samples):
        mag = TempDemod.calc_magnitude(samples)
        off_switch = self.calc_offswitchings(mag)
        new_data = TempDemod.digitize_signal(off_switch, self.samp_rate)
        if not np.any(new_data):
            return

        self.dig_data += new_data
        msg_fields = self.decode_data()

        if self.verbose and msg_fields:
            pprint.pprint(msg_fields)

        if self.file_name and msg_fields:
            with open(self.file_name, 'a+') as f:
                f.write('{time}\n{value}\n'.format(time=datetime.now(),
                        value=msg_fields))
