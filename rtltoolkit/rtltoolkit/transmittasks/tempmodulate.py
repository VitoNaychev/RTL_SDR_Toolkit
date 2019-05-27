import numpy as np

from rtltoolkit.basetasks.transmittask import TransmitTask


class TempModulate(TransmitTask):
    DIV_LEN = 0.5e-3   # in seconds
    ZERO_LEN = 2e-3
    ONE_LEN = 4e-3
    STOP_LEN = 8e-3

    ID_BITS = 4
    CHKSUM_BITS = 10
    CHAN_BITS = 2
    TEMP_BITS = 12
    HUMID_BITS = 8

    ON_FREQ = 1e3      # in hertz

    def __init__(self, samp_rate, center_freq, gain, samp_size):
        super().__init__(samp_rate, center_freq, gain, samp_size)

    def encode_data(chan, temp, humid):
        id_bits = [0, 1, 0, 1]
        chksum_bits = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        chan_bits = []
        temp_bits = []
        humid_bits = []

        for i in range(TempModulate.CHAN_BITS):
            chan_bits.append(chan % 2)
            chan = chan // 2
        chan_bits.reverse()

        temp *= 10
        for i in range(TempModulate.TEMP_BITS):
            temp_bits.append(temp % 2)
            temp = temp // 2
        temp_bits.reverse()

        for i in range(TempModulate.HUMID_BITS):
            humid_bits.append(humid % 2)
            humid = humid // 2
        humid_bits.reverse()

        data_frame = id_bits + chksum_bits + chan_bits + temp_bits + humid_bits

        return data_frame

    def generate_iq(on_freq, on_len, samp_rate):
        per_arr = np.arange(0, on_len, 1/samp_rate)
        wave_r = np.cos(2 * np.pi * on_freq * per_arr)
        wave_i = np.sin(2 * np.pi * on_freq * per_arr)
        wave = wave_r + wave_i * 1j

        return wave

    def modulate_data(data, samp_rate):
        signal = []
        on_wav = list(TempModulate.generate_iq(TempModulate.ON_FREQ,
                                               TempModulate.DIV_LEN,
                                               samp_rate))

        one_wav = int(TempModulate.ONE_LEN * samp_rate) * [0 + 0j]
        zero_wav = int(TempModulate.ZERO_LEN * samp_rate) * [0 + 0j]
        stop_wav = int(TempModulate.STOP_LEN * samp_rate) * [0 + 0j]

        for bit in data:
            if bit == 1:
                signal += one_wav
            else:
                signal += zero_wav

            signal += on_wav

        signal += stop_wav

        return np.array(signal)

    def execute(self):
        data = TempModulate.encode_data(1, 10, 15)
        signal = TempModulate.modulate_data(data, self.samp_rate)

        return signal
