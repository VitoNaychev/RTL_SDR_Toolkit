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

import RPi.GPIO as GPIO
import spidev

ENser_PIN = 29
ENinvL_PIN = 31
ENinvR_PIN = 33
ENres_PIN = 35
ENmid_PIN = 37

NCD2100_MIN = 6.6e-12    # 6.6 pF
CDAC1_STEP = 6.4e-12     # 6.4 pF
CDAC2_STEP = 1.4e-12     # 1.4 pF
CDAC3_STEP = 0.063e-12   # 0.063 pF ~ 63 fF

PE64909_MIN = 0.6e-12    # 0.6 pF
PE64909_STEP = 117e-15   # 117 fF

PE64102_MIN = 1.88e-12   # 1.88 pF
PE64102_STEP = 391e-15   # 391 fF

INVERTER_COMBS = {}


def populate_combinations():
    for i in range(0b10000):
        for j in range(0b10000):
            l_val = PE64909_MIN + i * PE64909_STEP
            r_val = PE64909_MIN + j * PE64909_STEP
            inverter_val = (l_val * r_val) / (l_val + r_val)
            INVERTER_COMBS[(i << 4) + j] = inverter_val


def encode_NCD2100(value):
    CDAC1_REG = 0
    CDAC2_REG = 0
    CDAC3_REG = 0

    CDAC1_REG = int(value / CDAC1_STEP)

    if CDAC1_REG > 0b11:
        print('NCD2100: Too high capacitence requested')
        return 0

    value -= CDAC1_REG * CDAC1_STEP
    CDAC2_REG = int(value / CDAC2_STEP)

    if CDAC2_REG > 0b111:
        print('NCD2100: Too high capacitence requested')
        return 0

    value -= CDAC2_REG * CDAC2_STEP
    CDAC3_REG = int(value / CDAC3_STEP)

    if CDAC3_REG > 0b11111:
        print('NCD2100: Too high capacitence requested')
        return 0

    NCD2100_REG = CDAC1_REG << 9 + CDAC2_REG << 6 + CDAC3_REG << 1 + 1

    # Although 11 bits must be send, spidev works only with
    # bytes, therefore we must shift the value of the register
    # 5 bits to the right, so the first 5 bits send are zeros
    # P.S. Bits might need to be flipped because of the
    # SPI transmission order
    print('NCD2100:', bin(NCD2100_REG))

    byte_arr = []
    byte_arr.append((NCD2100_REG << 5) & 0xFF)
    byte_arr.append((NCD2100_REG >> 3) & 0xFF)

    return byte_arr


def transmit_NCD2100(spi, cs_pin, byte_arr):
    spi.lsbfirst = True             # Set LSB order
    GPIO.output(cs_pin, False)

    spidev.writebytes2(byte_arr)

    GPIO.output(cs_pin, True)


def encode_PE64909(value):
    PE64909_REG = int(value / PE64909_STEP)

    if PE64909_REG > 0b1111:
        print('PE64909: Too high capacitence requested')

    return PE64909_REG & 0xFF


def encode_PE64102(value):
    PE64102_REG = int(value / PE64102_STEP)

    if PE64102_REG > 0b11111:
        print('PE64102: Too high capacitence requested')

    return PE64102_REG & 0xFF


def transmit_PE64xxx(spi, cs_pin, byte):
    spi.lsbfirst = False            # Set MSB order
    GPIO.output(cs_pin, True)

    spidev.writebytes2(byte)

    GPIO.output(cs_pin, False)


def tune_inverter(value):
    if 0.3e-12 > value or value > 0.969e-12:
        print('Inverter: Too high capacitence requested')
        return 0

    code = 0
    min_diff = 1

    for i in range(0b100000000):
        diff = value - INVERTER_COMBS[i]
        if diff < min_diff and diff >= 0:
            code = i
            min_diff = value - INVERTER_COMBS[i]

    return code

def init_GPIOs():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(ENser_PIN, GPIO.OUT)
    GPIO.output(ENser_PIN, False)
    GPIO.setup(ENinvL_PIN, GPIO.OUT)
    GPIO.output(ENinvL_PIN, False)
    GPIO.setup(ENinvR_PIN, GPIO.OUT)
    GPIO.output(ENinvR_PIN, False)
    GPIO.setup(ENres_PIN, GPIO.OUT)
    GPIO.output(ENres_PIN, True)
    GPIO.setup(ENmid_PIN, GPIO.OUT)
    GPIO.output(ENmid_PIN, True)


def init_SPI():
    spi = spidev.SpiDev()
    # Might need spi.open(0, 0) here
    spi.no_cs = True          # Disable use of the chip select
    spi.lsbfirst = True       # Set LSB order
    spi.maxspeedhz = 100e3    # NCD2100 max speed is 120kHz
