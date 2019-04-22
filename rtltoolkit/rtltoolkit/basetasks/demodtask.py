from rtltoolkit.basetasks.sdrtask import SDRTask


class DemodTask(SDRTask):
    def __init__(self, samp_rate, center_freq, gain, samp_size, verbose, file_name):
        super().__init__(samp_rate, center_freq, gain, samp_size)
        self.verbose = verbose
        self.file_name = file_name
