import numpy as np
import pyModeS as pms
import pprint

from rtltoolkit.basetasks.demodtask import DemodTask


class AdsbDemod(DemodTask):
    defaults = {
            'samp_rate': 2e6,
            'center_freq': 1090e6,
            'gain': 44.5,
            'samp_size': 2**18
            }

    MODES_PREAMBLE = 8          # microseconds
    MODES_LONG_MSG_BITS = 112
    MODES_SHORT_MSG_BITS = 56
    MODES_FULL_LEN = MODES_PREAMBLE + MODES_LONG_MSG_BITS

    def __init__(self, samp_rate, center_freq, gain, samp_size,
                 verbose=True, file_name=''):
        super().__init__(samp_rate, center_freq, gain, samp_size,
                         verbose, file_name)
        self.prev_msg = None

    def calc_magnitude(samples):
        samples *= 128
        samp_mag = np.around(np.absolute(samples))
        return samp_mag

    def detect_out_phase(mag):
        if mag[3] > mag[2] / 3:
            return 1
        if mag[10] > mag[9] / 3:
            return 1
        if mag[6] > mag[7] / 3:
            return 1
        # if samp_mag[-1] > samp_mag[1] / 3 return 1
        return 0

    def correct_phase(data_mag):
        for i in range(0, AdsbDemod.MODES_LONG_MSG_BITS*2 - 2, 2):
            if(data_mag[i] > data_mag[i + 1]):
                data_mag[i + 2] = (data_mag[i + 2] * 5) / 4
            else:
                data_mag[i + 2] = (data_mag[i + 2] * 4) / 5

        return data_mag

    def check_preamble(mag):
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
        if not (mag[0] > mag[1] and
                mag[1] < mag[2] and
                mag[2] > mag[3] and
                mag[3] < mag[0] and
                mag[4] < mag[0] and
                mag[5] < mag[0] and
                mag[6] < mag[0] and
                mag[7] > mag[8] and
                mag[8] < mag[9] and
                mag[9] > mag[6]):
            return 0

        high = (mag[0] + mag[2] + mag[7] + mag[9]) / 6

        # Check if the 4th and 5th bit of the preamble are lower than the
        # average high. Those two bits are the furthest from two high states
        # which means that that there should be no energy leakege from previous
        # high bits. If those two have a higher level than the average it means
        # that even after applying correction we won't get a valid message
        if mag[4] >= high or mag[5] >= high:
            return 0

        # Same as for the 4th and 5th
        if mag[11] >= high or \
           mag[12] >= high or \
           mag[13] >= high or \
           mag[14] >= high:
            return 0

        return 1

    def pack_into_bits(mag):
        data_bits = []
        for j in range(0, AdsbDemod.MODES_LONG_MSG_BITS * 2, 2):
            low = mag[j]
            high = mag[j + 1]

            if low == high:
                data_bits.append(2)
            elif low > high:
                data_bits.append(1)
            else:
                data_bits.append(0)

        return data_bits

    def pack_into_bytes(data_bits):
        data_bytes = []
        for j in range(0, AdsbDemod.MODES_LONG_MSG_BITS, 8):
            cur_byte = 0
            cur_byte |= data_bits[j + 0] << 7
            cur_byte |= data_bits[j + 1] << 6
            cur_byte |= data_bits[j + 2] << 5
            cur_byte |= data_bits[j + 3] << 4
            cur_byte |= data_bits[j + 4] << 3
            cur_byte |= data_bits[j + 5] << 2
            cur_byte |= data_bits[j + 6] << 1
            cur_byte |= data_bits[j + 7] << 0

            if cur_byte > 256 or cur_byte < 0:
                cur_byte = 0

            data_bytes.append(cur_byte)

        return data_bytes

    def dump_magnitude_bar(mag, index):

        bar = '[{:0>3}] |'.format(index)
        set = [' ', '.', '-', 'o']
        div = int(mag) // 256 // 4
        rem = int(mag) // 256 % 4
        bar += '{:<10}{:>30}'.format(('O' * div + set[rem]), int(mag))

        return bar + '\n'

    def dump_magnitude_vect(mag_arr):
        vector = ''
        for i in range(AdsbDemod.MODES_FULL_LEN + 5):
            bar = AdsbDemod.dump_magnitude_bar(mag_arr[i], i - 5)
            vector += bar

        return vector

    def is_valid(msg):
        return int(pms.crc(msg)) == 0

    def return_msg_len(msg_type):
        if msg_type == 16 or msg_type == 17 or \
           msg_type == 19 or msg_type == 20 or \
           msg_type == 21:
            return AdsbDemod.MODES_LONG_MSG_BITS
        else:
            return AdsbDemod.MODES_SHORT_MSG_BITS

    def decode_msg_type(msg):
        return pms.df(msg)

    def decode_msg_icao(msg):
        return pms.icao(msg)

    def decode_adsb_id(msg):
        id_fields = dict()
        id_fields['CS'] = pms.adsb.callsign(msg)
        id_fields['CAT'] = pms.adsb.category(msg)

        return id_fields

    def decode_adsb_pos(self, msg):
        pos_fields = dict()
        if self.prev_msg is not None \
           and pms.adsb.oe_flag(msg) != pms.adsb.oe_flag(self.prev_msg):

            lat, lon = 0, 0
            if pms.adsb.oe_flag(msg) == 0:
                lat, lon = pms.adsb.airborne_position(msg, self.prev_msg, 1, 0)
            else:
                lat, lon = pms.adsb.airborne_position(self.prev_msg, msg, 0, 1)

            pos_fields['LAT'] = lat
            pos_fields['LON'] = lon
        else:
            self.prev_msg = msg

        pos_fields['ALT'] = pms.adsb.altitude(msg)

        return pos_fields

    def decode_adsb_velocity(msg):
        velocity_fields = dict()
        spd, hdg, rocd, tag = pms.adsb.velocity(msg)
        velocity_fields['SPEED'] = spd
        velocity_fields['HEADING'] = hdg
        velocity_fields['VERTICAL'] = rocd
        velocity_fields['TAG'] = tag

        return velocity_fields

    def decode_adsb_ver(msg):
        op_fields = dict()
        op_fields['VER'] = pms.adsb.version(msg)

        return op_fields

    def decode(self, msg):
        msg_fields = dict()
        msg_fields['HEX'] = '0x' + msg
        msg_fields['DF'] = AdsbDemod.decode_msg_type(msg)
        msg_fields['ICAO'] = AdsbDemod.decode_msg_icao(msg)

        if msg_fields['DF'] == 17:
            adsb_fields = dict()
            adsb_fields['TC'] = pms.typecode(msg)

            if 1 <= adsb_fields['TC'] <= 4:
                adsb_fields['ID'] = AdsbDemod.decode_adsb_id(msg)

            if 9 <= adsb_fields['TC'] <= 18:
                adsb_fields['POS'] = AdsbDemod.decode_adsb_pos(self, msg)

            if adsb_fields['TC'] == 19:
                adsb_fields['VEL'] = AdsbDemod.decode_adsb_velocity(msg)

            if adsb_fields['TC'] == 31:
                adsb_fields['OP-STATUS'] = AdsbDemod.decode_adsb_ver(msg)

            msg_fields['ADS-B'] = adsb_fields

        return msg_fields

    def execute(self, samples):
        mag = AdsbDemod.calc_magnitude(samples)
        mag_cpy = []

        # Cycle through array of samples searching for a valid message
        # structure within it
        for i in range(len(mag) - AdsbDemod.MODES_FULL_LEN * 2):
            # All of the MODES lengths (defined in the begining of the class)
            # are multiplied by two, because of the encoding of the data, unitl
            # the data is converted into bits.
            # The modulation is PPM(Pulse Position Modulation) and each
            # pulse accompanied by and idle period represents a bit. Therefore
            # if one bit is with a length of 1 ms each of the two pulses
            # representing it will have a length of 0.5 ms. Because of this the
            # minimal sampling rate needed to catch those short pulses is 2 MHz
            # (T = 1/(2 * 10^6) = 0.5 ms)
            #        _____ _____            _____       _____
            #       |     |     |          |     |     |     |
            #       |     |     |          |     |     |     |
            #   OFF | ON  | ON  | OFF  OFF | ON  |     |     |
            #  _____|     |     |__________|     |_____|     |
            #
            # |<--->|<--->|
            # 0.5ms 0.5ms
            #
            # A logical one is denoted by an ON followed by and OFF and a
            # logical zero by an OFF followed by an ON

            # Check for a valid preamble denoting an incoming message
            # Keep in mind that having 2 MS/s means that alot of the noice will
            # be mistaken for a valid preamble, which is the reason for the
            # later tests of the message
            if not AdsbDemod.check_preamble(mag[i:
                                                i+AdsbDemod.MODES_PREAMBLE*2]):
                continue

            # Due to the fact that the sample period is equal to the length
            # of the pulses It is unlikely that the pulses will be totaly
            # synchronised with the sampling process. Therefore small
            # correction can be made to fix this. The main problem is that
            # if the pulses are not sampled properly they may "leak" in two
            # adjecent ones. Therefore phase correction is applied if we
            # detect that the difference between the low(OFF) and high(ON)
            # levels is too small which usually denotes incorrect(out of phase)
            # sampling. In the phase correction we make the high levels a bit
            # higher and the low ones a bit lower

            data_mag = mag[i + AdsbDemod.MODES_PREAMBLE * 2:
                           i + AdsbDemod.MODES_FULL_LEN * 2]
            mag_cpy = list(data_mag)

            if(i and AdsbDemod.detect_out_phase(mag_cpy)):
                mag_cpy = AdsbDemod.correct_phase(mag_cpy)

            data_bits = AdsbDemod.pack_into_bits(mag_cpy)
            data_bytes = AdsbDemod.pack_into_bytes(data_bits)

            # The downlink format is contained within the first 5 bits of the
            # ADS-B message structure. With it we can determine the length of
            # the message
            # +--------+--------+-----------+---------------------+---------+
            # |  DF 5  |  ** 3  |  ICAO 24  |       DATA 56       |  PI 24  |
            # +--------+--------+-----------+---------------------+---------+

            msg_type = data_bytes[0] >> 3
            msg_len = AdsbDemod.return_msg_len(msg_type) // 8

            delta = 0
            for j in range(0, msg_len * 8 * 2, 2):
                delta += abs(data_mag[j] -
                             data_mag[j + 1])

            delta /= msg_len * 4

            if delta < 13 * 255:
                continue

            data_bytes = data_bytes[:msg_len]

            msg = bytes(data_bytes).hex()

            if AdsbDemod.is_valid(msg):
                msg_fields = self.decode(msg)
                pprint.pprint(msg_fields)
                print('-' * 60)

# print(AdsbDemod.dump_magnitude_vect(mag[i - 5:i+AdsbDemod.MODES_FULL_LEN]))
