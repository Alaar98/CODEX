"""Modelo monocromático ilustrativo de conteo de fotoelectrones."""

import math

from .optics import collecting_area

PLANCK_J_S = 6.62607015e-34
LIGHT_SPEED_M_S = 299792458.0


def signal_electrons(
    irradiance_w_m2: float,
    diameter_m: float,
    wavelength_m: float,
    exposure_s: float,
    throughput: float,
    quantum_efficiency: float,
) -> float:
    """Señal total, suponiendo toda la energía en la longitud de onda dada.

    La irradiancia es la integrada en banda a la entrada de la apertura.
    No incluye pérdidas por extracción, movimiento ni saturación.
    """
    values = (irradiance_w_m2, wavelength_m, exposure_s, throughput, quantum_efficiency)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Los parámetros deben ser finitos")
    if irradiance_w_m2 < 0 or wavelength_m <= 0 or exposure_s <= 0:
        raise ValueError("Irradiancia no negativa; longitud de onda y exposición positivas")
    if not (0 <= throughput <= 1 and 0 <= quantum_efficiency <= 1):
        raise ValueError("Transmisión y eficiencia cuántica deben estar entre 0 y 1")
    photon_energy = PLANCK_J_S * LIGHT_SPEED_M_S / wavelength_m
    return (irradiance_w_m2 * collecting_area(diameter_m) * exposure_s
            * throughput * quantum_efficiency / photon_energy)


def signal_to_noise(signal_e: float, background_e: float, read_noise_e: float, pixels: int) -> float:
    """SNR con ruido de Poisson y lectura independiente por píxel.

    Fondo y señal son totales en la apertura de extracción de una exposición.
    read_noise_e es la desviación típica por píxel. No incluye corriente oscura.
    """
    if not all(math.isfinite(v) and v >= 0 for v in (signal_e, background_e, read_noise_e)):
        raise ValueError("Los términos de señal y ruido deben ser finitos y no negativos")
    if isinstance(pixels, bool) or not isinstance(pixels, int) or pixels <= 0:
        raise ValueError("El número de píxeles debe ser un entero positivo")
    variance = signal_e + background_e + pixels * read_noise_e**2
    return signal_e / math.sqrt(variance) if variance else 0.0
