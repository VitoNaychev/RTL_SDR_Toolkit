import matplotlib.pyplot as plt
import numpy as np
import helpers
from scipy.fftpack import fft
from displaytask import DisplayTask
from enum import Enum
import os

class Pilars(Enum):
    P0 =   '.'
    P10 =  '|'
    P15 =  '||'
    P20 =  '|||'
    P25 =  '||||'
    P30 =  '|||||'
    P35 =  '||||||'
    P40 =  '|||||||'
    P45 =  '||||||||'
    P50 =  '|||||||||'
    P55 =  '||||||||||'
    P60 =  '|||||||||||'
    P65 =  '||||||||||||'
    P70 =  '|||||||||||||'
    P75 =  '||||||||||||||'
    P80 =  '|||||||||||||||'
    P85 =  '||||||||||||||||'
    P90 =  '|||||||||||||||||'
    P95 =  '||||||||||||||||||'
    P100 = '|||||||||||||||||||'

    def get_pilar(val):
        return list(Pilars)[val // 10]

class FftSink(DisplayTask):
    def __init__(self, samp_rate, lower_lim, persis = False):
        super().__init__(samp_rate)
        self.lower_lim = lower_lim
        self.persis = persis
        self.flag = True

        # plt.ion()
        # self.fig = plt.figure()
        # self.ax = self.fig.add_subplot(111)
        # if lower_lim:
        #     self.ax.set_ylim(lower_lim, 0)

        # # variables to be initailised in the execute method to 
        # # use one less parameter in initialisation of class
        # self.persis_arr = None
        # self.line1 = None
        # self.line2 = None

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

    def cmd_fft(self, samp_fft):
        os.system('clear')
        # We divide the FFT into larger frequency band 'chunks' due to the
        # limitations of the command line. The purpose of this sink is 
        # only demostrative
        ch_count = 80
        chunk_size = len(samp_fft) // ch_count
        chunks_fft = [np.average(samp_fft[x:x+chunk_size]) for x in range(0, len(samp_fft), chunk_size)]
        chunk_scale =  -1 * 100 / self.lower_lim

        chunk_pilars = []

        for chunk in chunks_fft:
            if chunk < self.lower_lim:
                chunk = self.lower_lim
            ind = int(round((chunk + abs(self.lower_lim)) * chunk_scale / 5)) * 5
            chunk_pilars.append(Pilars.get_pilar(ind).value)
        
        for i in range(19, 0, -1):
            pilar_row = ''
            for pilar in chunk_pilars:
                if len(pilar) > i:
                    pilar_row += pilar[i]
                else:
                    pilar_row += ' '
            print(pilar_row)
                
        

    def execute(self, samples):
        # if self.flag:
        #     x = np.linspace(-self.samp_rate / 2, self.samp_rate/2, len(samples))
        #     self.persis_arr = [self.lower_lim - 10] * len(x)
        #     
        #     self.line1, = self.ax.plot(x, [self.lower_lim] * len(x))
        #     self.line2, = self.ax.plot(x, self.persis_arr) # linewidth=0.5 to change line width
        #     self.flag = False
        #     
        samp_fft = helpers.calc_fft(samples, self.samp_rate, len(samples), True)
        # self.update_fft(samp_fft)
        self.cmd_fft(samp_fft)



