import asyncio
from rtlsdr import RtlSdr


class SDRTask:
    defaults = {}
    def __init__(self, samp_rate, center_freq, gain, samp_size):
        # Instantiate rtl-sdr instance.
        self._sdr = RtlSdr()

        # Set the defaults if any of the above values
        # is skipped. The dicitonary 'defaults' is used from 
        # the child classes to set its default values.
        self.set_defaults()

        if samp_rate:
            self.samp_rate = samp_rate
            self._sdr.sample_rate = samp_rate
        if center_freq:
            self._sdr.center_freq = center_freq
        if gain:
            self._sdr.gain = gain
        if samp_size:
            self.samp_size = samp_size


    def set_defaults(self):
        self.samp_rate = self.defaults['samp_rate']
        self._sdr.sample_rate = self.defaults['samp_rate']
        self._sdr.center_freq = self.defaults['center_freq']
        self._sdr.samp_rate = self.defaults['gain']
        self.samp_size = self.defaults['samp_size']

    def execute(self, samples):
        pass

    async def run(self, time = 0):
        time_pass = 0

        async for samples in self._sdr.stream(self.samp_size):
            self.execute(samples)

            if time:
                time_pass += self._samp_size

            if time_pass / self.samp_rate >= time and time:
                break
        await _sdr.stop()

