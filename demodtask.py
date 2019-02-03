from sdrtask import SDRTask

class DemodTask(SDRTask):
    def __init__(self, samp_rate, verbose, file_name):
        super().__init__(samp_rate)
        self.verbose = verbose
        self.file_name = file_name
