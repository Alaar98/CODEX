"""TRACE first-order radiometry; see project notes for scope and conventions."""

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path

import numpy as np
import openpyxl

H = 6.62607015e-34
C = 299792458.
K = 1.380649e-23
SIGMA_SB = 5.670374419e-8
AB_ZERO = 3631e-26  # W m^-2 Hz^-1
ARCSEC_PER_RAD = 180*3600/np.pi
ERF = np.vectorize(math.erf, otypes=[float])

# Required workbook fields: units and SI conversion, not parameter values.
FIELDS = {
    "N_x": ("px", 1), "N_y": ("px", 1), "p_pixel": ("µm", 1e-6),
    "W_x": ("mm", 1e-3), "W_y": ("mm", 1e-3), "QE": ("-", 1),
    "lambda_min": ("nm", 1e-9), "lambda_max": ("nm", 1e-9),
    "t_int": ("ms", 1e-3), "sigma_read": ("e- RMS/pixel/read", 1),
    "I_dark": ("e-/pixel/s", 1), "SNR_min": ("-", 1),
    "FOV_min": ("deg", 1), "FOV_max": ("deg", 1),
    "D_ap_min": ("mm", 1e-3), "D_ap_max": ("mm", 1e-3),
    "T_optics": ("-", 1), "PSF_FWHM": ("px", 1),
    "sky_background": ("mag/arcsec²", 1), "albedo_pess": ("-", 1),
    "albedo_nom": ("-", 1), "albedo_opt": ("-", 1),
    "detector_short_dim": ("mm", 1e-3), "sun_exclusion_min": ("deg", 1),
    "FWC_high_gain": ("e-/pixel", 1), "FWC_low_gain_lower_bound": ("e-/pixel", 1),
}


@dataclass(frozen=True)
class Baseline:
    values: dict
    source_sha256: str

    def __getitem__(self, key):
        return self.values[key]


def load_baseline(path: Path):
    book = openpyxl.load_workbook(path, data_only=True)
    rows = {}
    for sheet in ("Detector_Baseline", "Optica_Deteccion"):
        for row in book[sheet].iter_rows(min_row=2, values_only=True):
            name = row[1]
            if name in rows:
                raise ValueError(f"Duplicate workbook field: {name}")
            rows[name] = row
    values = {}
    for name, (unit, factor) in FIELDS.items():
        if name not in rows or rows[name][3] != unit:
            raise ValueError(f"Missing field or incorrect units: {name}")
        value = rows[name][2]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"Missing/non-numeric value: {name}")
        values[name] = value*factor
        if name != "sky_background" and values[name] <= 0:
            raise ValueError(f"Nonpositive field: {name}")
    for key in ("QE", "T_optics", "albedo_pess", "albedo_nom", "albedo_opt"):
        if values[key] > 1:
            raise ValueError(f"Efficiency/albedo outside physical range: {key}")
    for low, high in (("lambda_min", "lambda_max"), ("FOV_min", "FOV_max"), ("D_ap_min", "D_ap_max")):
        if values[low] >= values[high]:
            raise ValueError(f"Invalid bounds {low}/{high}")
    if rows["phase_model"][2] != "Esfera Lambertiana" or rows["PSF_model"][2] != "Gaussiana":
        raise ValueError("Unsupported phase or PSF model")
    if rows["FWC_low_gain_relation"][2] != ">" or rows["FWC_selection"][2] != "highest_pixel_gain":
        raise ValueError("Unknown full-well convention or gain selection")
    for n, width in (("N_x", "W_x"), ("N_y", "W_y")):
        if values[n] != int(values[n]) or not np.isclose(values[n]*values["p_pixel"], values[width]):
            raise ValueError("Inconsistent detector dimensions")
    if not np.isclose(values["detector_short_dim"], min(values["W_x"], values["W_y"])):
        raise ValueError("Short dimension mismatch")
    book.close()
    return Baseline(values, hashlib.sha256(path.read_bytes()).hexdigest())


def peak_pixel_fraction(streak_length_px, sigma_px):
    """Exact central-pixel integral of Gaussian PSF convolved with a uniform
    horizontal segment. Pixel-centred alignment maximizes peak charge.
    """
    length = np.asarray(streak_length_px, dtype=float)
    if np.any(length < 0) or sigma_px <= 0:
        raise ValueError("Nonnegative streak and positive PSF width required")
    point_axis_fraction = math.erf(.5/(math.sqrt(2)*sigma_px))
    safe = np.maximum(length, 1e-4)
    def primitive(x):
        z = x/sigma_px
        return x*.5*(1+ERF(z/math.sqrt(2)))+sigma_px/np.sqrt(2*np.pi)*np.exp(-.5*z*z)
    along = (primitive(.5+safe/2)-primitive(.5-safe/2)
             -primitive(-.5+safe/2)+primitive(-.5-safe/2))/safe
    along = np.where(length < 1e-4, point_axis_fraction, along)
    return np.clip(along, 0, point_axis_fraction)*point_axis_fraction


@dataclass(frozen=True)
class StudyCase:
    aperture_m: float
    fov_deg: float
    phase_deg: float
    albedo: float
    transverse_speed_m_s: float
    observer_altitude_km: float = 450.

    @property
    def frame_rate_rad_s(self):
        # Circular LVLH at study altitude, not an adopted mission architecture.
        return math.sqrt(398600.4418/(6371+self.observer_altitude_km)**3)


class OpticalModel:
    def __init__(self, baseline):
        self.b = baseline
        wavelength = np.linspace(baseline["lambda_min"], baseline["lambda_max"], 2049)
        temperature, solar_constant = 5772., 1361.
        planck = 2*H*C**2/wavelength**5/np.expm1(H*C/(wavelength*K*temperature))
        irradiance = solar_constant*np.pi*planck/(SIGMA_SB*temperature**4)
        self.solar_photons_m2_s = float(np.trapezoid(irradiance*wavelength/(H*C), wavelength))
        self.ab_zero_photons_m2_s = AB_ZERO/H*math.log(baseline["lambda_max"]/baseline["lambda_min"])

    def derived(self, case):
        if not (case.aperture_m > 0 and 0 < case.fov_deg < 180 and 0 <= case.phase_deg <= 180
                and 0 <= case.albedo <= 1 and case.transverse_speed_m_s >= 0):
            raise ValueError("Invalid study parameters")
        f = self.b["detector_short_dim"]/(2*math.tan(math.radians(case.fov_deg)/2))
        scale = self.b["p_pixel"]/f
        area_eff = np.pi*case.aperture_m**2/4*self.b["T_optics"]*self.b["QE"]
        return f, scale, area_eff

    @staticmethod
    def phase_function(degrees):
        alpha = np.radians(degrees)
        return np.maximum(0., (np.sin(alpha)+(np.pi-alpha)*np.cos(alpha))/np.pi)

    def evaluate(self, case, range_m, diameter_m=None, magnitude_ab=None):
        r = np.asarray(range_m, dtype=float)
        if np.any(r <= 0) or not np.isfinite(r).all():
            raise ValueError("Positive finite distances required")
        if (diameter_m is None) == (magnitude_ab is None):
            raise ValueError("Specify diameter OR equivalent AB magnitude")
        f, scale, area_eff = self.derived(case)
        omega = np.abs(case.transverse_speed_m_s/r-case.frame_rate_rad_s)
        # Maximum overlap of an exposure with a central crossing of the short-axis
        # field. This conditional envelope does not model random arrival times.
        field_span = 2*math.tan(math.radians(case.fov_deg)/2)
        crossing_time = np.divide(field_span, omega, out=np.full_like(omega, np.inf), where=omega > 0)
        visible_time = np.minimum(self.b["t_int"], crossing_time)
        length_px = omega*visible_time/scale
        sigma = self.b["PSF_FWHM"]/(2*np.sqrt(2*np.log(2)))
        pixels = np.ceil(np.minimum(length_px+6*sigma, field_span/scale))*math.ceil(6*sigma)
        fraction = math.erf(3/math.sqrt(2))**2
        if magnitude_ab is not None:
            photons = self.ab_zero_photons_m2_s*10**(-.4*np.asarray(magnitude_ab))
            unresolved = np.ones(np.broadcast_shapes(r.shape, np.shape(magnitude_ab)), dtype=bool)
        else:
            d = np.asarray(diameter_m, dtype=float)
            if np.any(d <= 0) or not np.isfinite(d).all():
                raise ValueError("Positive finite sizes required")
            photons = self.solar_photons_m2_s*case.albedo*(d/(2*r))**2*self.phase_function(case.phase_deg)
            unresolved = d/r <= self.b["PSF_FWHM"]*scale
        total_e = photons*area_eff*visible_time
        signal = total_e*fraction
        background_rate = (self.ab_zero_photons_m2_s*10**(-.4*self.b["sky_background"])
                           *area_eff*(scale*ARCSEC_PER_RAD)**2)
        peak_object_e = total_e*peak_pixel_fraction(length_px, sigma)
        peak_total_e = peak_object_e+(background_rate+self.b["I_dark"])*self.b["t_int"]
        unsaturated = peak_total_e < self.b["FWC_high_gain"]
        variance = signal+pixels*((background_rate+self.b["I_dark"])*self.b["t_int"]+self.b["sigma_read"]**2)
        snr = signal/np.sqrt(variance)
        full_transit = crossing_time >= self.b["t_int"]
        solar_allowed = case.phase_deg <= 180-self.b["sun_exclusion_min"]
        return {"snr": snr, "signal_e": signal, "pixels": pixels, "streak_px": length_px,
                "magnitude_ab": -2.5*np.log10(np.maximum(photons, 1e-300)/self.ab_zero_photons_m2_s),
                "full_transit": full_transit, "unresolved": unresolved,
                "eligible": unresolved & solar_allowed & unsaturated,
                "partial_transit": ~full_transit, "visible_time_s": visible_time,
                "crossing_time_s": crossing_time,
                "unsaturated": unsaturated, "peak_pixel_e": peak_total_e,
                "peak_object_pixel_e": peak_object_e,
                "full_well_e_per_pixel": self.b["FWC_high_gain"],
                "background_e_per_pixel_s": background_rate}

    def transit_lower_range(self, case):
        max_rate = 2*math.tan(math.radians(case.fov_deg)/2)/self.b["t_int"]
        return case.transverse_speed_m_s/(max_rate+case.frame_rate_rad_s)

    def range_intervals(self, case, diameter_m, grid_m):
        """Return every sampled eligible interval, refining both boundaries.

        No assumption of monotone SNR: LVLH cancellation/pixel steps matter.
        Grid endpoints are reported as censored rather than roots.
        """
        grid = np.asarray(grid_m)
        if np.any(np.diff(grid) <= 0):
            raise ValueError("Distance grid must be increasing")
        def good(distance):
            value = self.evaluate(case, distance, diameter_m=diameter_m)
            return bool(value["eligible"] & (value["snr"] >= self.b["SNR_min"]))
        result = self.evaluate(case, grid, diameter_m=diameter_m)
        mask = result["eligible"] & (result["snr"] >= self.b["SNR_min"])
        starts = np.flatnonzero(mask & ~np.r_[False, mask[:-1]])
        ends = np.flatnonzero(mask & ~np.r_[mask[1:], False])
        intervals = []
        for start, end in zip(starts, ends):
            lo, hi = float(grid[start]), float(grid[end])
            for side, a, b in (("lower", grid[max(0, start-1)], grid[start]),
                               ("upper", grid[end], grid[min(len(grid)-1, end+1)])):
                if a == b:
                    continue
                for _ in range(32):
                    mid = (a+b)/2
                    if good(mid) == good(a):
                        a = mid
                    else:
                        b = mid
                if side == "lower": lo = float((a+b)/2)
                else: hi = float((a+b)/2)
            below = self.evaluate(case,lo*(1-1e-6),diameter_m=diameter_m)
            constraints = []
            for key, label in (("unsaturated", "full_well"), ("unresolved", "point_source_domain")):
                if not bool(below[key]): constraints.append(label)
            if float(below["snr"]) < self.b["SNR_min"]: constraints.append("SNR")
            if start == 0: constraints.append("distance_scan_lower_bound")
            intervals.append({"lower_m": lo, "upper_m": hi,
                              "lower_censored": bool(start == 0), "upper_censored": bool(end == len(grid)-1),
                              "lower_constraints": constraints})
        return intervals


def paper_reference(size_m=.1, range_m=100000., speed_m_s=5000., extraction_pixels=10.):
    """Paper §2.1 equations 1–7, plus diagnostic of printed equation 9."""
    focal, f_number, qe, exposure, pixel = .4, 2.8, .61, .025, 12e-6
    aperture = focal/f_number
    power = .4*.3*1361*size_m**2*aperture**2/(8*range_m**2)
    signal = qe*power*exposure/(H*600e12)
    def snr(n): return signal/math.sqrt(signal+n*((.01+.03)*exposure+4.3**2))
    literal = 2.44*speed_m_s*exposure*focal**2/(range_m*aperture*pixel**2)
    return {"power_w": power, "signal_e": signal, "extraction_pixels": extraction_pixels,
            "snr_with_specified_pixels": snr(extraction_pixels),
            "eq9_literal_value_per_m": literal,
            "eq9_times_wavelength_pixels": literal*C/600e12,
            "warning": "Printed Eq.9 lacks a wavelength factor dimensionally; diagnostic is not a reproduction of Fig.2"}
