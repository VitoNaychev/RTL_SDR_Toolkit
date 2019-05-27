import os
import sys
import time


class TransmitTask:
    def __init__(self, samp_rate, center_freq, gain, samp_size):
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.gain = gain
        self.samp_size = samp_size

    def execute(self):
        pass

    def run(self):
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
            os.dup2()
            cmd_args = ['sendiq', '-i', '-', '-s', str(self.samp_rate), '-f',
                        str(self.center_freq), '-t', 'double']

            os.execvp('sendiq', cmd_args)
