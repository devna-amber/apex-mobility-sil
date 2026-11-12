#!/usr/bin/env python3
"""
telemetry/dsp-filter/signal_conditioning.py
Discrete-Time FIR Low-Pass Filter & FFT Spectral Analyzer for EV Powertrain Telemetry.
"""

import sys
import numpy as np


def design_fir_lowpass(num_taps: int, cutoff_hz: float, sample_rate_hz: float) -> np.ndarray:
    """Design a linear-phase Hamming-windowed sinc FIR low-pass filter."""
    nyquist = sample_rate_hz / 2.0
    norm_cutoff = cutoff_hz / nyquist
    n = np.arange(num_taps) - (num_taps - 1) / 2.0

    # Ideal sinc impulse response
    h = np.sinc(norm_cutoff * n)
    # Apply Hamming window to suppress spectral sidelobes
    window = 0.54 - 0.46 * np.cos(2.0 * np.pi * np.arange(num_taps) / (num_taps - 1))
    h *= window
    # Normalize for unity DC gain (0 dB at 0 Hz)
    h /= np.sum(h)
    return h


def compute_snr_db(clean_signal: np.ndarray, test_signal: np.ndarray) -> float:
    """Compute Signal-to-Noise Ratio (SNR) in decibels."""
    noise = test_signal - clean_signal
    signal_power = np.mean(clean_signal ** 2)
    noise_power = np.mean(noise ** 2)
    if noise_power == 0:
        return float("inf")
    return 10.0 * np.log10(signal_power / noise_power)


def dominant_frequency_hz(signal: np.ndarray, sample_rate_hz: float) -> float:
    """Identify the peak frequency component using real FFT."""
    spectrum = np.abs(np.fft.rfft(signal - np.mean(signal)))
    freqs = np.fft.rfftfreq(len(signal), d=1.0 / sample_rate_hz)
    return float(freqs[np.argmax(spectrum)])


def main() -> int:
    fs = 2000.0          # 2 kHz telemetry sampling rate
    duration_s = 1.0     # 1-second simulation window
    t = np.linspace(0, duration_s, int(fs * duration_s), endpoint=False)

    # 1. Ground-truth EV battery current profile: 120A DC + 5Hz acceleration transient
    clean_current = 120.0 + 35.0 * np.sin(2.0 * np.pi * 5.0 * t)

    # 2. Inject 450Hz PWM inverter switching ripple + broadband sensor noise
    rng = np.random.default_rng(seed=42)
    inverter_ripple = 18.0 * np.sin(2.0 * np.pi * 450.0 * t)
    thermal_noise = rng.normal(0.0, 2.5, size=t.shape)
    noisy_current = clean_current + inverter_ripple + thermal_noise

    # 3. Design 51-tap FIR low-pass filter (40Hz cutoff) and convolve
    fir_taps = design_fir_lowpass(num_taps=51, cutoff_hz=40.0, sample_rate_hz=fs)
    filtered_current = np.convolve(noisy_current, fir_taps, mode="same")

    # Trim edge transient samples for accurate steady-state metrics
    trim = 30
    snr_before = compute_snr_db(clean_current[trim:-trim], noisy_current[trim:-trim])
    snr_after = compute_snr_db(clean_current[trim:-trim], filtered_current[trim:-trim])
    peak_noise_freq = dominant_frequency_hz(noisy_current - clean_current, fs)

    print(f"[SIL-DSP] Sample Rate          : {fs:.0f} Hz | FIR Taps: {len(fir_taps)}")
    print(f"[SIL-DSP] Detected Noise Peak  : {peak_noise_freq:.1f} Hz (Inverter Switching)")
    print(f"[SIL-DSP] Raw Sensor SNR       : {snr_before:.2f} dB")
    print(f"[SIL-DSP] Filtered Telemetry SNR: {snr_after:.2f} dB (+{snr_after - snr_before:.2f} dB gain)")

    # Verify at least 12 dB SNR improvement and false-trip elimination
    if (snr_after - snr_before) >= 12.0 and np.max(filtered_current[trim:-trim]) < 165.0:
        print("[PASS] FIR filter attenuated inverter ripple and prevented false over-current trip.")
        return 0
    else:
        print("[FAIL] Telemetry SNR gain below safety threshold.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
