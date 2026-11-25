"""
Parameters, models, load protocols and a single-case simulation runner.

Every simulation in the project goes through `run_case()`, which returns a
dictionary of time traces plus timing / status information, so that the
sweep, the timing benchmark, the mesh check and the validation all use exactly
the same model set-up.
"""
import time
import numpy as np
import pandas as pd
import pybamm

# Arrhenius versions of the Chen2020 transport functions (shipped in PyBaMM's OKane2022 set,
# same reference values as Chen2020, activation energies from Ecker 2015 / Cabanero 2018).
from pybamm.input.parameters.lithium_ion.OKane2022 import (
    graphite_LGM50_diffusivity_Chen2020,
    nmc_LGM50_diffusivity_Chen2020,
    electrolyte_diffusivity_Nyman2008_arrhenius,
    electrolyte_conductivity_Nyman2008_arrhenius,
)

import config as cfg

pybamm.set_logging_level("ERROR")

MODEL_CLASSES = {
    "SPM": pybamm.lithium_ion.SPM,
    "SPMe": pybamm.lithium_ion.SPMe,
    "DFN": pybamm.lithium_ion.DFN,
}


# ============================================================================
# Parameters
# ============================================================================
def get_parameters(T_amb_C=25.0, T_init_C=None, h=None):
    """Chen2020 (LG M50) with temperature dependence added.

    Chen2020 alone already has Arrhenius exchange-current densities, but its
    particle and electrolyte diffusivities / conductivity are temperature-
    independent, which would make an ambient-temperature sweep meaningless.
    We therefore swap in the Arrhenius versions of the *same* functions.
    """
    p = pybamm.ParameterValues("Chen2020")
    p.update({
        "Negative particle diffusivity [m2.s-1]": graphite_LGM50_diffusivity_Chen2020,
        "Positive particle diffusivity [m2.s-1]": nmc_LGM50_diffusivity_Chen2020,
        "Electrolyte diffusivity [m2.s-1]": electrolyte_diffusivity_Nyman2008_arrhenius,
        "Electrolyte conductivity [S.m-1]": electrolyte_conductivity_Nyman2008_arrhenius,
    })
    T_amb = T_amb_C + 273.15
    T_init = (T_amb_C if T_init_C is None else T_init_C) + 273.15
    p.update({"Ambient temperature [K]": T_amb, "Initial temperature [K]": T_init})
    if h is not None:
        p.update({"Total heat transfer coefficient [W.m-2.K-1]": h})
    return p


def build_model(name, thermal=cfg.THERMAL):
    return MODEL_CLASSES[name]({"thermal": thermal})


def make_solver():
    return pybamm.IDAKLUSolver(rtol=cfg.RTOL, atol=cfg.ATOL)


# ============================================================================
# Load protocols
# ============================================================================
def cccv_experiment(c_rate):
    return pybamm.Experiment(
        [(f"Charge at {c_rate}C until {cfg.V_MAX} V",
          f"Hold at {cfg.V_MAX} V until {cfg.CV_CUTOFF}")],
        period=f"{cfg.CHARGE_PERIOD_S} seconds",
    )


def cc_discharge_experiment(c_rate):
    return pybamm.Experiment(
        [f"Discharge at {c_rate}C until {cfg.V_MIN} V"],
        period=f"{cfg.DISCHARGE_PERIOD_S} seconds",
    )


def load_udds(scale=1.0, repeats=cfg.UDDS_REPEATS, dt=cfg.UDDS_DT_S):
    """Course UDDS profile (PEC format: negative = discharge, 5.4 Ah cell).

    Returns time [s] and current [A] in the PyBaMM sign convention
    (positive = discharge), rescaled to the 5 Ah cell and repeated.
    """
    raw = pd.read_csv(cfg.UDDS_CSV, skiprows=4, header=None).iloc[:, :2]
    raw = raw.apply(pd.to_numeric, errors="coerce").dropna().values
    t_raw, i_raw = raw[:, 0], -raw[:, 1] * (cfg.NOMINAL_CAPACITY_AH / 5.4)
    t1 = np.arange(0.0, t_raw[-1] + 1e-9, dt)
    i1 = np.interp(t1, t_raw, i_raw)
    period = t1[-1] + dt
    t = np.concatenate([t1 + k * period for k in range(repeats)])
    i = np.tile(i1, repeats) * scale
    return t, i


def load_m50t(path, dt=1.0):
    """Measured LG M50T data: Time (s), Voltage (V), Current (mA), Charge (mA.h), Temperature (degC)."""
    d = pd.read_csv(path)
    t = d["Time (s)"].values - d["Time (s)"].values[0]
    tg = np.arange(0.0, t[-1], dt)
    out = {
        "t": tg,
        "I": np.interp(tg, t, -d["Current (mA)"].values / 1000.0),   # +ve = discharge
        "V": np.interp(tg, t, d["Voltage (V)"].values),
        "T_C": np.interp(tg, t, d["Temperature (degC)"].values),
        "Q_Ah": np.interp(tg, t, d["Charge (mA.h)"].values / 1000.0),
    }
    return out


# ============================================================================
# Output extraction
# ============================================================================
def _safe(sol, name):
    try:
        return np.asarray(sol[name].entries)
    except Exception:
        return None


def extract_traces(sol, soc0):
    t = _safe(sol, "Time [s]")
    I = _safe(sol, "Current [A]")
    Q = _safe(sol, "Discharge capacity [A.h]")
    tr = {
        "t": t,
        "V": _safe(sol, "Voltage [V]"),
        "I": I,                                                   # +ve = discharge
        "Q_dis": Q,                                               # Ah discharged (negative while charging)
        "SOC": soc0 - Q / cfg.NOMINAL_CAPACITY_AH,
        "T_C": _safe(sol, "X-averaged cell temperature [K]") - 273.15,
        "phi_sep": _safe(sol, "Negative electrode surface potential difference at separator interface [V]"),
        "phi_n_avg": _safe(sol, "X-averaged negative electrode surface potential difference [V]"),
        "ce_min": None,
        "Q_ohm": _safe(sol, "Volume-averaged Ohmic heating [W.m-3]"),
        "Q_irr": _safe(sol, "Volume-averaged irreversible electrochemical heating [W.m-3]"),
        "Q_tot": _safe(sol, "Volume-averaged total heating [W.m-3]"),
    }
    ce = _safe(sol, "Electrolyte concentration [mol.m-3]")
    if ce is not None:
        tr["ce_min"] = ce.min(axis=0) if ce.ndim == 2 else ce
    # flatten scalar-in-time variables that come back as (1, nt)
    for k, v in tr.items():
        if isinstance(v, np.ndarray) and v.ndim > 1 and min(v.shape) == 1:
            tr[k] = v.ravel()
    return tr


def extract_profiles(sol, times):
    """Spatial profiles (for the gradient / electrolyte depletion figures) at given times."""
    out = {}
    try:
        x_n = sol["Negative electrode surface potential difference [V]"]
        x_e = sol["Electrolyte concentration [mol.m-3]"]
        xn = sol["x_n [m]"].entries[:, 0] * 1e6
        xe = sol["x [m]"].entries[:, 0] * 1e6
        out["x_n_um"] = xn
        out["x_um"] = xe
        out["times"] = np.array(times)
        out["phi_n"] = np.array([x_n(t=tt, x=xn * 1e-6) for tt in times])    # (nt, nx_n)
        out["c_e"] = np.array([x_e(t=tt, x=xe * 1e-6) for tt in times])      # (nt, nx)
    except Exception as exc:                                   # noqa: BLE001
        out["error"] = str(exc)
    return out


# ============================================================================
# Single case runner
# ============================================================================
def run_case(model_name, protocol, value, T_amb_C, var_pts=None, profile_times=None,
             h=None, keep_solution=False, udds_repeats=None):
    """Run one simulation.

    protocol : "charge" (value = C-rate), "discharge" (value = C-rate),
               "udds" (value = current scale), "measured" (value = dict from load_m50t)
    Returns dict with traces, timing and status.
    """
    rec = {"model": model_name, "protocol": protocol, "T_amb_C": T_amb_C,
           "value": value if protocol != "measured" else np.nan,
           "status": "ok", "message": ""}
    model = build_model(model_name)
    solver = make_solver()
    vp = var_pts or cfg.VAR_PTS

    t_wall0 = time.perf_counter()
    try:
        if protocol == "charge":
            soc0 = cfg.CHARGE_SOC0
            p = get_parameters(T_amb_C, h=h)
            sim = pybamm.Simulation(model, parameter_values=p, experiment=cccv_experiment(value),
                                    solver=solver, var_pts=vp)
            sol = sim.solve(initial_soc=soc0)
        elif protocol == "discharge":
            soc0 = cfg.DISCHARGE_SOC0
            p = get_parameters(T_amb_C, h=h)
            sim = pybamm.Simulation(model, parameter_values=p, experiment=cc_discharge_experiment(value),
                                    solver=solver, var_pts=vp)
            sol = sim.solve(initial_soc=soc0)
        elif protocol == "udds":
            soc0 = cfg.UDDS_SOC0
            t_d, i_d = load_udds(scale=value, repeats=udds_repeats or cfg.UDDS_REPEATS)
            p = get_parameters(T_amb_C, h=h)
            p.update({"Current function [A]": pybamm.Interpolant(t_d, i_d, pybamm.t, interpolator="linear"),
                      "Upper voltage cut-off [V]": cfg.UDDS_V_MAX_EVENT})
            sim = pybamm.Simulation(model, parameter_values=p, solver=solver, var_pts=vp)
            sol = sim.solve([0, t_d[-1]], t_interp=t_d, initial_soc=soc0)
        elif protocol == "measured":
            data = value
            soc0 = float(data.get("soc0", 1.0))      # 1.0 = start from fully charged (discharge tests)
            p = get_parameters(T_amb_C, T_init_C=float(data["T_C"][0]), h=h)
            p.update({"Current function [A]": pybamm.Interpolant(data["t"], data["I"], pybamm.t,
                                                                 interpolator="linear"),
                      "Lower voltage cut-off [V]": 2.4})
            sim = pybamm.Simulation(model, parameter_values=p, solver=solver, var_pts=vp)
            sol = sim.solve([0, data["t"][-1]], t_interp=data["t"], initial_soc=soc0)
        else:
            raise ValueError(protocol)
    except Exception as exc:                                   # noqa: BLE001
        rec.update(status="failed", message=f"{type(exc).__name__}: {exc}"[:300],
                   wall_s=time.perf_counter() - t_wall0)
        rec["traces"] = None
        return rec
    rec["wall_s"] = time.perf_counter() - t_wall0               # setup + discretisation + solve
    rec["solve_s"] = float(sol.solve_time.value)                # integration only
    rec["termination"] = str(getattr(sol, "termination", ""))
    tr = extract_traces(sol, soc0)
    rec["traces"] = tr

    # A solver failure inside an experiment step does not raise: detect it.
    if protocol == "charge":
        steps = sol.cycles[0].steps if sol.cycles and sol.cycles[0] is not None else []
        # Expected: CV ends at |I| = C/20 (= 0.25 A).  Allow the small overshoot of the event.
        finished_cv = len(steps) >= 2 and abs(tr["I"][-1]) <= cfg.NOMINAL_CAPACITY_AH / 20 * 1.05
        if not finished_cv:
            rec.update(status="failed",
                       message=f"stopped at t={tr['t'][-1]:.0f} s before end of CV (solver failure)")
        rec["t_cc_end"] = float(steps[0]["Time [s]"].entries[-1]) if steps else np.nan
    elif protocol == "discharge":
        if tr["V"][-1] > cfg.V_MIN + 0.02:
            rec.update(status="failed", message=f"stopped at t={tr['t'][-1]:.0f} s, V={tr['V'][-1]:.3f} V")
    elif protocol in ("udds", "measured"):
        t_end_expected = (load_udds(scale=value, repeats=udds_repeats or cfg.UDDS_REPEATS)[0][-1] if protocol == "udds" else value["t"][-1])
        if tr["t"][-1] < t_end_expected - 1 and protocol == "udds":
            rec.update(status="failed", message=f"stopped at t={tr['t'][-1]:.0f} s ({rec['termination']})")
    if profile_times is not None:
        pt = [min(tt, tr["t"][-1]) for tt in profile_times]
        rec["profiles"] = extract_profiles(sol, pt)
    if keep_solution:
        rec["solution"] = sol
    return rec
