#!/usr/bin/python3

import asyncio
import numpy as np
import scipy.signal as signal
import pyaudio
from rtlsdr import RtlSdr
from tempdemod import TempDemod
from fmdemod import FmDemod
from recordsamp import RecordSamp
from sdrtask import SDRTask
from rawiq import RawIQ
from fftsink import FftSink
from scanfm import ScanFm
import argparse

temp_default = {
        'center_freq': 433.7e6,
        'samp_rate': 1e6,
        'gain': 1.4
        }

fm_default = {
        'center_freq': 98.3e6,
        'samp_rate': 1e6,
        'gain': 'auto'
        }

scan_fm_default = {
        'center_freq': 87.5e6,
        #'center_freq': 98.5e6,
        'samp_rate': 2e6,
        'gain': 'auto'
        }
adsb_defult = {
        'center_freq': 1090e6,
        'samp_rate': 2e6,
        'gain': 44.5
        }

def init_parser(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--temp_demod", action="store_true", help="Listen to temperature sensor")
    group.add_argument("--fm_demod", action="store_true", help="Listen to radio station")
    group.add_argument("--raw_iq", action="store_true", help="Listen to Raw IQ data")
    group.add_argument("--adsb_demod", action="store_true", help="Listen ADS-B data sent from airplanes")
    group.add_argument("--fft_sink", action="store_true", help="Start FFT sink")
    group.add_argument("--scan_fm", action="store_true", help="Scan FM radio spectrum")

    parser.add_argument("-c", "--center", type=int, help="Center frequnecy")
    parser.add_argument("-r", "--rate", type=int, help="Sampling rate")
    parser.add_argument("-g", "--gain", type=float, help="Set SDR gain")
    parser.add_argument("-f", "--file", help="Save data to file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print data to standard output")
    parser.add_argument("--on_active", action="store_true", help='''Record samples only on activity
                                                                  - reffers to Raw IQ recording''')
    parser.add_argument("--diff", type=int, help='''Set difference that qualifies as
                                                             activity''')
    parser.add_argument("--limit", type=int, help="Set lower limit by Y axis for FFT Sink")
    parser.add_argument("--persistence", action="store_true", help="Display highest values over time")

def init_rtl_task(args):
    sdr_task = None
    default = None
    sdr = RtlSdr()
    
    center_freq = args.center
    samp_rate = args.rate
    out_file = args.file
    sdr_gain = args.gain
    verbose = args.verbose

    if args.temp_demod:
        default = temp_default
    elif args.fm_demod:
        default = fm_default
    elif args.adsb_demod:
        default = adsb_default
    elif args.scan_fm:
        default = scan_fm_default
    
    if not center_freq:
        center_freq = default['center_freq']
    if not samp_rate:
        samp_rate = default['samp_rate']
    if not sdr_gain:
        sdr_gain = default['gain']
    if not out_file:
        out_file = ''

    if args.temp_demod:
        sdr_task = TempDemod(samp_rate, verbose, out_file)
    elif args.fm_demod:
        sdr_task = FmDemod(samp_rate, verbose, out_file)
    elif args.adsb_demod:
        sdr_task = AdsbDemod(samp_rate, verbose, out_file)
    elif args.fft_sink:
        lower_lim = args.limit
        persis = args.persistence
        if not lower_lim:
            sdr_task = FftSink(samp_rate, persis = persis)
        else:
            sdr_task = FftSink(samp_rate, lower_lim, persis)
    elif args.raw_iq:
        on_active = args.on_active
        diff = args.diff
        if not diff:
            diff = 0
        sdr_task = RawIQ(samp_rate, verbose, out_file, on_active, diff)
    elif args.scan_fm:
        sdr_task = ScanFm(samp_rate)

    sdr.center_freq = center_freq
    sdr.sample_rate = samp_rate
    sdr.gain = sdr_gain

    return sdr, sdr_task


async def streaming(sdr, sdr_task, sdr_samp_size):
    await sdr_task.run(sdr)

    #await sdr.stop()

    sdr.close()


parser = argparse.ArgumentParser(description="A toolkit for the RTL-SDR")
init_parser(parser)
args = parser.parse_args()

# sdr_samp_size = RtlSdr.DEFAULT_READ_SIZE
sdr_samp_size = 2**14

sdr, sdr_task = init_rtl_task(args)
                         
loop = asyncio.get_event_loop()
loop.run_until_complete(streaming(sdr, sdr_task, sdr_samp_size))
loop.close()
