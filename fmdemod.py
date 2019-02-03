import numpy as np
import pyaudio
import scipy.signal as signal
from sdrtask import SDRTask
from demodtask import DemodTask

class FmDemod(DemodTask):
    f_bw = 200000
    audio_freq = 44100
    def __init__(self, samp_rate, verbose = True, file_name = ''):
        super().__init__(samp_rate, verbose, file_name)

        self.dec_rate = int(self.samp_rate / FmDemod.f_bw)
        self.samp_rate_fm = int(self.samp_rate / self.dec_rate)

        self.dec_audio = int(self.samp_rate_fm / FmDemod.audio_freq)
        self.audio_rate = int(self.samp_rate_fm / self.dec_audio)
        self.stream = None
        if verbose:
            p = pyaudio.PyAudio()
            self.stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=self.audio_rate,
                output=True,
                frames_per_buffer = self.audio_rate)


    def focus_FM_signal(self, samples):
        samples = signal.decimate(samples, self.dec_rate)
        return samples

    def demod_FM_signal(self, samples):
        samples = samples[1:] * np.conj(samples[:-1])
        samples = np.angle(samples)
        return samples

    def de_emphasis_filter(self, samples):
        # The de-emphasis filter
        # Given a signal (in a numpy array) with sampling rate samp_rate_fm
        d = self.samp_rate_fm * 75e-6   # Calculate the # of samples to hit the -3dB point
        x = np.exp(-1/d)   # Calculate the decay between each sample
        b = [1-x]          # Create the filter coefficients
        a = [1,-x]
        samples = signal.lfilter(b, a, samples)
        return samples

    def focus_mono_signal(self, samples):
        samples = signal.decimate(samples, self.dec_audio)
        return samples

    def scale_audio(self, samples):
        samples *= 10000 / np.max(np.abs(samples))
        return samples
    
    def play_samples(self, audio_data):
        audio_data = np.ndarray.tobytes(audio_data.astype("int16"))
        self.stream.write(audio_data)
    
    def execute(self, samples):
        samples = self.focus_FM_signal(samples)
        samples = self.demod_FM_signal(samples)
        samples = self.de_emphasis_filter(samples)
        samples = self.focus_mono_signal(samples)
        audio_data = self.scale_audio(samples)
        if self.verbose:
            self.play_samples(audio_data)
        if self.file_name:
            with open(self.file_name, 'ab') as f:
                f.write(audio_data.astype('int16'))

    def __del__(self):
        if stream is not None:
            self.stream.close()

