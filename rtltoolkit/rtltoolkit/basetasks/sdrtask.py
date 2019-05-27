import os
import sys
import numpy as np
import time


class SDRTask:
    defaults = {}

    def __init__(self, samp_rate, center_freq, gain, samp_size):
        # Instantiate rtl-sdr instance. If no RTL-SDR is found
        # a OSError will be raised which is handled in main.py
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.gain = gain
        self.samp_size = samp_size

        # Set the defaults if any of the above values
        # is skipped. The dicitonary 'defaults' is used from
        # the child classes to set its default values.
        self.set_defaults()

    def set_defaults(self):
        if not self.samp_rate:
            self.samp_rate = self.defaults['samp_rate']
        if not self.center_freq:
            self.center_freq = self.defaults['center_freq']
        if not self.gain:
            self.gain = self.defaults['gain']
        if not self.samp_size:
            self.samp_size = self.defaults['samp_size']

    def execute(self, samples):
        pass

    def run(self):
        print('Sampling at {} S/s'.format(self.samp_rate))
        print('Tuned to {} Hz'.format(self.center_freq))
        print('Tuner gain set to {} dB'.format(self.gain))
        print('Sample block size is {} bytes'.format(self.samp_size))

        r, w = os.pipe()
        os.set_inheritable(r, True)
        os.set_inheritable(w, True)

        pid = os.fork()

        if pid != 0:
            os.close(w)
            r = os.fdopen(r, 'rb')

            while True:
                data = list(r.read(self.samp_size * 2))
                if len(data) == 0:
                    continue
                data = np.array(data).astype(np.float64).view(np.complex128)
                data /= 127.5
                data -= (1 + 1j)
                self.execute(data)
        else:
            time.sleep(1)
            print('Listening...'.format(self.center_freq))

            os.close(r)
            os.dup2(w, sys.stdout.fileno())

            err = os.open('/dev/null', os.O_WRONLY)
            os.dup2(err, sys.stderr.fileno())

            cmd_args = ['rtl_sdr', '-', '-f', str(self.center_freq), '-s',
                        str(self.samp_rate), '-g', str(self.gain), '-b',
                        str(self.samp_size * 2)]

            os.execvp('rtl_sdr', cmd_args)
