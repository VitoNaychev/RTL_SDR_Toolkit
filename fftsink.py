import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fft

class FftSink:
    def __init__(self, samp_rate, samp_len, y_lower_lim = -60, persis = False):
        self.samp_rate = samp_rate
        self.samp_len = samp_len
        self.persis = persis

        x = np.linspace(-samp_rate / 2, samp_rate/2, samp_len)
        self.persis_arr = [y_lower_lim - 10] * len(x)

        plt.ion()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_ylim(y_lower_lim, 0)
        self.line1, = self.ax.plot(x, [y_lower_lim] * len(x))
        self.line2, = self.ax.plot(x, self.persis_arr) # linewidth=0.5 to change line width

    def moving_average(samps, n=3):
        cumsum, moving_aves = [0], []

        for i, x in enumerate(samps, 1):
            cumsum.append(cumsum[i-1] + x)
            if i>=n:
                moving_ave = (cumsum[i] - cumsum[i-n])/n
            else:
                moving_ave = (cumsum[i] - cumsum[0]) / i

            moving_aves.append(moving_ave)

        return moving_aves


    def calc_fft(samples, samp_rate, samp_len, average = False):
        samp_fft = 20 * np.log10(2.0/samp_len * np.abs(fft(samples)))
        neg_fft = samp_fft[len(samp_fft) // 2:]
        samp_fft = np.concatenate((neg_fft, samp_fft[:len(samp_fft) // 2]))
        if(average):
            samp_fft = FftSink.moving_average(samp_fft, 100)
        return samp_fft

    def update_fft(self, samp_fft):
        if self.persis:
            for i, sf in enumerate(samp_fft, 0):
                if sf > self.persis_arr[i]:
                    self.persis_arr[i] = sf

        self.line1.set_ydata(samp_fft)
        if self.persis:
            self.line2.set_ydata(self.persis_arr)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
