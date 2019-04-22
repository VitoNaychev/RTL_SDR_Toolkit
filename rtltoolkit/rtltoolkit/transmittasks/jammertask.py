import numpy as np

from rtltoolkit.basetasks.transmittask import TransmitTask


class JammerTask(TransmitTask):
    def __init__(self):
        # No need to ''oversample the sinusoid
        # mainly because we won't be transmitting
        # data with it and it will come out as a
        # square wave from the Raspberry Pi's pin
        # so  we will use only 4 point to represent it
        super().__init__(4, '')

    def execute(self):
        sin_data = []
        sin_data.append(np.around(np.sin(np.pi * 0 / 4), 2)
                        + np.around(np.cos(np.pi * 0 / 4), 2) * 1j)
        sin_data.append(np.around(np.sin(np.pi * 1 / 4), 2)
                        + np.around(np.cos(np.pi * 1 / 4), 2) * 1j)
        sin_data.append(np.around(np.sin(np.pi * 2 / 4), 2)
                        + np.around(np.cos(np.pi * 2 / 4), 2) * 1j)
        sin_data.append(np.around(np.sin(np.pi * 3 / 4), 2)
                        + np.around(np.cos(np.pi * 3 / 4), 2) * 1j)
        for i in range(1e6):
            sin_data += sin_data

        return np.array(sin_data)
