__all__ = ["get_instrument_paths", "get_note_block_spectrum"]

instrument_folder = r"D:\Software\Minecraft Note Block Studio\Data\Sounds"
instrument_files = {
    "0": "harp.ogg", # Harp (any)
    "1": "dbass.ogg", # Double Bass (wood)
    "2": "bdrum.ogg", # Bass Drum (stone)
    "3": "sdrum.ogg", # Snare Drum (sand)
    "4": "click.ogg", # Click (glass)
    "5": "guitar.ogg", # Guitar (wool)
    "6": "flute.ogg", # Flute (clay)
    "7": "bell.ogg", # Bell (gold block)
    "8": "icechime.ogg", # Chime (ice)
    "9": "xylobone.ogg", # Xylophone (bone)
    "10": "iron_xylophone.ogg", # Iron Xylophone (iron block)
    "11": "cow_bell.ogg", # Cowbell (soul sand)
    "12": "didgeridoo.ogg", # Didgeridoo (pumpkin)
    "13": "bit.ogg", # Bit (emerald block)
    "14": "banjo.ogg", # Banjo (haybale)
    "15": "pling.ogg", # Pling (glowstone)
    "16": "trumpet.ogg", # Trumpet (waxed copper)
    "17": "trumpet_exposed.ogg", # Exposed Trumpet (waxed exposed copper)
    "18": "trumpet_weathered.ogg", # Weathered Trumpet (waxed weathered trumpet)
    "19": "trumpet_oxidized.ogg" # Oxidized Trumpet (waxed oxidized trumpet)
}

note_block_spectrum = {
    "F#1-F2": {"start": 10, "instrument": 12, "key_offset": 0}, # Didgeridoo
    "F#2-F3": {"start": 22, "instrument": 1, "key_offset": 12}, # Double Bass
    "F#3-F4": {"start": 34, "instrument": 0, "key_offset": 0}, # Harp
    "F#4-F5": {"start": 46, "instrument": 6, "key_offset": 0}, # Flute
    "F#5-F6": {"start": 58, "instrument": 6, "key_offset": 12}, # Flute
    "F#6-F7": {"start": 70, "instrument": 7, "key_offset": 12} # Bell
}

def get_instrument_paths():
    instrument_paths = {}
    for id, file in instrument_files.items():
        instrument_paths[id] = f"{instrument_folder}\\{file}"

    return instrument_paths

def get_note_block_spectrum():
    return note_block_spectrum