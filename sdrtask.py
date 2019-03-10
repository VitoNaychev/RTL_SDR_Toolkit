import asyncio
from rtlsdr import RtlSdr

class SDRTask:
    def __init__(self, samp_rate):
        self.samp_rate = samp_rate

    def execute(self, samples):
        pass

    async def run(self, sdr, time = 0, samp_size = RtlSdr.DEFAULT_READ_SIZE):
        samp_size = 2**16
        time_pass = 0
        
        async for samples in sdr.stream(samp_size):
            self.execute(samples)
            
            if time:
                time_pass += samp_size

            if time_pass / self.samp_rate >= time and time:
                break

