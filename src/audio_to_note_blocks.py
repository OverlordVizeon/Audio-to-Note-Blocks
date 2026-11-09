import librosa
import numpy
import pynbs

import note_block_data
import stft
import lufs_normalization

# USER INPUTS
# AUDIO_PATH is the path to the audio that will be converted to note blocks
# FREQUENCY_PRECISION is the maximum number of frequencies (note blocks) that can be present in any tick
# TICKS_PER_SECOND is the number of Minecraft ticks in a second. The highest ticks per second (tps) possible in Minecraft is 20
# A4 is the frequency of the key A in the fourth octave and equals 440 in the 12-tone equal temperament tuning system. You can change this to experiment with different tuning systems, but A4 = 440 is generally considered the universal standard for 12-TET

AUDIO_PATH = r"D:\Downloads\tn-shi - Synthesis.wav"
FREQUENCY_PRECISION = 50
TICKS_PER_SECOND = 60
A4 = 440

# SCRIPT
A0_TO_A4 = 49
A0_TO_FSHARP3 = 33
OCTAVE_SIZE = 12

def get_peak_amplitude(spectrogram):
    peak_amplitude = 0
    
    for spectrum in spectrogram:
        for frequency_bin in spectrum:
            if frequency_bin["amplitude"] > peak_amplitude:
                peak_amplitude = frequency_bin["amplitude"]

    return peak_amplitude

def filter_frequencies(spectrogram, peak_amplitude):
    # Only get frequencies which are audible; 0.03 is arbitrary, but appears to be a good balance of precision and size
    amplitude_cutoff = peak_amplitude * 0.03
    filtered_spectrogram = []
    
    for spectrum in spectrogram:
        filtered_frequency_bins = []
        
        for frequency_bin in spectrum:
            if frequency_bin["amplitude"] > amplitude_cutoff:
                filtered_frequency_bins.append(frequency_bin)

        filtered_frequency_bins.sort(key = lambda frequency_bin: frequency_bin["amplitude"], reverse = True)
        filtered_frequency_bins = filtered_frequency_bins[:FREQUENCY_PRECISION]
        filtered_spectrogram.append(filtered_frequency_bins)

    return filtered_spectrogram

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

def normalize_song_volume(notes):
    loudest_velocity = 0
    for note in notes:
        if note.velocity > loudest_velocity:
            loudest_velocity = note.velocity

    global_boost_factor = 100 / loudest_velocity

    for note in song.notes:
        note.velocity = int(round(note.velocity * global_boost_factor))

    return notes

if __name__ == "__main__":
    samples, sample_rate = librosa.load(AUDIO_PATH, sr=None)
    window_size = 4096
    hop_size = sample_rate // TICKS_PER_SECOND

    spectrogram = stft.stft(
        samples = samples,
        sample_rate = sample_rate,
        window_size = window_size,
        hop_size = hop_size
    )

    song = pynbs.new_file(song_name = "Magic.nbs", tempo = TICKS_PER_SECOND)

    note_block_spectrum = note_block_data.get_note_block_spectrum()
    lufs_normalization_factors = lufs_normalization.get_instrument_factors()

    peak_amplitude = get_peak_amplitude(spectrogram)
    filtered_spectrogram = filter_frequencies(spectrogram, peak_amplitude)

    for spectrum_i, spectrum in enumerate(filtered_spectrogram):
        notes_in_tick = {}

        for frequency_bin_i, frequency_bin in enumerate(spectrum):
            note = create_note_block(frequency_bin, peak_amplitude, lufs_normalization_factors)
            if note == None:
                continue

            note.tick = spectrum_i

            note_identifier = (note.instrument, note.key)
            if note_identifier not in notes_in_tick or note.velocity > notes_in_tick[note_identifier].velocity:
                notes_in_tick[note_identifier] = note

        for note in notes_in_tick.values():
            song.notes.append(note)

    song.notes = normalize_song_volume(song.notes)

    print("Exporting song...")
    song.save("export.nbs")

    print("Export complete!")