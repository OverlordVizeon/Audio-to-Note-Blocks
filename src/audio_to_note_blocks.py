import librosa
import numpy
import pynbs
import time

import note_block_data
import lufs_normalization

# USER INPUTS
# AUDIO_PATH is the path to the audio that will be converted to note blocks
# MINIMUM_FREQUENCY_VOLUME is the minimum volume a frequency must be for it to be turned into a note block relative to the loudest frequency in its tick. This is intended to ensure that only humanly-audible frequencies are played, optimizing song playback and exported file size at a diminishing cost to accuracy
# TICKS_PER_SECOND is the number of Minecraft ticks in a second. The highest ticks per second (tps) possible in Minecraft is 20
# SONG_NAME is the name of the file exported. Adding '.nbs' at the end is optional
# STEREO determines whether the output is in stereo or mono

AUDIO_PATH = r"D:\Downloads\Mariah Carey - All I Want For Christmas Is You.wav"
MAXIMUM_FREQUENCIES_PER_TICK = 40 # Currently unused
TICKS_PER_SECOND = 20
SONG_NAME = "export.nbs"
STEREO = True

# SCRIPT
A4 = 440
A0_TO_A4 = 49
A0_TO_FSHARP3 = 33
ABSOLUTE_NOISE_FLOOR = 0.001
OCTAVE_SIZE = 12

def format_song_name(song_name):
    if song_name[-4:] != ".nbs":
        song_name += ".nbs"

    return song_name

def fft(samples, sample_rate, window_size):
    hann_window = numpy.hanning(window_size)
    windowed_frames = samples * hann_window

    fft_window_size = window_size * 4
    frequency_bins = numpy.fft.rfft(windowed_frames, n = fft_window_size)

    frequencies = numpy.fft.rfftfreq(fft_window_size, d = 1 / sample_rate)
    amplitudes = numpy.abs(frequency_bins) * (2 / numpy.sum(hann_window))

    return frequencies, amplitudes

def get_spectrum(samples, sample_rate, window_size, is_stereo):
    audio_channels = samples.ndim

    if is_stereo and audio_channels == 2:
        left_samples, right_samples = samples[0], samples[1]
    else:
        left_samples, right_samples = samples, samples
    
    frequencies, left_amplitudes = fft(samples = left_samples, sample_rate = sample_rate, window_size = window_size)
    _, right_amplitudes = fft(samples = right_samples, sample_rate = sample_rate, window_size = window_size)

    return frequencies, left_amplitudes, right_amplitudes

def build_stereo_sound(left_amplitudes, right_amplitudes):
    combined_amplitudes = (left_amplitudes + right_amplitudes) / 2

    epsilon = 1e-10
    pannings = numpy.round((right_amplitudes - left_amplitudes) / (right_amplitudes + left_amplitudes + epsilon) * 100).astype(int)
    
    return combined_amplitudes, pannings

def apply_a_weighting(frequencies, amplitudes):
    linear_weights = numpy.array(10 ** (librosa.A_weighting(frequencies) / 20))
    weighted_amplitudes = amplitudes * linear_weights

    return weighted_amplitudes

def filter_frequencies(frequencies, amplitudes, weighted_amplitudes, pannings):
    if len(weighted_amplitudes) < 3:
        return frequencies, amplitudes, pannings
    
    minimum_frequency = A4 * 2 ** ((10 - A0_TO_A4 - 0.5) / 12)
    maximum_frequency = A4 * 2 ** ((81 - A0_TO_A4 + 0.5) / 12)
    playable = (frequencies >= minimum_frequency) & (frequencies <= maximum_frequency)

    frequencies = frequencies[playable]
    amplitudes = amplitudes[playable]
    weighted_amplitudes = weighted_amplitudes[playable]
    pannings = pannings[playable]

    if len(weighted_amplitudes) == 0:
        return frequencies, amplitudes, pannings

    peaks = numpy.zeros(len(amplitudes), dtype = bool)
    peaks[1:-1] = (amplitudes[1:-1] > amplitudes[:-2]) & (amplitudes[1:-1] >= amplitudes[2:])

    frequencies = frequencies[peaks]
    amplitudes = amplitudes[peaks]
    weighted_amplitudes = weighted_amplitudes[peaks]
    pannings = pannings[peaks]

    return frequencies, amplitudes, pannings

def create_note_block(tick, frequency, amplitude, panning, note_block_spectrum, lufs_normalization_factors):
    if frequency <= 0:
        return None
    
    piano_key = int(round(12 * numpy.log2(frequency / A4) + A0_TO_A4))
    if piano_key <= 9 or piano_key >= 82:
        return None

    instrument, key_in_note_block_range = None, None
    for octave in note_block_spectrum.values():
        if piano_key < octave["start"] + OCTAVE_SIZE:
            instrument = octave["instrument"]

            key_in_octave_range = piano_key - octave["start"] + octave["key_offset"]
            key_in_note_block_range = key_in_octave_range + A0_TO_FSHARP3
            break

    velocity = amplitude * lufs_normalization_factors[instrument][key_in_octave_range]
    
    piano_key_offset = note_block_spectrum[0]["start"] + note_block_spectrum[5]["start"] + 1
    return pynbs.Note(
        tick = tick,
        layer = piano_key_offset - piano_key,
        instrument = instrument,
        key = key_in_note_block_range,
        velocity = velocity,
        panning = int(panning)
    )

def build_song(tick_i, frequencies, amplitudes, pannings, note_block_spectrum, lufs_normalization_factors):
    notes_in_tick = {}
    
    for frequency, amplitude, panning in zip(frequencies, amplitudes, pannings):
        note = create_note_block(tick_i, frequency, amplitude, panning, note_block_spectrum, lufs_normalization_factors)
        if note == None:
            continue 
        
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

    print("Initializing new .nbs file...")
    song = pynbs.new_file(tempo = TICKS_PER_SECOND)
    note_block_spectrum = note_block_data.get_note_block_spectrum()
    lufs_normalization_factors = lufs_normalization.get_instrument_factors()
    print("Done!")

    print("Building song...")
    total_samples = samples.shape[-1]
    for tick_i, sample_i in enumerate(range(0, total_samples - window_size + 1, hop_size)):
        tick_samples = samples[..., sample_i : sample_i + window_size]

        frequencies, left_amplitudes, right_amplitudes = get_spectrum(tick_samples, sample_rate, window_size, STEREO)
        amplitudes, pannings = build_stereo_sound(left_amplitudes, right_amplitudes)
        weighted_amplitudes = apply_a_weighting(frequencies, amplitudes)
        frequencies, amplitudes, pannings = filter_frequencies(frequencies, amplitudes, weighted_amplitudes, pannings)
        
        build_song(tick_i, frequencies, amplitudes, pannings, note_block_spectrum, lufs_normalization_factors)
    print("Done!")

    print("Normalizing song volume...")
    normalize_song_volume(song)
    print("Done!")

    print("Exporting song...")
    song.save(formatted_song_name)
    print("Done!")

    total_end_time = time.perf_counter()

    print()
    print(f"Song saved as {formatted_song_name}! (took {total_end_time - total_start_time:.3f} seconds)")