import argparse

parser = argparse.ArgumentParser(description="A toolkit for the RTL-SDR")
group = parser.add_mutually_exclusive_group()
group.add_argument("--temp_demod", action="store_true", help="Listen to temperature sensor")
group.add_argument("--fm_demod", action="store_true", help="Listen to radio station")
group.add_argument("--fft_sink", action="store_true", help="Start FFT sink")

parser.add_argument("-c", "--center", type=int, help="Center frequnecy")
parser.add_argument("-r", "--rate", type=int, help="Sampling rate")
parser.add_argument("-f", "--file", help="Save data to file")

args = parser.parse_args()
