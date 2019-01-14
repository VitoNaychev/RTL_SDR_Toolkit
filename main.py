import asyncio
import numpy as np
import scipy.signal as signal
import pyaudio
from rtlsdr import RtlSdr
from tempdemod import TempDemod
from fmdemod import FmDemod

async def execute(temp_demod, samples):
    temp_demod.execute(np.array(samples).astype("complex64"))


async def streaming():
    samp_rate = 1e6
    samp_size = 2**17

    sdr = RtlSdr()
    sdr.sample_rate = samp_rate
    #sdr.center_freq = 433.7e6
    sdr.center_freq = 98.3e6
    sdr.gain = 'auto'

    temp_demod = TempDemod(samp_rate)
    fm_demod = FmDemod(samp_rate)

    async for samples in sdr.stream(samp_size):
        fm_demod.execute(samples)

    await sdr.stop()

    sdr.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(streaming())
loop.close()
