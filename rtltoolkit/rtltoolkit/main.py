#!/usr/bin/python3.5

import sys
import argparse

from rtlsdr import RtlSdr

from rtltoolkit.demodtasks.tempdemod import TempDemod
from rtltoolkit.demodtasks.fmdemod import FmDemod
from rtltoolkit.demodtasks.adsbdemod import AdsbDemod
from rtltoolkit.recordtasks.rawiq import RawIQ
from rtltoolkit.displaytasks.fftsink import FftSink
from rtltoolkit.displaytasks.scanfm import ScanFm
from rtltoolkit.transmittasks.jammertask import JammerTask
from rtltoolkit.transmittasks.fmmodulate import FmModulate
from rtltoolkit.transmittasks.tempmodulate import TempModulate


def init_parser(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--temp",
                       action="store_true",
                       help="Listen to temperature sensor")
    group.add_argument("--fm-radio",
                       action="store_true",
                       help="Listen to radio station")
    group.add_argument("--raw",
                       action="store_true",
                       help="Listen to Raw IQ data")
    group.add_argument("--adsb",
                       action="store_true",
                       help="Listen ADS-B data sent from airplanes")
    group.add_argument("--fft",
                       action="store_true",
                       help="Start FFT sink")
    group.add_argument("--scan-fm",
                       action="store_true",
                       help="Scan FM radio spectrum")
    group.add_argument("--jammer",
                       action="store_true",
                       help="Jam certain frequency")
    group.add_argument("--transmit-fm",
                       action="store_true",
                       help="Transmit FM radio")
    group.add_argument("--transmit-temp",
                       action="store_true",
                       help="Transmit data based on the TFA 30 3200 sensor")

    parser.add_argument("-c",
                        "--center",
                        type=float,
                        help="Center frequnecy")
    parser.add_argument("-r",
                        "--rate",
                        type=float,
                        help="Sampling rate")
    parser.add_argument("-g",
                        "--gain",
                        type=float,
                        help="Set SDR gain")
    parser.add_argument("-f",
                        "--file",
                        help="Save data to file")
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="Print data to standard output")

    parser.add_argument("--on-active",
                         action="store_true",
                         help='''Record samples only on activity
                                 - reffers to Raw IQ recording''')
    parser.add_argument("--diff",
                        type=int,
                        help='''Set difference that qualifies as activity''')
    parser.add_argument("--limit",
                         type=int,
                         help="Set lower limit by Y axis for FFT Sink")
    parser.add_argument("--persistence",
                        action="store_true",
                        help="Display highest values over time")
    parser.add_argument("--cmd",
                        action="store_true",
                        help="Choose CMD mode for the FFT Sink")
    parser.add_argument("--tune-freq",
                        type=int,
                        help="Choose frequency for the wave to be transmitted")


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

    if args.temp:
        sdr_task = TempDemod(samp_rate, center_freq, gain, samp_size, verbose, out_file)
    elif args.fm_radio:
        sdr_task = FmDemod(samp_rate, center_freq, gain, samp_size, verbose, out_file)
    elif args.adsb:
        sdr_task = AdsbDemod(samp_rate, center_freq, gain, samp_size, verbose, out_file)
    elif args.fft:
        limit = args.limit
        persis = args.persistence
        cmd = args.cmd
        sdr_task = FftSink(samp_rate, center_freq, gain, samp_size, cmd, limit, persis)
    elif args.raw:
        diff = args.diff
        sdr_task = RawIQ(samp_rate, verbose, out_file, diff)
    elif args.scan_fm:
        sdr_task = ScanFm(samp_rate, center_freq, gain, samp_size)
    elif args.transmit_fm:
        tune_freq = args.tune_freq
        sdr_task = FmModulate(samp_rate, center_freq, gain, samp_size, tune_freq)
    elif args.transmit_temp:
        sdr_task = TempModulate(samp_rate, center_freq, gain, samp_size)
    elif args.jammer:
        sdr_task = JammerTask(samp_rate, center_freq, gain, samp_size)

    return sdr_task


def streaming(sdr_task):
    sdr_task.run()


def main():
    parser = argparse.ArgumentParser(description="A toolkit for the RTL-SDR")
    init_parser(parser)
    args = parser.parse_args()

    try:
        sdr_task = init_rtl_task(args)
    except OSError:
        print('No RTL-SDR found.')
        print('Exiting')
        sys.exit()

    try:
        streaming(sdr_task)
    except KeyboardInterrupt:
        print('Bye!')
