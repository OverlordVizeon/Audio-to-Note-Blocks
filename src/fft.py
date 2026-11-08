import numpy

# USER INPUTS
# f(x) can be any function
# SECONDS represents the amount of time processed by the DFT. When f(x) = sin(2 * pi * x), f(seconds) where seconds = 1 evaluates the entire period of the curve 'sample_rate' times, up to but not including (f(seconds))
# SAMPLE_RATE is the number of times a function is sampled per second, or the Hz. It must be greater than the nyquist frequency, or double the frequency of the highest-frequency sine wave in a function, at the absolute minimum in order for the DFT to give correct results.

def f(x):
    return numpy.sin(50 * 2 * numpy.pi * x) + numpy.sin(120 * 2 * numpy.pi * x)

SECONDS = 1
SAMPLE_RATE = 300

# SCRIPT
def get_samples(f, duration_in_seconds, sample_rate):
    samples = []

    sample_count = int(numpy.floor(duration_in_seconds * sample_rate))
    for sample in range(sample_count):
        samples.append(f(sample / sample_rate))

    return samples

def pad_to_power_of_two(samples):
    sample_count = len(samples)
    if sample_count <= 1:
        return samples

    if sample_count & (sample_count - 1) != 0:
        next_power_of_two = 1 << (sample_count - 1).bit_length()
        return samples + [0] * (next_power_of_two - sample_count)

    return samples

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

def get_spectrum(frequency_bins, sample_rate, original_sample_count):
    spectrum = []
    total_bins = len(frequency_bins)

    for frequency_bin_i in range((total_bins >> 1) + 1):
        frequency_bin = frequency_bins[frequency_bin_i]
        
        frequency = frequency_bin_i * sample_rate / total_bins
        amplitude = numpy.sqrt(numpy.real(frequency_bin) ** 2 + numpy.imag(frequency_bin) ** 2) / original_sample_count
        phase_shift = numpy.atan2(numpy.imag(frequency_bin), numpy.real(frequency_bin))

        if frequency_bin_i != 0 and frequency_bin_i != total_bins >> 1:
            amplitude *= 2
        
        spectrum.append({
            "frequency": frequency,
            "amplitude": amplitude,
            "phase_shift": phase_shift
        })

    return spectrum

# EXECUTION
if __name__ == "__main__":
    samples = get_samples(f, SECONDS, SAMPLE_RATE)
    original_sample_count = len(samples)
    spectrum = get_spectrum(fft(pad_to_power_of_two(samples)), SAMPLE_RATE, original_sample_count)

    for frequency in spectrum:
        print(frequency["frequency"], "-" * round(frequency["amplitude"] * 100))