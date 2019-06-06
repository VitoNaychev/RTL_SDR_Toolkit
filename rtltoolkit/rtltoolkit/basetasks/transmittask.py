import os
import sys
import time
from rtltoolkit.helpers.filtertuner import FilterTuner


class TransmitTask:
    def __init__(self, samp_rate, center_freq, gain, samp_size):
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.gain = gain
        self.samp_size = samp_size
        self.tuner = FilterTuner()
        

    def execute(self):
        pass

    def run(self):
        try:
            print('Attempting to configure filter')
            self.tuner.tune(self.center_freq)
        except ValueError:
            print('Center frequency outside of filter range')
            print('TRANSMITTING WITHOUT FILTER')

        r, w = os.pipe()
        os.set_inheritable(r, True)
        os.set_inheritable(w, True)

        pid = os.fork()

        if pid != 0:
            os.close(r)
            w = os.fdopen(w, 'wb')

            while True:
                data = self.execute()
                w.write(data)
        else:
            time.sleep(1)
            print('Beggining transmission...')
            os.close(w)
            os.dup2(r, sys.stdin.fileno())
            cmd_args = ['sendiq', '-i', '-', '-s', str(self.samp_rate), '-f',
                        str(self.center_freq), '-t', 'double']

            os.execvp('sendiq', cmd_args)
