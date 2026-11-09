import librosa
import numpy
import pynbs
import time

import note_block_data
import stft
import lufs_normalization

# USER INPUTS
# AUDIO_PATH is the path to the audio that will be converted to note blocks
# MINIMUM_FREQUENCY_VOLUME is the minimum volume a frequency must be for it to be turned into a note block relative to the loudest frequency in its tick. This is intended to ensure that only humanly-audible frequencies are played, optimizing song playback and exported file size at a diminishing cost to accuracy
# MAXIMUM_NOTES_PER_TICK is the maximum number of frequencies that will be processed in any tick. This is not the same as the maximum number of note blocks per tick. Set to -1 for unlimited
# TICKS_PER_SECOND is the number of Minecraft ticks in a second. The highest ticks per second (tps) possible in Minecraft is 20
# SONG_NAME is the name of the file exported. Adding '.nbs' at the end is optional

AUDIO_PATH = r"D:\Music\Note Block Studio\Audio\The Chains of Reality.wav"
MINIMUM_FREQUENCY_VOLUME = 0.1
MAXIMUM_FREQUENCIES_PER_TICK = 40
TICKS_PER_SECOND = 60
SONG_NAME = "export.nbs"

# SCRIPT
A4 = 440
A0_TO_A4 = 49
A0_TO_FSHARP3 = 33
OCTAVE_SIZE = 12

def format_song_name(song_name):
    if song_name[-4:] != ".nbs":
        song_name += ".nbs"

    return song_name

def apply_a_weighting(spectrogram):
    for spectrum in spectrogram:
        for frequency_bin in spectrum:
            frequency = frequency_bin["frequency"]

            decibel_weight = librosa.A_weighting(frequency)
            linear_weight = 10 ** (decibel_weight / 20)

            frequency_bin["amplitude"] *= linear_weight

    return spectrogram

def get_global_peak_amplitude(spectrogram):
    peak_amplitude = 0
    
    for spectrum in spectrogram:
        local_peak_amplitude = get_local_peak_amplitude(spectrum)
        if local_peak_amplitude > peak_amplitude:
            peak_amplitude = local_peak_amplitude

    return peak_amplitude

def get_local_peak_amplitude(spectrum):
    peak_amplitude = 0

    for frequency_bin in spectrum:
        current_amplitude = frequency_bin["amplitude"]
        if current_amplitude > peak_amplitude:
            peak_amplitude = current_amplitude

    return peak_amplitude

def filter_frequencies(spectrum, local_peak_amplitude, global_peak_amplitude):
    absolute_noise_floor = global_peak_amplitude * 0.001
    amplitude_cutoff = max(local_peak_amplitude * MINIMUM_FREQUENCY_VOLUME, absolute_noise_floor)
    
    filtered_frequency_bins = []
        
    for frequency_bin in spectrum:
        if frequency_bin["amplitude"] > amplitude_cutoff:
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
        velocity = velocity
    )

def build_song(spectrogram):
    global_peak_amplitude = get_global_peak_amplitude(spectrogram)

    lufs_normalization_factors = lufs_normalization.get_instrument_factors()

    for spectrum_i, spectrum in enumerate(spectrogram):
        notes_in_tick = {}

        local_peak_amplitude = get_local_peak_amplitude(spectrum)
        filtered_spectrum = filter_frequencies(spectrum, local_peak_amplitude, global_peak_amplitude)

        for frequency_bin in filtered_spectrum:
            note = create_note_block(frequency_bin, global_peak_amplitude, lufs_normalization_factors)
            if note == None:
                continue

            note.tick = spectrum_i

            note_identifier = (note.instrument, note.key)
            if note_identifier not in notes_in_tick or note.velocity > notes_in_tick[note_identifier].velocity:
                notes_in_tick[note_identifier] = note

        sorted_notes = list(notes_in_tick.values())
        sorted_notes.sort(key = lambda note: note.layer)

        for note in sorted_notes:
            song.notes.append(note)

def normalize_song_volume(notes):
    loudest_velocity = 0
    for note in notes:
        if note.velocity > loudest_velocity:
            loudest_velocity = note.velocity

    global_boost_factor = 100 / loudest_velocity

    for note in song.notes:
        note.velocity = int(round(note.velocity * global_boost_factor))

    return notes

def remove_silent_notes(notes):
    for note in notes:
        if note.velocity == 0:
            notes.remove(note)

if __name__ == "__main__":
    total_start_time = time.perf_counter()

    formatted_song_name = format_song_name(SONG_NAME)

    print(f"Loading {formatted_song_name}...")
    samples, sample_rate = librosa.load(AUDIO_PATH, sr=None)
    window_size = 4096
    hop_size = sample_rate // TICKS_PER_SECOND
    print("Done!")

    print("Building spectrogram...")
    spectrogram = stft.stft(
        samples = samples,
        sample_rate = sample_rate,
        window_size = window_size,
        hop_size = hop_size
    )
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
    normalize_song_volume(song.notes)
    print("Done!")

    print("Removing silent notes...")
    remove_silent_notes(song.notes)
    print("Done!")

    print("Exporting song...")
    song.save(format_song_name(SONG_NAME))
    print("Done!")

    total_end_time = time.perf_counter()

    print()
    print(f"Song saved as {formatted_song_name}! (Took {total_end_time - total_start_time:.3f} seconds)")