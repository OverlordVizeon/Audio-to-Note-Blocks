import numpy

# EXPLANATION
# f(x) can be any function
# 'seconds' represents the amount of time processed by the DFT. When f(x) = sin(2 * pi * x), f(seconds) where seconds = 1 evaluates the entire period of the curve 'sample_rate' times, up to but not including (f(seconds))
# sample_rate is the number of times a function is sampled per second, or the Hz. It must be greater than the nyquist frequency, or double the frequency of the highest-frequency sine wave in a function, at the absolute minimum in order for the DFT to give correct results.

# USER INPUTS
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

def dft(samples):
    frequency_bins = []
    total_samples = len(samples)
    
    for frequency_bin_i in range(total_samples):
        frequency_bin = 0 + 0j
        
        for sample_i, sample in enumerate(samples):
            frequency_bin += sample * numpy.e ** (-2j * numpy.pi * sample_i * frequency_bin_i / total_samples)

        frequency_bins.append(frequency_bin)

    return frequency_bins

def get_spectrum(frequency_bins, sample_rate):
    spectrum = []
    total_bins = len(frequency_bins)

    for frequency_bin_i in range((total_bins >> 1) + 1):
        frequency_bin = frequency_bins[frequency_bin_i]

        frequency = frequency_bin_i * sample_rate / total_bins
        amplitude = numpy.sqrt(numpy.real(frequency_bin) ** 2 + numpy.imag(frequency_bin) ** 2) / total_bins
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
    spectrum = get_spectrum(dft(get_samples(f, SECONDS, SAMPLE_RATE)), SAMPLE_RATE)

    for frequency in spectrum:
        print(frequency["frequency"], "-" * round(frequency["amplitude"] * 100))