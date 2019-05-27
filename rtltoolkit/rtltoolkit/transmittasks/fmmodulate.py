import numpy as np

from rtltoolkit.basetasks.transmittask import TransmitTask


class FmModulate(TransmitTask):
    def __init__(self, samp_rate, center_freq, gain, samp_size, tune_freq):
        super().__init__(samp_rate, center_freq, gain, samp_size)
        self.tune_freq = tune_freq

    def generate_sin(tune_freq, sig_len, samp_rate):
        per_arr = np.arange(0, sig_len, 1/samp_rate)
        sin_wav = np.sin(2 * np.pi * tune_freq * per_arr)
        return sin_wav

    def modulate_wave(sin_wav, coef, samp_rate, sig_len):
        mod_r = np.cos(2 * np.pi * coef * sin_wav)
        mod_i = np.sin(2 * np.pi * coef * sin_wav)
        mod_wav = mod_r + mod_i * 1j

        return mod_wav

    def execute(self):
        sig_len = self.samp_size / self.samp_rate
        sin_wav = FmModulate.generate_sin(self.tune_freq,
                                          sig_len, self.samp_rate)
        mod_wav = FmModulate.modulate_wave(sin_wav, 1,
                                           self.samp_rate, sig_len)

        return mod_wav
