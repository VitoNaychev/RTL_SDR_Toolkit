#!/usr/bin/python3

import asyncio
import numpy as np
import scipy.signal as signal
import pyaudio
import argparse
import sys

from rtlsdr import RtlSdr

from tempdemod import TempDemod
from fmdemod import FmDemod
from recordsamp import RecordSamp
from sdrtask import SDRTask
from rawiq import RawIQ
from fftsink import FftSink
from scanfm import ScanFm
from adsbdemod import AdsbDemod
from adsbdemod import AdsbDemod
from transmittask import TransmitTask
from jammertask import JammerTask
from replaytask import ReplayTask


def init_parser(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--temp_demod", action="store_true", help="Listen to temperature sensor")
    group.add_argument("--fm_demod", action="store_true", help="Listen to radio station")
    group.add_argument("--raw_iq", action="store_true", help="Listen to Raw IQ data")
    group.add_argument("--adsb_demod", action="store_true", help="Listen ADS-B data sent from airplanes")
    group.add_argument("--fft_sink", action="store_true", help="Start FFT sink")
    group.add_argument("--scan_fm", action="store_true", help="Scan FM radio spectrum")

    parser.add_argument("-c", "--center", type=float, help="Center frequnecy")
    parser.add_argument("-r", "--rate", type=float, help="Sampling rate")
    parser.add_argument("-g", "--gain", type=float, help="Set SDR gain")
    parser.add_argument("-f", "--file", help="Save data to file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print data to standard output")
    parser.add_argument("--on_active", action="store_true", help='''Record samples only on activity
                                                                  - reffers to Raw IQ recording''')
    parser.add_argument("--diff", type=int, help='''Set difference that qualifies as
                                                             activity''')
    parser.add_argument("--limit", type=int, help="Set lower limit by Y axis for FFT Sink")
    parser.add_argument("--persistence", action="store_true", help="Display highest values over time")
    parser.add_argument("--cmd", action="store_true", help="Choose CMD mode for the FFT Sink")


def check_args(args):
    # Check if all the arguments are in the bounds
    # for the current SDR. Use the defined enum 
    # to determine the SDR and hardcode the values 
    # for it
    pass

def init_rtl_task(args):
    sdr_task = None

    samp_rate = args.rate
    center_freq = args.center
    gain = args.gain
    samp_size = RtlSdr.DEFAULT_READ_SIZE

    out_file = args.file
    verbose = args.verbose

    if not out_file:
        out_file = ''

    if args.temp_demod:
        sdr_task = TempDemod(samp_rate, verbose, out_file)
    elif args.fm_demod:
        sdr_task = FmDemod(samp_rate, center_freq, gain, samp_size, verbose, out_file)
    elif args.adsb_demod:
        sdr_task = AdsbDemod(samp_rate, center_freq, gain, samp_size, verbose, out_file)
    elif args.fft_sink:
        limit = args.limit
        persis = args.persistence
        cmd = args.cmd
        sdr_task = FftSink(samp_rate, center_freq, gain, samp_size, cmd, limit, persis)
    elif args.raw_iq:
        diff = args.diff
        sdr_task = RawIQ(samp_rate, verbose, out_file, diff)
    elif args.scan_fm:
        sdr_task = ScanFm(samp_rate, center_freq, gain, samp_size)

    return sdr_task


async def streaming(sdr_task, time):
    await sdr_task.run(time)

parser = argparse.ArgumentParser(description="A toolkit for the RTL-SDR")
init_parser(parser)
args = parser.parse_args()

time = 0

sdr_task = init_rtl_task(args)

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(streaming(sdr_task, time))
except KeyboardInterrupt:
#    sdr_task._sdr.close()
    loop.stop()

sys.exit()
loop.close()
