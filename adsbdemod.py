import numpy as np
from sdrtask import SDRTask

class ADSBDemod(SDRTask):
    MODES_PREAMBLE = 8          # microseconds
    MODES_LONG_MSG_BITS = 112
    MODES_SHORT_MSG_BITS = 56
    MODES_FILL_LEN = MODES_PREAMBLE + MODES_LONG_MSG_BITS
    
    def __init__(self, samp_rate, verbose = True, file_name = ''):
        super().__init__(samp_rate, verbose, file_name)
    
    def calc_magnitude(samples):
        samples *= np.around(255)
        samp_mag = np.around(np.absolute(samples) * 360)
        return samp_mag

    def detect_out_phase(samp_mag):

        if samp_mag[3] > samp_mag[2] / 3: return 1
        if samp_mag[10] > samp_mag[9] / 3: return 1
        if samp_mag[6] > samp_mag[7] / 3: return 1
        # if samp_mag[-1] > samp_mag[1] / 3 return 1
        return 0
    
    def correct_phase(samp_mag):
        data_bits = samp_mag[16:]
        for i in range(0, ADSBDemod.MODES_LONG_BITS*2 - 2, 2):
            if(data_bits[i] > data_bits[i + 1]):
                data_bits[i + 2] = (data_bits[i + 2] * 5) / 4
            else:
                data_bits[i + 2] = (data_bits[i + 2] * 4) / 5
        samp_mag[16:ADSBDemod.MODES_LONG_BITS] = data_bits
        return samp_mag

    def execute(self, samples):
        # PREAMBLE STRUCTURE
        # Each sample has a length of 0.5 microseconds
        # Thus the total length of 16 samples
        #
        # 0   -----------------
        # 1   -
        # 2   ------------------
        # 3   --
        # 4   -
        # 5   --
        # 6   -
        # 7   ------------------
        # 8   --
        # 9   -------------------
        # 10  --
        # 11  -
        # 12  --
        # 13  -
        # 14  --
        # 15  -

        use_correction = False
        mag = calc_magnitude(samples)
        mag_cpy = []

        for i in range(len(samples) - MODES_FULL_LEN * 2):
            if not (mag[i] > mag[i + 1] and \
                 mag[i + 1] < mag[i + 2] and \
                 mag[i + 2] > mag[i + 3] and \
                 mag[i + 3] < mag[i] and \
                 mag[i + 4] < mag[i] and \
                 mag[i + 5] < mag[i] and \
                 mag[i + 6] < mag[i] and \
                 mag[i + 7] > mag[i + 8] and \
                 mag[i + 8] < mag[i + 9] and \
                 mag[i + 9] > mag[i + 6]):
                continue
            
            high = (mag[i] + mag[i + 2] + mag[i + 7] + mag[i + 9]) / 6

            if mag[i + 4] >= high or mag[i + 5] > high:
                continue

            if mag[i + 11] >= high or \
               mag[i + 12] >= high or \
               mag[i + 13] >= high or\
               mag[i + 14] >= high:
                continue

            if use_correction:
                mag_cpy = mag[i + ADSBDemod.MODES_PREAMBLE * 2 : ADSBDemod.MODES_LONG_MSG_BITS*2]
                if(i and detect_out_phase(mag_cpy)):
                    mag_cpy = correct_phase(mag_copy)
            
            bits = []

            for j in range(0, ADSBDemod.MODES_LONG_MSG_BITS, 2):
                low = mag_cpy[i + j]
                high = mag_cpy[i + j + 1]

                delta = abs(low - high)

                if j and delta < 256:
                    bits.append(bits[-1])
                elif low == high:
                    bits.append(2)
                elif low > high:
                    bits.append(1)
                else:
                    bits.append(0)

            print(bits)

