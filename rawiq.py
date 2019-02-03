from recordsamp import RecordSamp
from fftsink import FftSink
from sdrtask import SDRTask
from recordtask import RecordTask
import numpy as np

class RawIQ(RecordTask):
    def __init__(self, samp_rate, verbose = False, file_name = '', on_active = False, diff = 0):
        super().__init__(samp_rate, verbose, file_name, on_active, diff)
        self.samp_record = RecordSamp(file_name)
        self.count = 0
        self.verbose = verbose

    def execute(self, samples):
        samples = np.array(samples)
        if self.verbose:
            print(samples)
        samp_fft = None
        if self.on_active:
            samp_fft = FftSink.calc_fft(samples, self.samp_rate, len(samples), average = True)
            if min(samp_fft[100:]) + self.diff > max(samp_fft[100:]):
                samples = np.array([])

        self.samp_record.add_to_queue(samples)
        if self.on_active and not samples.any() and not self.samp_record.is_queue_empty():
            print("KUR KUR")
            self.samp_record.save_to_file(self.file_name + str(self.count) + "_dif_" +
                    str(int(round(max(samp_fft[100:]) - min(samp_fft[100:])))) + '.npy')
            self.samp_record.empty_queue()
            self.count += 1
