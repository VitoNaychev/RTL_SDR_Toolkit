import matplotlib.pyplot as plt
import numpy as np
import helpers
from scipy.fftpack import fft
from displaytask import DisplayTask
from enum import Enum
import os
import time

class FftSink(DisplayTask):
    defaults = {
            'samp_rate' : 2e6,
            'center_freq' : 92.4e6,
            'gain' : 40.1,
            'samp_size' : 2**13
            }

    def __init__(self, samp_rate, center_freq, gain, samp_size, cmd, limit, persis = False):
        super().__init__(samp_rate, center_freq, gain, samp_size)
        self.limit = limit
        self.persis = persis
        self.flag = True

        if cmd:
            self.init_cmd_fft()
        else:
            self.init_inter_fft()

    def init_cmd_fft(self):
        pass

    def init_inter_fft(self):
        plt.ion()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        if limit:
            self.ax.set_ylim(limit, 0)

        # variables to be initailised in the execute method to 
        # use one less parameter in initialisation of class
        self.persis_arr = None
        self.line1 = None
        self.line2 = None
    

    def update_inter_fft(self, samp_fft):
        if self.persis:
            for i, sf in enumerate(samp_fft, 0):
                if sf > self.persis_arr[i]:
                    self.persis_arr[i] = sf

        self.line1.set_ydata(samp_fft)
        if self.persis:
            self.line2.set_ydata(self.persis_arr)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update_cmd_fft(self, samp_fft):
        # Clear tty from last render
        os.system('clear')

        # Get the current size of the tty window
        rows, columns = os.popen('stty size', 'r').read().split()
        rows = int(rows)
        columns = int(columns)

        y_axis_size = 7
        # We divide the FFT into larger frequency band 'chunks' due to the
        # limitations of the command line. The count of the chunks is
        # equal to the width of the tty window
        ch_count = columns - y_axis_size - 1

        # Caclulate what part of the FFT each chunk will hold
        chunk_size = len(samp_fft) // ch_count
        
        # Calculate the corresponding FFT for each chunk
        # by taking the average value from the original FFT
        # for each chunk size
        chunks_fft = [np.average(samp_fft[x:x+chunk_size]) for x in range(0, len(samp_fft), chunk_size)]
        chunks_fft = np.array(chunks_fft)

        # Calculate the scaling factor for the chunks 
        # by taking the absolute value of the limit
        scale = rows / abs(self.limit)

        # We first move the FFT to the positive side of the
        # nuerical values so that the smallest value will equal 
        # 0 and the largest will equal the absolute value of the
        # limit. 
        scaled_chunks = ((np.array(chunks_fft) + abs(self.limit)) * scale)

        # After that we convert the array to a numpy one
        # and round each value. This way we have a scaled
        # integer representing the numbers of characters 
        # that will form the FFT's value
        pilars = np.round(scaled_chunks).astype(int)

        for i in range(rows, 0, -1):
            # First we take the inverted scale so we can
            # convert between rows and dBm
            inv_scale = 1 / scale
            
            # Next we want the values to be evenly spaced
            # and also this scale to change when the size 
            # of the tty changes
            if i % round(scale * 10) == 0:
                pilar_row = str(round((i - rows) * inv_scale)) + ' -- '
            else:
                pilar_row = ' ' * y_axis_size

            pilar_row += ''.join(['|' if pilar >= i else ' ' for pilar in pilars])
                
            print(pilar_row)

        # We want to show the x axis underneath the FFT plot
        # therefore we need to make a scaling between the
        # columns and the frequency band. Because the frequencies
        # will be shown in MHz we will space them in .25 MHz chunks
        freq_scale = ch_count / (self.samp_rate / 1e6)
        
        # It is highly unlikely that by multiplying the current
        # column times the frequency scale we will get a 
        # number that can be divided percicely by 25. Because of
        # this we multiply the frequency scale by 0.25 and after
        # rounding the number we get the closest column that can represent
        # the current frequency
        x_axis = ' ' * y_axis_size
        while i < columns:
            if i % round(freq_scale * 0.25) == 0:
                # Get the frequency of the current column starting 
                # with respect to the first one which has a relative
                # value of 0 Hz when calculated with this equation
                freq_val = i / round(freq_scale * 0.25) * 0.25

                # Subtract the sampling rate divided by two to get
                # the positive and negative freqency spectrumn
                freq_val -= round(self.samp_rate / 1e6, 2) / 2
                
                # Sum with the center frequency of the SDR to get
                # the actual frequency band we are representing
                freq_val += round(self._sdr.center_freq / 1e6, 2)
                
                # Round the frequency value to the second
                # decimal place
                freq_val = round(freq_val, 2)
                
                # Convert to string and add the MHz lable
                lable_str = str(freq_val) + ' MHz'

                # Check if the lable that we are trying to add to
                # the X axis is going to exceed the column count
                if i + len(lable_str) >= columns - y_axis_size:
                    # If yes break the while cycle and continue to
                    # print.
                    break
                else:   
                    # Else add the length of the string to the
                    # counter 'i' and add the string to the
                    # lable field
                    i += len(lable_str)
                    x_axis += lable_str
            else:
                x_axis += ' '
                i += 1

        print(x_axis)
        
        

    def execute(self, samples):
        # if self.flag:
        #     x = np.linspace(-self.samp_rate / 2, self.samp_rate/2, len(samples))
        #     self.persis_arr = [self.limit - 10] * len(x)
        #     
        #     self.line1, = self.ax.plot(x, [self.limit] * len(x))
        #     self.line2, = self.ax.plot(x, self.persis_arr) # linewidth=0.5 to change line width
        #     self.flag = False
        #     
        samp_fft = helpers.calc_fft(samples, self.samp_rate, len(samples), True)
        
        if cmd:
            self.update_inter_fft(samp_fft)
        else:
            self.update_cmd_fft(samp_fft)

