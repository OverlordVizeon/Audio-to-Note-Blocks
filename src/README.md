# Audio-to-Note-Blocks
Simulating audio with Minecraft note block sounds.

This project was an opportunity to learn how real audio systems process signals and extract frequencies in music applications. By building a DFT, or a **Discrete Fourier Transform**, I learned the mathematics at the bedrock of signal processing. The naive DFT is superseded by the FFT, or the **Fast Fourier Transform**, which significantly improves on the performance of the DFT through a recursive implementation (O(n^2) -> O(nlog(n)). Finally, the FFT needed to be upgraded to a STFT, or a **Short-Time Fourier Transform**, which can capture the change in extracted frequencies over time.

`dft.py` and `fft.py` are not used in the actual script, however I have provided them here for public viewing.
