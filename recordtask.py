from sdrtask import SDRTask

class RecordTask(SDRTask):
    def __init__(self, samp_rate, center_freq, gain, samp_size, verbose, file_name, crit_val):
        super().__init__(samp_rate, center_freq, gain, samp_size)
        self.verbose = verbose
        self.file_name = file_name
        self.crit_val = crit_val
