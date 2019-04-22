import numpy as np
import pyaudio
import scipy.signal as signal

from rtltoolkit.basetasks.demodtask import DemodTask

# 1. Refactor code and remove 'self' where possible
# 1.5. Deal with annoying warnings and remove pyadio messages
# 2. Try to make a pretty FFT sink for the audio
# 3. Make a sink for the audio wave data


class FmDemod(DemodTask):
    defaults = {
            'samp_rate' : 1e6,
            'center_freq' : 89.4e6,
            'gain' : 'auto',
            'samp_size' : 2e19
            }

    FM_BW = 200000
    AUDIO_RATE = 44100
    def __init__(self, samp_rate, center_freq, gain, samp_size, verbose = True, file_name = ''):
        super().__init__(samp_rate, center_freq, gain, samp_size, verbose, file_name)

        self.dec_rate = int(self.samp_rate / FmDemod.FM_BW)
        self.fm_rate = int(self.samp_rate / self.dec_rate)

        self.dec_audio = int(self.fm_rate / FmDemod.AUDIO_RATE)
        self.audio_rate = int(self.fm_rate / self.dec_audio)
        self.stream = None

        if verbose:
            p = pyaudio.PyAudio()
            self.stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=self.audio_rate,
                output=True,
                frames_per_buffer = self.audio_rate)


    def focus_FM_signal(samples, samp_rate):
        dec_rate = int(samp_rate / FmDemod.FM_BW)
        samples = signal.decimate(samples, dec_rate)
        return samples

    def demod_FM_signal(samples):
        samples = samples[1:] * np.conj(samples[:-1])
        samples = np.angle(samples)
        return samples

    def de_emphasis_filter(samples, fm_rate):
        # The de-emphasis filter
        # Given a signal (in a numpy array) with sampling rate samp_rate_fm
        d = fm_rate * 75e-6   # Calculate the # of samples to hit the -3dB point
        x = np.exp(-1/d)   # Calculate the decay between each sample
        b = [1-x]          # Create the filter coefficients
        a = [1,-x]
        samples = signal.lfilter(b, a, samples)
        return samples

    def focus_mono_signal(samples, fm_rate):
        dec_audio = int(fm_rate / FmDemod.AUDIO_RATE)
        samples = signal.decimate(samples, dec_audio)
        return samples

    def scale_audio(samples):
        samples *= 10000 / np.max(np.abs(samples))
        return samples

    def play_samples(audio_data, stream):
        audio_data = np.ndarray.tobytes(audio_data.astype("int16"))
        stream.write(audio_data)

    def execute(self, samples):
        samples = np.array(samples)
        samples = FmDemod.focus_FM_signal(samples, self.samp_rate)
        samples = FmDemod.demod_FM_signal(samples)
        samples = FmDemod.de_emphasis_filter(samples, self.fm_rate)
        samples = FmDemod.focus_mono_signal(samples, self.fm_rate)
        audio_data = FmDemod.scale_audio(samples)

        if self.verbose:
            FmDemod.play_samples(audio_data, self.stream)

        if self.file_name:
            with open(self.file_name, 'ab') as f:
                f.write(audio_data.astype('int16'))

    def __del__(self):
        if self.stream is not None:
            self.stream.close()

