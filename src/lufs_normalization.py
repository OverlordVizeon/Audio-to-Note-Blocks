import librosa
import numpy
import pyloudnorm

import note_block_data

__all__ = ["get_instrument_factors"]

def get_perceived_loudness(samples, sample_rate):
    minimum_length = int(numpy.ceil(0.4 * sample_rate))
    if len(samples) < minimum_length:
        samples = numpy.pad(samples, (0, minimum_length - len(samples)), mode = "wrap")

    meter = pyloudnorm.Meter(sample_rate)
    return meter.integrated_loudness(samples)

def get_instrument_factors():
    instrument_paths = note_block_data.get_instrument_paths()
    note_block_spectrum = note_block_data.get_note_block_spectrum()

    instrument_lufs = {}
    for octave in note_block_spectrum.values():
        instrument_id, key_offset = octave["instrument"], octave["key_offset"]
        path = instrument_paths[str(instrument_id)]
        instrument_samples, sample_rate = librosa.load(path, sr = None)

        if instrument_id not in instrument_lufs:
            instrument_lufs[instrument_id] = {}

        for semitone in range(key_offset, key_offset + 12):
            pitch_shift = 2 ** ((semitone - 12) / 12)
            target_sample_rate = sample_rate / pitch_shift
            
            shifted_instrument_samples = librosa.resample(
                instrument_samples,
                orig_sr = sample_rate,
                target_sr = target_sample_rate
            )

            instrument_lufs[instrument_id][semitone] = float(get_perceived_loudness(shifted_instrument_samples, sample_rate))

    all_lufs = []
    for semitones in instrument_lufs.values():
        all_lufs.extend(semitones.values())

    quietest_lufs = min(all_lufs)

    instrument_factors = {}
    for instrument_id, semitones in instrument_lufs.items():
        instrument_factors[instrument_id] = {}
        for semitone, instrument_loudness in semitones.items():
            instrument_factors[instrument_id][semitone] = 10 ** ((quietest_lufs - instrument_loudness) / 20)

    return instrument_factors