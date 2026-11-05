"""Ejemplo sintético; no representa una misión ni un objeto real."""

from space_debris_detection.optics import diffraction_limit
from space_debris_detection.radiometry import signal_electrons, signal_to_noise


def main() -> None:
    diameter_m = 0.20
    wavelength_m = 550e-9
    signal = signal_electrons(
        irradiance_w_m2=1e-14,
        diameter_m=diameter_m,
        wavelength_m=wavelength_m,
        exposure_s=1.0,
        throughput=0.6,
        quantum_efficiency=0.8,
    )
    snr = signal_to_noise(signal, background_e=100.0, read_noise_e=3.0, pixels=9)
    print("Presupuesto ilustrativo (hipótesis sintéticas)")
    print(f"Límite de difracción: {diffraction_limit(wavelength_m, diameter_m):.3e} rad")
    print(f"Señal: {signal:.2f} e−")
    print(f"SNR: {snr:.2f}")


if __name__ == "__main__":
    main()
