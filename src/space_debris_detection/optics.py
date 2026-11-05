"""Relaciones ópticas de primer orden; unidades SI."""

import math


def collecting_area(diameter_m: float) -> float:
    """Área de una apertura circular sin obstrucción, en m²."""
    if not math.isfinite(diameter_m) or diameter_m <= 0:
        raise ValueError("El diámetro debe ser finito y positivo")
    return math.pi * diameter_m**2 / 4


def diffraction_limit(wavelength_m: float, diameter_m: float) -> float:
    """Criterio de Rayleigh para apertura circular, en radianes."""
    collecting_area(diameter_m)
    if not math.isfinite(wavelength_m) or wavelength_m <= 0:
        raise ValueError("La longitud de onda debe ser finita y positiva")
    return 1.22 * wavelength_m / diameter_m
