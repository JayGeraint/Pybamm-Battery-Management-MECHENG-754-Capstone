"""Shared parameter, SOC, trace and acceptance contracts for the study.

The electrode-window SOC is a beginning-of-life charge-inventory coordinate.
It is not an aged-cell SOC estimator and must not be used with side reactions.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import os
os.environ.setdefault("PYBAMM_DISABLE_TELEMETRY", "true")
import numpy as np
import pandas as pd
import pybamm

TRANSPORT_KEYS = (
    "Negative particle diffusivity [m2.s-1]",
    "Positive particle diffusivity [m2.s-1]",
    "Electrolyte diffusivity [m2.s-1]",
    "Electrolyte conductivity [S.m-1]",
)
VARIANTS = ("Chen2020", "Chen2020_OKane2022_transport")
SOC_DEFINITIONS = ("electrode_window", "nominal_5Ah")


class RunRejected(ValueError):
    def __init__(self, message, category="physical_failure"):
        super().__init__(message)
        self.category = category


def parameters(variant="Chen2020"):
    if variant not in VARIANTS:
        raise ValueError(f"Unknown parameter variant: {variant}")
    p = pybamm.ParameterValues("Chen2020")
    if variant == VARIANTS[1]:
        source = pybamm.ParameterValues("OKane2022")
        p.update({k: source[k] for k in TRANSPORT_KEYS})
    return p


@lru_cache(maxsize=4)
def capacity_basis(variant="Chen2020"):
    p = parameters(variant)
    x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(p)
    qn = float(p.evaluate(pybamm.LithiumIonParameters().n.Q_init))
    qp = float(p.evaluate(pybamm.LithiumIonParameters().p.Q_init))
    q = qn * (x100 - x0)
    if not np.isfinite(q) or q <= 0 or not np.isclose(q, qp * (y0-y100), rtol=1e-6):
        raise ValueError("Invalid or inconsistent electrode-window capacity")
    return {"nominal_capacity_ah": float(p["Nominal cell capacity [A.h]"]),
            "electrode_window_capacity_ah": float(q),
            "x_0": float(x0), "x_100": float(x100),
            "y_0": float(y0), "y_100": float(y100),
            "reference_temperature_k": float(p["Reference temperature [K]"])}


def validate_config(cfg):
    cfg = dict(cfg)
    cfg.setdefault("parameter_variant", "Chen2020")
    cfg.setdefault("soc_definition", "electrode_window")
    if cfg["parameter_variant"] not in VARIANTS or cfg["soc_definition"] not in SOC_DEFINITIONS:
        raise ValueError("Unknown parameter variant or SOC definition")
    for key in ("repeats", "mesh_points", "particle_mesh_points"):
        v = cfg.get(key, cfg["mesh_points"])
        if isinstance(v, bool) or not np.isfinite(v) or int(v) != v or v < 1:
            raise ValueError(f"{key} must be a positive integer")
    for key in ("sample_period_s", "rtol", "atol", "voltage_limit_v", "cv_cutoff_c", "heat_transfer_w_m2_k"):
        if not np.isfinite(cfg[key]) or cfg[key] <= 0:
            raise ValueError(f"{key} must be finite and positive")
    if not np.isfinite(cfg["initial_soc"]) or not 0 < cfg["initial_soc"] < .8:
        raise ValueError("The 10-to-80 style study requires 0 < initial_soc < 0.8")
    for key in ("models", "rates_c", "temperatures_c"):
        if not cfg[key] or len(set(cfg[key])) != len(cfg[key]):
            raise ValueError(f"Empty or duplicate entries in {key}")
    if set(cfg["models"]) - {"SPM", "SPMe", "DFN"} or "DFN" not in cfg["models"]:
        raise ValueError("Select SPM/SPMe/DFN and include the DFN reference")
    if not all(np.isfinite(v) and v > cfg["cv_cutoff_c"] for v in cfg["rates_c"]):
        raise ValueError("Charge rates must be finite and exceed the CV cutoff")
    if not all(np.isfinite(v) and v > -273.15 for v in cfg["temperatures_c"]):
        raise ValueError("Temperatures must be finite and above absolute zero")
    return cfg


def read_trace(path, *, duplicate_policy="reject"):
    """Round-trip floats preserve the two distinct sides of solver switches.

    An exact duplicate requires an explicit keep_last policy. The number removed
    is returned in frame.attrs for the caller to record; no file is overwritten.
    """
    frame = pd.read_csv(path, float_precision="round_trip")
    if len(frame) < 2 or "time_s" not in frame:
        raise ValueError(f"Missing or empty time series: {path}")
    if not np.isfinite(frame.select_dtypes(include="number").to_numpy()).all():
        raise ValueError(f"Nonfinite trace: {path}")
    duplicates = int(frame.time_s.duplicated(keep="last").sum())
    if duplicates:
        if duplicate_policy != "keep_last":
            raise ValueError(f"{duplicates} exact duplicate timestamps: {path}")
        frame = frame.drop_duplicates("time_s", keep="last").reset_index(drop=True)
    if len(frame) < 2 or np.any(np.diff(frame.time_s) <= 0):
        raise ValueError(f"Time must strictly increase: {path}")
    frame.attrs["exact_duplicates_removed"] = duplicates
    return frame


def classify(row):
    required = ("voltage_cc_mv_rmse", "temperature_c_max_abs", "time_to_80_error_s")
    try:
        valid = all(k in row and not isinstance(row[k], (bool, str)) and np.isfinite(row[k]) for k in required)
    except (TypeError, ValueError):
        valid = False
    if not valid:
        return "invalid_metrics"
    if row["voltage_cc_mv_rmse"] < 0 or row["temperature_c_max_abs"] < 0:
        return "invalid_metrics"
    return "adequate" if (row[required[0]] <= 20 and row[required[1]] <= 1
                          and abs(row[required[2]]) <= 60) else "accuracy_failure"


def source_hashes(root=None):
    root = Path(root or __file__).resolve().parent if root is None else Path(root)
    paths = list(root.glob("*.py")) + list((root / "configs").glob("*.json")) + [root / "requirements-lock.txt"]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}


def evidence_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
