import numpy

__all__ = ["stft"]

def stft(samples, sample_rate, window_size, hop_size):
    num_frames = 1 + (len(samples) - window_size) // hop_size

    strides = (samples.strides[0] * hop_size, samples.strides[0])
    frames = numpy.lib.stride_tricks.as_strided(
        samples,
        shape = (num_frames, window_size),
        strides = strides
    )

    hann_window = numpy.hanning(window_size)
    windowed_frames = frames * hann_window

    frequency_bins = numpy.fft.rfft(windowed_frames, axis = 1)

    magnitudes = numpy.abs(frequency_bins) * (2.0 / numpy.sum(hann_window))
    frequencies = numpy.fft.rfftfreq(window_size, d = 1.0 / sample_rate)

    spectrogram = []
    for frame_magnitudes in magnitudes:
        spectrum = []
        for frequency_bin_i, amplitude in enumerate(frame_magnitudes):
            spectrum.append({
                "frequency": float(frequencies[frequency_bin_i]),
                "amplitude": float(amplitude)
            })

        spectrogram.append(spectrum)

    return spectrogram