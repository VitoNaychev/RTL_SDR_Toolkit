# Filter pin configuration
#
# Pin 0 - DATA
# Pin 1 - CLK
# Pin 2 - ENser (Enable series capacitor)
# Pin 3 - ENinvL (Enable left inverter capacitor)
# Pin 4 - ENinvR (Enable right inverter capacitor)
# Pin 5 - ~ENres (Enable outer resonators)
# Pin 6 - ~ENmid (Enable middle resonator)
# Pin 7 - Vdd
# Pin 8 - GND
#
# Rapsberry Pi - Filter pin configration
#
# Pin 19 - DATA
# Pin 23 - CLK
# Pin 29 - ENser
# Pin 31 - ENinvL
# Pin 33 - ENinvR
# Pin 35 - ~ENres
# Pin 37 - ~ENmid
# Pin  1 - Vdd (3.3 V)
# Pin 39 - GND
#
# NCD 2100 Operation specification
# https://www.mouser.bg/datasheet/2/205/NCD2100-515357.pdf
#
# "By default the NCD2100 operates in Memory Mode so that in most end-user
#  applications the capacitance value corresponds to the calibration
#  information programmed in the memory. Whether shift register or memory
#  mode is in use is determined by the logical state at the CLK input."
#
# CLK = 1: Shift Register Mode    CLK = 0: Memory Mode
#
# Therefore while the filter is operating the CLK line sholud always be held
# high so that the value will be read from the Shift register instead from
# the non-volatile memory
#
# "Modifying the capacitance is easily accomplished by loading the 11 bit
#  control code into pin DA using the clock (CLK), with pin PV held low or
#  left open. When pin PV is open circuit, an internal pull down resistor
#  having a nominal value of 180k will satisfy the logic 0 requirement"
#
# When programming the NCD 2100 capacitors, their PV pins should be held low
# (~ENres and ~ENmid depending on which we want to program)
#
# "The NCD2100 utilizes a first-in first-out shift register so it is necessary
#  to ensure only 11 rising edges of theclock are applied to the device when
#  entering data.The least significant bit (LSB) of the serial data is the
#  first bit entered into the shift register. This bit is CHKand does not
#  affect the value of the capacitance. Assuch, bit CHK is a “Don’t Care” in
#  Shift Register Modeand may be set to either a logic 0 or a logic 1. When
#  the last bit is entered into the shift register, the CLK input must remain
#  at a logic 1 for the control datain the shift register to regulate the
#  capacitor value."
#
# Message structure
# +-----+----+----+----+----+----+----+----+----+----+----+
# | CHK | B1 | B2 | B3 | B4 | B5 | B1 | B2 | B3 | B1 | B2 |
# +-----+----+----+----+----+----+----+----+----+----+----+
#        [         CDAC3        ] [    CDAC2   ] [ CDAC1 ]
#
#
#
# PE64909 operation specification
# https://www.psemi.com/pdf/datasheets/pe64909ds.pdf
#
#

# import RPi.GPIO as GPIO
# import spidev

from filterdesign import FilterDesign


class FilterTuner:
    POLES = 3
    BANDWIDTH = 5e6
    L = [4e-9, 4e-9, 4e-9]

    ENser_PIN = 29
    ENinvL_PIN = 31
    ENinvR_PIN = 33
    ENres_PIN = 35
    ENmid_PIN = 37

    INVERTER_COMBS = {}

    def __init__(self):
        FilterTuner.populate_combinations()
        # FilterTuner.init_GPIOs()
        # self.spi = FilterTuner.init_SPI()
        self.spi = None
        self.filter_design = FilterDesign(FilterTuner.POLES,
                                          FilterTuner.BANDWIDTH,
                                          FilterTuner.L)

    def print_filter_values(calc_values, actual_values):
        resonator_calc = calc_values['C'][0]
        resonator_actual = actual_values['res']
        middle_calc = calc_values['C'][1]
        middle_actual = actual_values['mid']
        inverter_calc = calc_values['Ic'][0]
        inverter_actual = actual_values['inv']
        series_calc = calc_values['Cin']
        series_actual = actual_values['ser']
        print('VALUES\tCALC\t\tACTUAL')
        print('----------------------------------')
        print('RES:\t{:.3f} pF\t{:.3f} pF'.format(resonator_calc * 1e12,
                                                      resonator_actual * 1e12))
        print('MID:\t{:.3f} pF\t{:.3f} pF'.format(middle_calc * 1e12,
                                                  middle_actual * 1e12))
        print('INV:\t{:.3f} pF\t{:.3f} pF'.format(inverter_calc * 1e12,
                                                    inverter_actual * 1e12))
        print('SER:\t{:.3f} pF\t{:.3f} pF'.format(series_calc * 1e12,
                                                  series_actual * 1e12))

    def tune(self, center_freq):
        calc_values = self.filter_design.calculate(center_freq)
        # Because the filter is 3 pole 3 values are returned
        # the first and the last for the outter resonators
        # and the middle for the middle one
        resonator_values = calc_values['C']
        middle_value = resonator_values[1]
        outter_value = resonator_values[0]  # == resonator_value[2]
        # For a 3 pole filter there are only two inverters with
        # the same value, therefore its irrelevant which we take
        inverter_value = calc_values['Ic'][0]  # == calc_values['Ic'][1]
        # Same as for the inverter. Cin equals Cout
        series_value = calc_values['Cin']  # == calc_values['Cout']

        series_actual = FilterTuner.tune_series(series_value, self.spi)
        inverter_actual = FilterTuner.tune_inverter(inverter_value, self.spi)
        middle_actual = FilterTuner.tune_middle(middle_value, self.spi)
        resonator_actual = FilterTuner.tune_resonator(outter_value, self.spi)

        actual_values = {
                        'ser': series_actual,
                        'res': resonator_actual,
                        'mid': middle_actual,
                        'inv': inverter_actual
                        }

        FilterTuner.print_filter_values(calc_values, actual_values)

    def populate_combinations():
        PE64909_MIN = 0.6e-12    # 0.6 pF
        PE64909_STEP = 117e-15   # 117 fF

        for i in range(0b10000):
            for j in range(0b10000):
                l_val = PE64909_MIN + i * PE64909_STEP
                r_val = PE64909_MIN + j * PE64909_STEP
                inverter_val = (l_val * r_val) / (l_val + r_val)
                FilterTuner.INVERTER_COMBS[(i << 4) + j] = inverter_val

    def encode_NCD2100(value):
        NCD2100_MIN = 6.6e-12    # 6.6 pF
        CDAC1_STEP = 6.4e-12     # 6.4 pF
        CDAC2_STEP = 1.4e-12     # 1.4 pF
        CDAC3_STEP = 0.063e-12   # 0.063 pF ~ 63 fF

        CDAC1_REG = 0
        CDAC2_REG = 0
        CDAC3_REG = 0

        value -= NCD2100_MIN

        CDAC1_REG = int(value / CDAC1_STEP)
        if CDAC1_REG > 0b11:
            CDAC1_REG = 0b11
        value -= CDAC1_REG * CDAC1_STEP

        CDAC2_REG = int(value / CDAC2_STEP)
        if CDAC2_REG > 0b111:
            CDAC2_REG = 0b111
        value -= CDAC2_REG * CDAC2_STEP

        CDAC3_REG = int(value / CDAC3_STEP)
        if CDAC3_REG > 0b11111:
            CDAC3_REG = 0b11111
        value -= CDAC3_REG * CDAC3_STEP

        if value > CDAC3_STEP:
            print('NCD2100: Too high capacitence requested')
            return 0

        NCD2100_REG = ((CDAC1_REG << 9) +
                       (CDAC2_REG << 6) +
                       (CDAC3_REG << 1) + 1)

        # Although 11 bits must be send, spidev works only with
        # bytes, therefore we must shift the value of the register
        # 5 bits to the right, so the first 5 bits send are zeros
        # P.S. Bits might need to be flipped because of the
        # SPI transmission order
        byte_arr = []
        byte_arr.append((NCD2100_REG << 5) ^ 0xFF)
        byte_arr.append((NCD2100_REG >> 3) ^ 0xFF)

        ncd2100_value = (CDAC1_REG * CDAC1_STEP +
                         CDAC2_REG * CDAC2_STEP +
                         CDAC3_REG * CDAC3_STEP) + NCD2100_MIN

        return byte_arr, ncd2100_value

    def encode_inverter(value):
        PE64909_MIN = 0.6e-12    # 0.6 pF
        PE64909_MAX = 2.35e-12

        INV_MIN = (PE64909_MIN * PE64909_MIN) / (2 * PE64909_MIN)   # 0.3 pF
        INV_MAX = (PE64909_MAX * PE64909_MAX) / (2 * PE64909_MAX)  # 1.175 pF

        if INV_MIN > value or value > INV_MAX:
            print('Inverter: Too high capacitence requested')
            return 0

        code = 0
        min_diff = 1

        for i in range(0b100000000):
            diff = value - FilterTuner.INVERTER_COMBS[i]
            if diff < min_diff and diff >= 0:
                code = i
                min_diff = value - FilterTuner.INVERTER_COMBS[i]

        invL_code = code & 0x0F   # Get first four bits from code
        invR_code = code >> 4     # Get last four bits from code

        return invL_code ^ 0xFF, invR_code ^ 0xFF, FilterTuner.INVERTER_COMBS[code]

    def encode_PE64102(value):
        PE64102_MIN = 1.88e-12   # 1.88 pF
        PE64102_STEP = 391e-15   # 391 fF

        value -= PE64102_MIN
        PE64102_REG = int(value / PE64102_STEP)

        if PE64102_REG > 0b11111:
            print('PE64102: Too high capacitence requested')
            return 0

        return PE64102_REG ^ 0xFF, (PE64102_REG * PE64102_STEP + PE64102_MIN)

    def transmit_NCD2100(spi, cs_pin, byte_arr):
        # NCD2100 requires LSB order
        spi.lsbfirst = True             # Set LSB order

        # Set the Chip Select pin
        GPIO.output(cs_pin, False)

        spidev.writebytes2(byte_arr)

        GPIO.output(cs_pin, True)

    def transmit_PE64xxx(spi, cs_pin, byte):
        # The PE64xxx series require MSB order
        spi.lsbfirst = False            # Set MSB order

        # Set the Chip Select pin
        GPIO.output(cs_pin, True)

        spidev.writebytes2(byte)

        GPIO.output(cs_pin, False)

    def tune_inverter(req_value, spi):
        # Get the codes for the left and right digital capacitor
        # as well as the actuall inverter value
        invL_code, invR_code, inverter_actual = FilterTuner.encode_inverter(req_value)

        # transmit_PE64xxx(spi, FilterTuenr.ENinvL_PIN, invL_code)
        # transmit_PE64xxx(spi, FilterTuner.ENinvR_PIN, invR_code)
        return inverter_actual

    def tune_series(req_value, spi):
        # Values of paralel and series capacitor to
        # the digital capacitor
        CAP_PAR = 0.25e-12  # 0.25 pF
        CAP_SER = 7.5e-12   # 7.5  pF

        # First calculate the value of PE64102 because it's
        # connected in series with other capacitors
        pe64102_val = abs((req_value * CAP_SER) / (req_value - CAP_SER))

        # Subtract the parallel capacitors value
        pe64102_val -= CAP_PAR

        # The function returns the code to be transmited and the
        # actual value calculated with that code
        pe64102_code, pe64102_actual = FilterTuner.encode_PE64102(pe64102_val)

        # Calculate the actual value of the series capacitor
        pe64102_actual += CAP_PAR
        series_actual = (pe64102_actual * CAP_SER) / (pe64102_actual + CAP_SER)

        # transmit_PE64xxx(spi, FilterTuner.ENser_PIN, pe64102_code)
        return series_actual

    def tune_resonator(req_value, spi):
        # Parallel capacitor value of the outter resonators
        RES_PAR = 16.8e-12  # 16.8 pF

        # Get the NCD2100 code as well as the actual
        # NCD2100 value
        ncd2100_code, ncd2100_actual = FilterTuner.encode_NCD2100(req_value - RES_PAR)

        # Calculate the outter resonators value
        resonator_actual = ncd2100_actual + RES_PAR

        # transmit_NCD2100(spi, FilterTuner.ENres_PIN, ncd2100_code)
        return resonator_actual

    def tune_middle(req_value, spi):
        # Parallel capacitor value of the middle resonators
        MID_PAR = 18e-12    # 18 pF

        # Get the NCD2100 code as well as the actual
        # NCD2100 value
        ncd2100_code, ncd2100_value = FilterTuner.encode_NCD2100(req_value - MID_PAR)

        # Calculate the middle resonator value
        middle_actual = ncd2100_value + MID_PAR

        # transmit_NCD2100(spi, FilterTuner.ENmid_PIN, ncd2100_code)
        return middle_actual

    def init_GPIOs():
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(FilterTuner.ENser_PIN, GPIO.OUT)
        GPIO.output(FilterTuner.ENser_PIN, False)
        GPIO.setup(FilterTuner.ENinvL_PIN, GPIO.OUT)
        GPIO.output(FilterTuner.ENinvL_PIN, False)
        GPIO.setup(FilterTuner.ENinvR_PIN, GPIO.OUT)
        GPIO.output(FilterTuner.ENinvR_PIN, False)
        GPIO.setup(FilterTuner.ENres_PIN, GPIO.OUT)
        GPIO.output(FilterTuner.ENres_PIN, True)
        GPIO.setup(FilterTuner.ENmid_PIN, GPIO.OUT)
        GPIO.output(FilterTuner.ENmid_PIN, True)

    def init_SPI(self):
        spi = spidev.SpiDev()
        # Might need spi.open(0, 0) here
        spi.no_cs = True          # Disable use of the chip select
        spi.lsbfirst = True       # Set LSB order
        spi.maxspeedhz = 100e3    # NCD2100 max speed is 120kHz

        return spi
