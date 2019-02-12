import matplotlib.pyplot as plt
import numpy as np
import helpers
from scipy.fftpack import fft
from displaytask import DisplayTask
from enum import Enum
import os

class FftSink(DisplayTask):
    def __init__(self, samp_rate, lower_lim, persis = False):
        super().__init__(samp_rate)
        self.lower_lim = lower_lim
        self.persis = persis
        self.flag = True

        plt.ion()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        if lower_lim:
            self.ax.set_ylim(lower_lim, 0)

        # variables to be initailised in the execute method to 
        # use one less parameter in initialisation of class
        self.persis_arr = None
        self.line1 = None
        self.line2 = None

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

        chunk_size = len(samp_fft) // 40
        chunks_fft = [np.average(samp_fft[x:x+40]) for x in range(0, len(samp_fft), 40)]
        chunk_scale =  100 / self.limt
        chunk_pilars = []

        for chunk in chunks_fft:
            chunk_pilars.append(Pilars.get_pilars(round(chunk * chunk_scale)))
        
        for i in range(9, 0, -1):
            pilar_row = ''
            for pilar in chunk_pilars:
                pilar_row += pilar[i]
            print(pilar_row)
                
        

    def execute(self, samples):
        if self.flag:
            x = np.linspace(-self.samp_rate / 2, self.samp_rate/2, len(samples))
            self.persis_arr = [self.lower_lim - 10] * len(x)
            
            self.line1, = self.ax.plot(x, [self.lower_lim] * len(x))
            self.line2, = self.ax.plot(x, self.persis_arr) # linewidth=0.5 to change line width
            self.flag = False
            
        samp_fft = helpers.calc_fft(samples, self.samp_rate, len(samples), True)
        self.update_fft(samp_fft)



class Pilars(Enum):
    P0 =   '.'
    P10 =  '|'
    P20 =  '||'
    P30 =  '|||'
    P40 =  '||||'
    P50 =  '|||||'
    P60 =  '||||||'
    P70 =  '|||||||'
    P80 =  '||||||||'
    P90 =  '|||||||||'
    P100 = '||||||||||'

    def get_pilar(val):
        return list(Pilars)[val // 10]

