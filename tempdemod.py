import numpy as np
import math
from datetime import datetime
import matplotlib.pyplot as plt

class TempDemod:
    def __init__(self, samp_rate, output = True, file_name = ''):
        self.samp_rate = samp_rate
        self.output = output
        self.file_name = file_name
        self.dig_data = []
    
    def calc_ampl(samples):
        samp_ampl = samples.real ** 2 + samples.imag ** 2
        TempDemod.calc_mean_ampl(samp_ampl)
        return samp_ampl
    
    def calc_mean_ampl(samp_ampl):
        return sum(samp_ampl) / len(samp_ampl)

    def calc_offswitchings(samp_ampl):
        j = 0
        off_count = [0] # number of samples in each off-switching
        
        ampl_mean = TempDemod.calc_mean_ampl(samp_ampl)

        for i in range(1, len(samp_ampl)):
            if samp_ampl[i] < ampl_mean and samp_ampl[i - 1] < ampl_mean:
                off_count[j] += 1
            elif samp_ampl[i] > ampl_mean and samp_ampl[i - 1] < ampl_mean:
                j += 1
                off_count.append(0)
        # print("Off count:", len(off_count))
        plt.plot(off_count, 'r.')
        plt.show()
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
        print(self.dig_data) 
        while True:
            try:
                beg = 0
                end = 0
                for i, bin_num in enumerate(self.dig_data, 0):
                    if bin_num == 2 and beg == end:
                        end = i
                    elif bin_num == 2:
                        beg = end
                        end = i
                        break

                if end == 0:
                    break

                sens_data = list(self.dig_data[beg + 1:end])
                self.dig_data = self.dig_data[end:]
                
                print("Beg", beg)
                print("End", end)
                print("Data:", sens_data)
                print("Len:", len(sens_data))
                
                humid_int = TempDemod.get_humidity(sens_data)
                temp_int = TempDemod.get_temp(sens_data)
                chan_int = TempDemod.get_channel(sens_data)

                str_data.append("Temperature: " + str(temp_int) + "°C " + "Humidity: " 
                                 + str(humid_int) + "% " + "Channel: " + str(chan_int))
            except ValueError:
                break

        return str_data
    
    def execute(self, samples):
        samp_ampl = TempDemod.calc_ampl(samples)
        off_switch = TempDemod.calc_offswitchings(samp_ampl)
        new_data = TempDemod.digitize_signal(off_switch)
        if not np.any(new_data):
            return

        self.dig_data += new_data
        str_data = self.decode_data()
        if self.output:
            for string in str_data:
                print(string)
            

