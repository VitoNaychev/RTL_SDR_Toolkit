import numpy as np


def moving_average(samps, n=3):
    cumsum, moving_aves = [0], []

    for i, x in enumerate(samps, 1):
        cumsum.append(cumsum[i-1] + x)

        if i >= n:
            moving_ave = (cumsum[i] - cumsum[i-n])/n
        else:
            moving_ave = (cumsum[i] - cumsum[0]) / i

        moving_aves.append(moving_ave)

    for i, x in enumerate(samps[:n], 0):
        cumsum[i] = (cumsum[i - 1] + x)
        moving_ave = (cumsum[i] - cumsum[i-n]) / n
        moving_aves[i] = moving_ave

    return np.array(moving_aves)


def calc_fft(samples, samp_rate, samp_len, average=False):
    samp_fft = 20 * np.log10(2.0/samp_len * np.abs(np.fft.fft(samples)))
    neg_fft = samp_fft[len(samp_fft) // 2:]
    samp_fft = np.concatenate((neg_fft, samp_fft[:len(samp_fft) // 2]))
    if(average):
        samp_fft = moving_average(samp_fft, 100)
    return samp_fft
