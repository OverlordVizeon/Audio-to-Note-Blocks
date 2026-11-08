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

AUDIO_PATH = r"D:\Downloads\Vizeon.wav"
FREQUENCY_PRECISION = 100
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
    # Only get frequencies which are audible; 0.01 is arbitrary
    amplitude_cutoff = peak_amplitude * 0.01
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

def get_piano_key(frequency):
    if frequency <= 0:
        return None
        
    piano_key = int(round(12 * numpy.log2(frequency / A4) + A0_TO_A4))
    
    if piano_key <= 9 or piano_key >= 82:
        return None
        
    return piano_key

def create_note(tick, key, velocity, note_block_spectrum, volume_normalization_factors):
    instrument, key_in_octave_range, velocity = None, None, velocity

    for octave in note_block_spectrum.values():
        if key <= octave["octave_start"] + OCTAVE_SIZE - 1:
            instrument = octave["instrument"]
            key_in_octave_range = key - octave["octave_start"] + octave["key_offset"]
            break

    key_in_note_block_range = key_in_octave_range + A0_TO_FSHARP3
    volume_normalization_factor = volume_normalization_factors[instrument][key_in_octave_range]

    return pynbs.Note(
        tick = tick,
        layer = None,
        instrument = instrument,
        key = key_in_note_block_range,
        velocity = int(round(velocity * volume_normalization_factor))
    )

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
    volume_normalization_factors = lufs_normalization.get_instrument_factors()

    peak_amplitude = get_peak_amplitude(spectrogram)
    filtered_spectrogram = filter_frequencies(spectrogram, peak_amplitude)

    for spectrum_i, spectrum in enumerate(filtered_spectrogram):
        notes_in_tick = {}

        for frequency_bin_i, frequency_bin in enumerate(spectrum):
            piano_key = get_piano_key(frequency_bin["frequency"])

            if piano_key is None:
                continue
            
            velocity = round(frequency_bin["amplitude"] * 100 / peak_amplitude)
            
            note_to_add = create_note(
                tick = spectrum_i,
                key = piano_key,
                velocity = velocity,
                note_block_spectrum = note_block_spectrum,
                volume_normalization_factors = volume_normalization_factors
            )

            note_identifier = (note_to_add.instrument, note_to_add.key)

            if note_identifier not in notes_in_tick or velocity > notes_in_tick[note_identifier].velocity:
                notes_in_tick[note_identifier] = note_to_add

        sorted_notes = list(notes_in_tick.values())
        sorted_notes.sort(key = lambda note: note.velocity, reverse = True)

        for note_i, note in enumerate(sorted_notes):
            note.layer = note_i
            song.notes.append(note)

        print(f"{spectrum_i + 1} ticks built!")

    song.save("export.nbs")