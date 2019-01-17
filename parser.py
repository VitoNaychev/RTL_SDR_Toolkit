import argparse
from rtlsdr import RtlSdr

parser = argparse.ArgumentParser(description="A toolkit for the RTL-SDR")
group = parser.add_mutually_exclusive_group()
group.add_argument("--temp_demod", action="store_true", help="Listen to temperature sensor")
group.add_argument("--fm_demod", action="store_true", help="Listen to radio station")
group.add_argument("--fft_sink", action="store_true", help="Start FFT sink")

parser.add_argument("-c", "--center", type=int, help="Center frequnecy")
parser.add_argument("-r", "--rate", type=int, help="Sampling rate")
parser.add_argument("-g", "--gain", help="Set SDR gain")
parser.add_argument("-f", "--file", help="Save data to file")
parser.add_argument("-v", "--verbose", help="Print data to standard output")

args = parser.parse_args()
print(args.center)

print(RtlSdr.DEFAULT_READ_SIZE)
