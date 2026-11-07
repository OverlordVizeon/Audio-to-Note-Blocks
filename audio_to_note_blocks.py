import librosa
import math
import pynbs
import stft

# USER INPUTS
AUDIO_PATH = r"D:\Music\Note Block Studio\Audio\The Chains of Reality.wav"
FREQUENCY_PRECISION = 20
TICKS_PER_SECOND = 60
A4 = 440

# SCRIPT
A0_TO_A4 = 49
A0_TO_FSHARP3 = 34

def get_highest_amplitude(spectrogram):
    highest_amplitude = 0
    
    for spectrum in spectrogram:
        for frequency_bin in spectrum:
            if frequency_bin["amplitude"] > highest_amplitude:
                highest_amplitude = frequency_bin["amplitude"]

    return highest_amplitude

def filter_frequencies(spectrogram, highest_amplitude):
    # Only get frequencies which are audible; 0.02 is arbitrary
    amplitude_cutoff = highest_amplitude * 0.02
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
        
    piano_key = int(12 * math.log2(frequency / A4) + A0_TO_A4)
    
    if piano_key <= 9 or piano_key >= 82:
        return None
        
    return piano_key

def create_note(tick, key, velocity):
    instrument, key_in_octave_range = None, None
    
    if key >= 70:
        instrument = 7 # Bell
        key_in_octave_range = key - 70 + A0_TO_FSHARP3
    elif key >= 58:
        instrument = 7 # Bell
        key_in_octave_range = key - 58 + A0_TO_FSHARP3
    elif key >= 46:
        instrument = 6 # Flute
        key_in_octave_range = key - 46 + A0_TO_FSHARP3
    elif key >= 34:
        instrument = 15 # Pling
        key_in_octave_range = key - 34 + A0_TO_FSHARP3
    elif key >= 22:
        instrument = 1 # Double Bass
        key_in_octave_range = key - 22 + A0_TO_FSHARP3
    elif key >= 10:
        instrument = 1 # Double Bass
        key_in_octave_range = key - 10 + A0_TO_FSHARP3

    return pynbs.Note(
        tick = tick,
        layer = None,
        instrument = instrument,
        key = key_in_octave_range,
        velocity = velocity
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

    highest_amplitude = get_highest_amplitude(spectrogram)
    filtered_spectrogram = filter_frequencies(spectrogram, highest_amplitude)

    # Convert to note block song
    song = pynbs.new_file(song_name = "Magic.nbs", tempo = TICKS_PER_SECOND)

    for spectrum_i, spectrum in enumerate(filtered_spectrogram):
        notes_in_tick = {}

        for frequency_bin_i, frequency_bin in enumerate(spectrum):
            piano_key = get_piano_key(frequency_bin["frequency"])

            if piano_key is None:
                continue
            
            velocity = round(frequency_bin["amplitude"] * 100 / highest_amplitude)
            
            note_to_add = create_note(spectrum_i, piano_key, velocity)
            note_identifier = (note_to_add.instrument, note_to_add.key)

            if note_identifier not in notes_in_tick or velocity > notes_in_tick[note_identifier].velocity:
                notes_in_tick[note_identifier] = note_to_add

        sorted_notes = list(notes_in_tick.values())
        sorted_notes.sort(key = lambda note: note.velocity, reverse = True)

        for note_i, note in enumerate(sorted_notes):
            note.layer = note_i
            song.notes.append(note)

    song.save("Magic.nbs")