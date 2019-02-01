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
import argparse

temp_default = {
        'center_freq': 433.7e6
        'samp_rate': 1e6
        'gain': 1.4
        }

fm_default = {
        'center_freq': 98.3e6
        'samp_rate': 1e6
        'gain': 'auto'
        }

raw_default = {
        'center_freq': 1090e6
        'samp_rate': 2e6
        'gain': 44.5
        }

adsb_default = {
        'center_freq': 1090e6
        'samp_rate': 2e6
        'gain': 44.5
        }

def init_parser(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--temp_demod", action="store_true", help="Listen to temperature sensor")
    group.add_argument("--fm_demod", action="store_true", help="Listen to radio station")
    group.add_argument("--raw_iq", action="store_true", help="Listen to Raw IQ data")
    group.add_argument("--adsb", action="store_true", help="Listen ADS-B data sent from airplanes")
    group.add_argument("--fft_sink", action="store_true", help="Start FFT sink")

    parser.add_argument("-c", "--center", type=int, help="Center frequnecy")
    parser.add_argument("-r", "--rate", type=int, help="Sampling rate")
    parser.add_argument("-g", "--gain", type=float, help="Set SDR gain")
    parser.add_argument("-f", "--file", help="Save data to file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print data to standard output")
    parser.add_argument("--on_active", action="store_true", help='''Record samples only on activity
                                                                  - reffers to Raw IQ recording''')
    parser.add_argument("--diff", type=int, help='''Set difference that qualifies as
                                                             activity''')

def init_task(args):
    center_freq = args.center
    samp_rate = 2e6
    out_file = args.file
    sdr_gain = args.gain
    verbose = args.verbose
    
    # sdr_samp_size = RtlSdr.DEFAULT_READ_SIZE
    sdr_samp_size = 2**18
    
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
    elif args.raw_iq:
        if not center_freq:
            center_freq = 1090e6
        if not samp_rate:
            samp_rate = 1e6
        if not out_file:
            out_file = ''
        if not sdr_gain:
            sdr_gain = 44.5
        if args.on_active:
            on_active = True
        if args.diff:
            active_diff = args.diff
        sdr_task = RawIQ(samp_rate, verbose, out_file, on_active, active_diff)
                         

def initTempTask():
    temp_task = TempDemod(samp_rate, verbose, out_file)
    return temp_task

def initFmTask():
    fm_task = FmDemod(samp_rate, verbose, out_file)
    return fm_task

def initADSBTask():
    adsb_task = ADSBDemod(samp_rate, verbose, out_file)
    return adsb_task

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
samp_rate = 2e6
out_file = args.file
sdr_gain = args.gain
verbose = args.verbose

# sdr_samp_size = RtlSdr.DEFAULT_READ_SIZE
sdr_samp_size = 2**18

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
elif args.raw_iq:
    if not center_freq:
        center_freq = 1090e6
    if not samp_rate:
        samp_rate = 1e6
    if not out_file:
        out_file = ''
    if not sdr_gain:
        sdr_gain = 44.5
    if args.on_active:
        on_active = True
    if args.diff:
        active_diff = args.diff
    sdr_task = RawIQ(samp_rate, verbose, out_file, on_active, active_diff)
                         
                         
loop = asyncio.get_event_loop()
loop.run_until_complete(streaming(sdr_task, center_freq, samp_rate, sdr_gain, sdr_samp_size))
loop.close()
