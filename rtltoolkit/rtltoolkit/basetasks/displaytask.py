from rtltoolkit.basetasks.sdrtask import SDRTask

class DisplayTask(SDRTask):
    def __init__(self, samp_rate, center_freq, gain, samp_size):
        super().__init__(samp_rate, center_freq, gain, samp_size)
