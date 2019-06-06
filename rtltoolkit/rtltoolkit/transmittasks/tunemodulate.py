import numpy as np
import wave

from rtltoolkit.basetasks.transmittask import TransmitTask

class TuneModulate(TransmitTask):
    def __init__(self, samp_rate, center_freq, gain, samp_size, file_name):
        super().__init__(samp_rate, center_freq, gain, samp_size)
        self.tune_file = wave.open(file_name, 'rb')
        self.samp_rate = self.tune_file.getframerate()


    def modulate_wave(tune_wav, coef):
        mod_r = np.cos(2 * np.pi * coef * tune_wav)
        mod_i = np.sin(2 * np.pi * coef * tune_wav)
        mod_wav = mod_r + mod_i * 1j

        return mod_wav

    def execute(self):
        tune_arr = list(self.tune_file.readframes(self.samp_size))
        if len(tune_arr) == 0:
            self.tune_file.rewind()
            tune_arr = list(self.tune_file.readframes(self.samp_size))

        tune_arr = np.array(tune_arr, dtype=np.float64)
        tune_arr *= 255 / max(tune_arr)
        tune_arr /= 127.5
        tune_arr -= 1

        samp_arr = TuneModulate.modulate_wave(tune_arr, 2)

        return samp_arr
