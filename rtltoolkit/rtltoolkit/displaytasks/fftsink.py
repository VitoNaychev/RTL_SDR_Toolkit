import matplotlib.pyplot as plt
import numpy as np
import os

from rtltoolkit.basetasks.displaytask import DisplayTask
from rtltoolkit.helpers import ffthelpers


# 1.Fix labling and exponent in the interactive plot
class FftSink(DisplayTask):
    defaults = {
            'samp_rate': 2e6,
            'center_freq': 92.4e6,
            'gain': 40.1,
            'samp_size': 2**13
            }

    def __init__(self, samp_rate, center_freq, gain, samp_size, cmd, limit, persis = False):
        super().__init__(samp_rate, center_freq, gain, samp_size)
        self.limit = limit
        self.persis = persis
        self.cmd = cmd

        # Depending on the mode initiate the correct FFT plot
        if self.cmd:
            self.init_cmd_fft()
        else:
            self.init_inter_fft()

    def init_cmd_fft(self):
        pass

    def init_inter_fft(self):
        # Iniciate pyplot interactive mode
        plt.ion()

        # Create a Figure
        self.fig = plt.figure()

        # Get the Axes from the subplot
        self.ax = self.fig.add_subplot(111)

        # Set the Y axes lower limit to 'limit'
        if self.limit:
            self.ax.set_ylim(self.limit, 0)

        # Create an array representing the x shape of the plot
        x_shape = np.linspace(-self.samp_rate / 2, self.samp_rate/2, self.samp_size)
        x_shape += self.center_freq

        # Create the persistence array and set it's value bellow
        # the lower limit
        self.persis_arr = [self.limit - 10] * self.samp_size

        # Create the FFT and Persistance Line2D objects by
        # calling the Axis.plot method
        self.fft_line, = self.ax.plot(x_shape, [self.limit] * self.samp_size)
        self.persis_line, = self.ax.plot(x_shape, self.persis_arr)

    def update_inter_fft(self, fft_arr):
        # Set the new data for the FFT line
        self.fft_line.set_ydata(fft_arr)
        if self.persis:
            # Check if any of the new FFT values exceeds the
            # persistence arrays values and update them if yes
            self.persis_arr = [fft_samp if persis_samp < fft_samp else persis_samp \
                            for fft_samp, persis_samp in zip(fft_arr, self.persis_arr)]
            # Set the new data for the persistence line
            self.persis_line.set_ydata(self.persis_arr)

        # Update the new data on the canvas
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def update_cmd_fft(self, fft_arr):
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
        chunk_size = len(fft_arr) // ch_count

        # Calculate the corresponding FFT for each chunk
        # by taking the average value from the original FFT
        # for each chunk size
        chunks_fft = [np.average(fft_arr[x:x+chunk_size]) for x in range(0, len(fft_arr), chunk_size)]
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
                freq_val += round(self.center_freq / 1e6, 2)

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
        # Calculate FFT of current samples
        fft_arr = ffthelpers.calc_fft(samples, self.samp_rate, len(samples), True)

        # Depending on the chosen mode update the FFT plot
        if self.cmd:
            self.update_cmd_fft(fft_arr)
        else:
            self.update_inter_fft(fft_arr)
