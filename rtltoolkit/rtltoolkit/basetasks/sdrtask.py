import os
import sys
import numpy as np


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

    def print_info(self):
        print('Sampling at {} S/s'.format(self.samp_rate))
        print('Tuned to {} Hz'.format(self.center_freq))
        print('Tuner gain set to {} dB'.format(self.gain))
        print('Sample block size is {} bytes'.format(self.samp_size))

    def normalise_samples(data):
        data = np.array(data).astype(np.float64).view(np.complex128)
        data /= 127.5
        data -= (1 + 1j)

        return data

    def run(self):
        # Print SDR tuning info
        self.print_info()

        # Create pipe for communication between the
        # 'rtl_sdr' process and the main program
        r, w = os.pipe()
        os.set_inheritable(r, True)
        os.set_inheritable(w, True)

        # Fork process
        pid = os.fork()

        if pid != 0:
            # Close the write end of the parent process
            os.close(w)
            r = os.fdopen(r, 'rb')

            while True:
                data = []
                # Wait for the child process to append data to
                # the pipe
                while len(data) == 0:
                    data = list(r.read(self.samp_size * 2))

                # Because 'rtl_sdr' serves data byte by byte, meaning
                # that the even bytes will be the In-phase component
                # and the odd ones - the Quadrature or vice-versa
                # Thus we need to split them in order to get complex
                # numbers and normalise them between [1 + 1j] and [-1 + -1j]
                samples = SDRTask.normalise_samples(data)
                # Call the execute function to process the incoming signal
                self.execute(samples)
        else:
            print('Listening...'.format(self.center_freq))

            # Close the read end of the pipe
            os.close(r)
            # Redirect the stdin of the new process to the
            # writting end of the pipe
            os.dup2(w, sys.stdout.fileno())

            # Redirect the stderr of the new process to
            # /dev/null. Done because the programe 'rtl_sdr'
            # starts printing info about the SDR to the
            # stderr, which pollutes the terminal
            err = os.open('/dev/null', os.O_WRONLY)
            os.dup2(err, sys.stderr.fileno())

            # Build the argument array for 'rtl_sdr'
            # Argument descriptions can be found with
            # 'rtl_sdr --help'
            cmd_args = ['rtl_sdr', '-', '-f', str(self.center_freq), '-s',
                        str(self.samp_rate), '-g', str(self.gain), '-b',
                        str(self.samp_size * 2)]

            # Execute 'rtl-sdr' in the child process
            os.execvp('rtl_sdr', cmd_args)
