import librosa
import numpy
import pynbs
import time

import note_block_data
import stft_optimized
import lufs_normalization

# USER INPUTS
# AUDIO_PATH is the path to the audio that will be converted to note blocks
# MINIMUM_FREQUENCY_VOLUME is the minimum volume a frequency must be for it to be turned into a note block relative to the loudest frequency in its tick. This is intended to ensure that only humanly-audible frequencies are played, optimizing song playback and exported file size at a diminishing cost to accuracy
# MAXIMUM_NOTES_PER_TICK is the maximum number of frequencies that will be processed in any tick. This is not the same as the maximum number of note blocks per tick. Set to -1 for unlimited
# TICKS_PER_SECOND is the number of Minecraft ticks in a second. The highest ticks per second (tps) possible in Minecraft is 20
# SONG_NAME is the name of the file exported. Adding '.nbs' at the end is optional
# STEREO determines whether the output is in stereo or mono

AUDIO_PATH = r"D:\Downloads\tn-shi - Synthesis.wav"
MINIMUM_FREQUENCY_VOLUME = 0.05
MAXIMUM_FREQUENCIES_PER_TICK = 25
TICKS_PER_SECOND = 60
SONG_NAME = "export.nbs"
STEREO = True

# SCRIPT
A4 = 440
A0_TO_A4 = 49
A0_TO_FSHARP3 = 33
OCTAVE_SIZE = 12

def format_song_name(song_name):
    if song_name[-4:] != ".nbs":
        song_name += ".nbs"

    return song_name

def combine_stereo_spectrograms(left_spectrogram, right_spectrogram):
    combined_spectrogram = []

    for left_spectrum, right_spectrum, in zip(left_spectrogram, right_spectrogram):
        combined_spectrum = []

        for left_frequency_bin, right_frequency_bin in zip(left_spectrum, right_spectrum):
            left_amplitude, right_amplitude = left_frequency_bin["amplitude"], right_frequency_bin["amplitude"]

            combined_amplitude = (left_amplitude + right_amplitude) / 2
            panning = 0
            
            if combined_amplitude > 0:
                panning_ratio = (right_amplitude - left_amplitude) / (right_amplitude + left_amplitude)
                panning = int(round(panning_ratio * 100))

            combined_spectrum.append({
                "frequency": left_frequency_bin["frequency"],
                "amplitude": combined_amplitude,
                "panning": panning
            })

        combined_spectrogram.append(combined_spectrum)

    return combined_spectrogram

def apply_a_weighting(spectrogram):
    if not spectrogram or not spectrogram[0]:
        return spectrogram
    
    frequencies = []

    for frequency_bin in spectrogram[0]:
        frequencies.append(frequency_bin["frequency"])

    frequencies = numpy.array(frequencies)
    
    linear_weights = tuple(10 ** (librosa.A_weighting(frequencies) / 20))
    
    for spectrum in spectrogram:
        for frequency_bin_i, frequency_bin in enumerate(spectrum):
            frequency_bin["weighted_amplitude"] = frequency_bin["amplitude"] * linear_weights[frequency_bin_i]
    
    return spectrogram

def get_global_peak_amplitudes(spectrogram):
    raw_peak_amplitude = 0
    weighted_peak_amplitude = 0
    
    for spectrum in spectrogram:
        for frequency_bin in spectrum:
            if frequency_bin["amplitude"] > raw_peak_amplitude:
                raw_peak_amplitude = frequency_bin["amplitude"]
            if frequency_bin["weighted_amplitude"] > weighted_peak_amplitude:
                weighted_peak_amplitude = frequency_bin["weighted_amplitude"]

    return raw_peak_amplitude, weighted_peak_amplitude

def get_local_weighted_peak_amplitude(spectrum):
    peak_amplitude = 0

    for frequency_bin in spectrum:
        current_amplitude = frequency_bin["weighted_amplitude"]
        if current_amplitude > peak_amplitude:
            peak_amplitude = current_amplitude

    return peak_amplitude

def filter_frequencies(spectrum, local_weighted_peak_amplitude, global_weighted_peak_amplitude):
    absolute_noise_floor = global_weighted_peak_amplitude * 0.001
    amplitude_cutoff = max(local_weighted_peak_amplitude * MINIMUM_FREQUENCY_VOLUME, absolute_noise_floor)
    
    filtered_frequency_bins = []
        
    for frequency_bin in spectrum:
        if frequency_bin["weighted_amplitude"] > amplitude_cutoff:
            filtered_frequency_bins.append(frequency_bin)

    filtered_frequency_bins.sort(key = lambda frequency_bin: frequency_bin["amplitude"], reverse = True)
    
    if MAXIMUM_FREQUENCIES_PER_TICK != -1:
        filtered_frequency_bins = filtered_frequency_bins[:MAXIMUM_FREQUENCIES_PER_TICK]

    return filtered_frequency_bins

def create_note_block(frequency_bin, peak_amplitude, lufs_normalization_factors):
    piano_key, instrument, key_in_note_block_range, velocity = None, None, None, None
    
    frequency = frequency_bin["frequency"]
    if frequency <= 0:
        return None

    piano_key = int(round(12 * numpy.log2(frequency / A4) + A0_TO_A4))
    if piano_key <= 9 or piano_key >= 82:
        return None
    
    note_block_spectrum = note_block_data.get_note_block_spectrum()
    key_in_octave_range = None

    for octave in note_block_spectrum.values():
        if piano_key < octave["start"] + OCTAVE_SIZE:
            instrument = octave["instrument"]

            key_in_octave_range = piano_key - octave["start"] + octave["key_offset"]
            key_in_note_block_range = key_in_octave_range + A0_TO_FSHARP3
            break

    velocity = frequency_bin["amplitude"] * 100 / peak_amplitude * lufs_normalization_factors[instrument][key_in_octave_range]

    return pynbs.Note(
        tick = None,
        layer = 81 - piano_key,
        instrument = instrument,
        key = key_in_note_block_range,
        velocity = velocity,
        panning = frequency_bin["panning"]
    )

def build_song(spectrogram):
    global_raw_peak_amplitude, global_weighted_peak_amplitude = get_global_peak_amplitudes(spectrogram)

    lufs_normalization_factors = lufs_normalization.get_instrument_factors()

    for spectrum_i, spectrum in enumerate(spectrogram):
        notes_in_tick = {}

        local_weighted_peak_amplitude = get_local_weighted_peak_amplitude(spectrum)
        filtered_spectrum = filter_frequencies(spectrum, local_weighted_peak_amplitude, global_weighted_peak_amplitude)

        for frequency_bin in filtered_spectrum:
            note = create_note_block(frequency_bin, global_raw_peak_amplitude, lufs_normalization_factors)
            if note == None:
                continue

            note.tick = spectrum_i

            note_identifier = (note.instrument, note.key)
            if note_identifier not in notes_in_tick or note.velocity > notes_in_tick[note_identifier].velocity:
                notes_in_tick[note_identifier] = note

        sorted_notes = list(notes_in_tick.values())
        sorted_notes.sort(key = lambda note: note.layer)

        song.notes.extend(sorted_notes)

def normalize_song_volume(song):
    loudest_velocity = 0
    for note in song.notes:
        if note.velocity > loudest_velocity:
            loudest_velocity = note.velocity

    if loudest_velocity > 0:
        global_boost_factor = 100 / loudest_velocity

        audible_notes = []
        for note in song.notes:
            note.velocity = int(round(note.velocity * global_boost_factor))

            if note.velocity > 0:
                audible_notes.append(note)

        song.notes = audible_notes

if __name__ == "__main__":
    total_start_time = time.perf_counter()

    formatted_song_name = format_song_name(SONG_NAME)

    print(f"Loading {formatted_song_name}...")
    samples, sample_rate = librosa.load(AUDIO_PATH, sr = None, mono = not STEREO)
    window_size = 4096
    hop_size = sample_rate // TICKS_PER_SECOND
    print("Done!")

    print("Building spectrogram...")
    if STEREO and samples.ndim == 2:
        left_samples, right_samples = samples[0], samples[1]
    else:
        left_samples, right_samples = samples, samples
    
    left_spectrogram = stft_optimized.stft(
        samples = left_samples,
        sample_rate = sample_rate,
        window_size = window_size,
        hop_size = hop_size
    )

    right_spectrogram = stft_optimized.stft(
        samples = right_samples,
        sample_rate = sample_rate,
        window_size = window_size,
        hop_size = hop_size
    )

    spectrogram = combine_stereo_spectrograms(left_spectrogram, right_spectrogram)
    print("Done!")

    print("Applying A-weighting...")
    spectrogram = apply_a_weighting(spectrogram)
    print("Done!")

    print("Initializing new .nbs file...")
    song = pynbs.new_file(tempo = TICKS_PER_SECOND)
    print("Done!")

    print("Building song...")
    build_song(spectrogram)
    print("Done!")

    print("Normalizing song volume...")
    normalize_song_volume(song)
    print("Done!")

    print("Exporting song...")
    song.save(format_song_name(SONG_NAME))
    print("Done!")

    total_end_time = time.perf_counter()

    print()
    print(f"Song saved as {formatted_song_name}! (took {total_end_time - total_start_time:.3f} seconds)")