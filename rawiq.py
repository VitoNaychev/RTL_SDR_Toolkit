from recordsamp import RecordSamp
import helpers
from sdrtask import SDRTask
from recordtask import RecordTask
import numpy as np

class RawIQ(RecordTask):
    def __init__(self, samp_rate, center_freq, gain, samp_size, verbose, file_name, diff):
        super().__init__(samp_rate, center_freq, gain, samp_size, verbose, file_name, diff)
        self.samp_record = RecordSamp(file_name)
        self.count = 0
        self.verbose = verbose

    def execute(self, samples):
        samples = np.array(samples)
        if self.verbose:
            print(samples)

        samp_fft = None
        if self.diff:
            samp_fft = helpers.calc_fft(samples, self.samp_rate, len(samples), average = True)
            if min(samp_fft[100:]) + self.diff > max(samp_fft[100:]):
                samples = np.array([])

        self.samp_record.add_to_queue(samples)

        if self.diff and not samples.any() and not self.samp_record.is_queue_empty():
            self.samp_record.save_to_file(self.file_name + str(self.count) + '.npy')
            self.samp_record.empty_queue()
            self.count += 1

        if not self.diff:
            self.samp_record.save_to_file()
