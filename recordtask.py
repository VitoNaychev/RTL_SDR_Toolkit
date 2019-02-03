from sdrtask import SDRTask

class RecordTask(SDRTask):
    def __init__(self, samp_rate, verbose, file_name, on_active, diff):
        super().__init__(samp_rate)
        self.verbose = verbose
        self.file_name = file_name
        self.on_active = on_active
        self.diff = diff
