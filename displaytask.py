from sdrtask import SDRTask

class DisplayTask(SDRTask):
    def __init__(self, samp_rate):
        super().__init__(samp_rate)
