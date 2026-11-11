# Audio-to-Note-Blocks
This project was an opportunity to learn how real audio systems process signals and extract frequencies in music applications. By building a DFT, or a **Discrete Fourier Transform**, I learned the mathematics at the bedrock of signal processing. The naive DFT is superseded by the FFT, or the **Fast Fourier Transform**, which significantly improves on the performance of the DFT through a recursive implementation (O(n^2) -> O(nlog(n)). Since the FFT only takes frequencies of a moment in time, I upgraded it to a STFT, or a **Short-Time Fourier Transform**, which can capture the change in extracted frequencies over time by repeating FFTs and weighting the amplitudes of each frequency with a Hann window.

## How does this work?
Note blocks in vanilla Minecraft naturally have a fixed pitch range - 25 notes total, centered on F#, to be exact. However, not all note blocks have the same octave range, and the script exploits this to cover a greater range of sounds.

<img width="675" height="339" alt="Minecraft note block key range chart, courtesy of u/CraftyGamer_ on Reddit." src="https://github.com/user-attachments/assets/77b2ba1e-31e3-4731-a70f-37ac9a522f71" />

As such, it is possible to represent up to six octaves of note block sounds, which is enough to accurately represent most audio.

## Notes & Disclaimers
> [!NOTE]
> I, Vizeon, have been making original note block music since 2021 and have composed a complete discography of music. I do not believe `.nbs` files produced by this script to be considered "note block music" in the sense that they're an artistic recreation of the input audio in note blocks. This script has no intentionality and should not represent what "good" note block music is. At its core, the script is just an approximate mapping of frequencies to note blocks with filters to clean up its output.

> [!NOTE]
> AI was used to build my conceptual understanding and to learn about audio processing techniques, but **all code was manually written by me**. I condemn the use of AI as replacement for human input and, truthfully, I had enough passion for this project learn and build every detail by hand anyway. AI was used as a research tool and nothing more. No slop here!

> [!NOTE]
> `dft.py`, `fft.py`, and `stft.py` are not used in the actual script, however I have provided them here for public viewing. They were instrumental to understanding how to begin to build a system like this.
