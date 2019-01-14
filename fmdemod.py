import numpy as np
import pyaudio
import scipy.signal as signal

class FmDemod:
    f_bw = 200000
    audio_freq = 44100
    def __init__(self, samp_rate, output = True, file_name = ''):
        self.samp_rate = samp_rate
        self.output = output
        self.file_name = file_name
        
        self.dec_rate = int(self.samp_rate / FmDemod.f_bw)
        self.samp_rate_fm = int(self.samp_rate / self.dec_rate)

        self.dec_audio = int(self.samp_rate_fm / FmDemod.audio_freq)
        self.audio_rate = int(self.samp_rate_fm / self.dec_audio)
        self.stream = None
        if output:
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
        audio_data = np.ndarray.tobytes(samples.astype("int16"))
        return audio_data
    
    def play_samples(self, audio_data):
        self.stream.write(audio_data)
    
    def execute(self, samples):
        samples = self.focus_FM_signal(samples)
        samples = self.demod_FM_signal(samples)
        samples = self.de_emphasis_filter(samples)
        audio_data = self.focus_mono_signal(samples)
        audio_data = self.scale_audio(audio_data)
        if self.output:
            self.play_samples(audio_data)

    def __del__(self):
        if stream is not None:
            self.stream.close()

