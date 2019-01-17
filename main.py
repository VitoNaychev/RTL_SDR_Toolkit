import asyncio
import numpy as np
import scipy.signal as signal
import pyaudio
from rtlsdr import RtlSdr
from tempdemod import TempDemod
from fmdemod import FmDemod
from recordsamp import RecordSamp
from sdrtask import SDRTask
import argparse

def init_parser(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--temp_demod", action="store_true", help="Listen to temperature sensor")
    group.add_argument("--fm_demod", action="store_true", help="Listen to radio station")
    group.add_argument("--fft_sink", action="store_true", help="Start FFT sink")

    parser.add_argument("-c", "--center", type=int, help="Center frequnecy")
    parser.add_argument("-r", "--rate", type=int, help="Sampling rate")
    parser.add_argument("-g", "--gain", type=int, help="Set SDR gain")
    parser.add_argument("-f", "--file", type=int, help="Save data to file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print data to standard output")

async def streaming(sdr_task, center_freq, samp_rate, sdr_gain, sdr_samp_size):
    sdr = RtlSdr()
    sdr.center_freq = center_freq
    sdr.sample_rate = samp_rate
    sdr.gain = sdr_gain

    async for samples in sdr.stream(sdr_samp_size):
        sdr_task.execute(samples)

    await sdr.stop()

    sdr.close()


parser = argparse.ArgumentParser(description="A toolkit for the RTL-SDR")
init_parser(parser)
args = parser.parse_args()

center_freq = args.center
samp_rate = args.rate
out_file = args.file
sdr_gain = args.gain
verbose = args.verbose

sdr_samp_size = RtlSdr.DEFAULT_READ_SIZE

sdr_task = None

if args.temp_demod:
    if not center_freq:
        center_freq = 433.7e6
    if not samp_rate:
        samp_rate = 1e6
    if not out_file:
        out_file = ''
    if not sdr_gain:
        sdr_gain = 1.4
    sdr_task = TempDemod(samp_rate, verbose, out_file)
elif args.fm_demod:
    if not center_freq:
        center_freq = 98.3e6
    if not samp_rate:
        samp_rate = 1e6
    if not out_file:
        out_file = ''
    if not sdr_gain:
        sdr_gain = 'auto'
    sdr_task = FmDemod(samp_rate, verbose, out_file)
                         
                         
loop = asyncio.get_event_loop()
loop.run_until_complete(streaming(sdr_task, center_freq, samp_rate, sdr_gain, sdr_samp_size))
loop.close()
