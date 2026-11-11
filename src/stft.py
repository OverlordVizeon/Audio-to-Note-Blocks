import numpy

# SCRIPT
def pad_to_power_of_two(samples):
    sample_count = len(samples)

    if sample_count & (sample_count - 1) != 0 and sample_count > 1:
        next_power_of_two = 1 << (sample_count - 1).bit_length()
        return samples + [0] * (next_power_of_two - sample_count), sample_count

    return samples, sample_count

def fft(samples):
    total_samples = len(samples)
    
    if total_samples <= 1:
        return samples

    even_samples, odd_samples = fft(samples[0::2]), fft(samples[1::2])

    lower_frequency_bins, upper_frequency_bins = [], []
    for frequency_bin_i in range(total_samples >> 1):
        twiddle = numpy.e ** (-2j * numpy.pi * frequency_bin_i / total_samples) * odd_samples[frequency_bin_i]
        
        lower_frequency_bins.append(even_samples[frequency_bin_i] + twiddle)
        upper_frequency_bins.append(even_samples[frequency_bin_i] - twiddle)

    return lower_frequency_bins + upper_frequency_bins

def stft(samples, sample_rate, window_size, hop_size):
    # Spectrogram consists of frames; each frame consists of frequencies, amplitudes, and phase shifts
    spectrogram = []
    
    for frame_i in range(0, len(samples) - window_size + 1, hop_size):    
        spectrum = []

        frame_samples = samples[frame_i : frame_i + window_size]

        windowed_samples = []
        for sample_i, sample in enumerate(frame_samples):
            window_multiplier = 0.5 * (1 - numpy.cos(2 * numpy.pi * sample_i / (len(frame_samples) - 1)))
            windowed_samples.append(sample * window_multiplier)

        padded_samples, original_sample_count = pad_to_power_of_two(windowed_samples)
        frequency_bins = fft(padded_samples)

        nyquist_bin_i = len(frequency_bins) >> 1

        for frequency_bin_i, frequency_bin in enumerate(frequency_bins[:nyquist_bin_i + 1]):
            frequency = frequency_bin_i * sample_rate / len(frequency_bins)
            
            amplitude = numpy.sqrt(numpy.real(frequency_bin) ** 2 + numpy.imag(frequency_bin) ** 2) / original_sample_count

            if frequency_bin_i != 0 and frequency_bin_i != nyquist_bin_i:
                amplitude *= 2
            
            phase_shift = numpy.atan2(numpy.imag(frequency_bin), numpy.real(frequency_bin))

            spectrum.append({
                "frequency": frequency,
                "amplitude": amplitude,
                "phase_shift": phase_shift
            })

        spectrogram.append(spectrum)

    return spectrogram