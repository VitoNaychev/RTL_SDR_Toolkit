import numpy as np

from rtltoolkit.basetasks.transmittask import TransmitTask


class JammerTask(TransmitTask):
    def __init__(self, samp_rate, center_freq, gain, samp_size):
        super().__init__(samp_rate, center_freq, gain, samp_size)

    def generate_iq(samp_rate, samp_size):
        sig_len = samp_size / samp_rate
        per_arr = np.arange(0, sig_len, 1/samp_rate)
        freq = samp_rate / 100

        sin_wav = np.sin(2 * np.pi * freq * per_arr)
        cos_wav = np.cos(2 * np.pi * freq * per_arr)
        iq_wav = cos_wav + sin_wav * 1j
        return iq_wav

    def execute(self):
        iq_wav = JammerTask.generate_iq(self.samp_rate, self.samp_size)
        return iq_wav
