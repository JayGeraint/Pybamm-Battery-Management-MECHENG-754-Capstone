"""
Error metrics of a reduced model (SPM / SPMe) against the DFN reference.
All comparisons are made on the DFN time grid, over the time span both runs cover.
"""
import numpy as np
import config as cfg


def _interp(t_ref, t, y):
    return np.interp(t_ref, t, y)


def _common(ref, red):
    t_end = min(ref["t"][-1], red["t"][-1])
    mask = ref["t"] <= t_end
    return ref["t"][mask], mask


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def time_to_soc(tr, target):
    idx = np.where(tr["SOC"] >= target)[0]
    return float(tr["t"][idx[0]]) if idx.size else np.nan


def plating_stats(tr):
    phi = tr["phi_sep"]
    t = tr["t"]
    below = phi < cfg.PLATING_THRESHOLD_V
    dt = np.diff(t, prepend=t[0])
    return float(np.min(phi)), float(np.sum(dt[below]))


def single_run_summary(rec):
    """Quantities that describe one run on its own (no comparison)."""
    tr = rec["traces"]
    out = {}
    if tr is None:
        return out
    out["t_end_s"] = float(tr["t"][-1])
    out["Tpeak_C"] = float(np.max(tr["T_C"]))
    out["Q_end_Ah"] = float(abs(tr["Q_dis"][-1]))
    out["SOC_end"] = float(tr["SOC"][-1])
    phi_min, t_below = plating_stats(tr)
    out["phi_sep_min_V"] = phi_min
    out["t_phi_below0_s"] = t_below
    if tr.get("ce_min") is not None:
        out["ce_min"] = float(np.min(tr["ce_min"]))
    if rec["protocol"] == "charge":
        out["t_cc_end_s"] = rec.get("t_cc_end", np.nan)
        t_cc = rec.get("t_cc_end", np.nan)
        out["Q_cc_Ah"] = float(abs(np.interp(t_cc, tr["t"], tr["Q_dis"]))) if np.isfinite(t_cc) else np.nan
        out["t80_s"] = time_to_soc(tr, 0.80)
    return out


def compare(ref_rec, red_rec):
    """Errors of a reduced-model run relative to the DFN run of the same case."""
    out = {}
    ref, red = ref_rec["traces"], red_rec["traces"]
    if ref is None or red is None:
        return out
    t, mask = _common(ref, red)
    V_ref, V_red = ref["V"][mask], _interp(t, red["t"], red["V"])
    T_ref, T_red = ref["T_C"][mask], _interp(t, red["t"], red["T_C"])
    S_ref, S_red = ref["SOC"][mask], _interp(t, red["t"], red["SOC"])
    I_ref, I_red = ref["I"][mask], _interp(t, red["t"], red["I"])

    out["V_rmse_mV"] = 1e3 * rmse(V_ref, V_red)
    out["V_maxerr_mV"] = 1e3 * float(np.max(np.abs(V_ref - V_red)))
    out["T_rmse_K"] = rmse(T_ref, T_red)
    out["Tpeak_err_K"] = float(np.max(red["T_C"]) - np.max(ref["T_C"]))
    out["SOC_maxerr_pct"] = 100 * float(np.max(np.abs(S_ref - S_red)))
    out["I_rmse_A"] = rmse(I_ref, I_red)

    s_ref, s_red = single_run_summary(ref_rec), single_run_summary(red_rec)
    out["phi_sep_min_err_mV"] = 1e3 * (s_red["phi_sep_min_V"] - s_ref["phi_sep_min_V"])
    # does the reduced model see the plating-risk condition that DFN sees?
    ref_risk = s_ref["phi_sep_min_V"] < cfg.PLATING_THRESHOLD_V
    red_risk = s_red["phi_sep_min_V"] < cfg.PLATING_THRESHOLD_V
    out["plating_flag_agree"] = bool(ref_risk == red_risk)
    out["plating_missed"] = bool(ref_risk and not red_risk)

    if ref_rec["protocol"] == "charge":
        t_cc = ref_rec.get("t_cc_end", np.nan)
        m_cc = t <= t_cc
        out["V_rmse_cc_mV"] = 1e3 * rmse(V_ref[m_cc], V_red[m_cc]) if m_cc.any() else np.nan
        for key, name in (("t_cc_end_s", "t_cc_end_err_s"), ("Q_cc_Ah", "Q_cc_err_Ah"),
                          ("t80_s", "t80_err_s"), ("t_end_s", "t_end_err_s"), ("Q_end_Ah", "Q_end_err_Ah")):
            out[name] = s_red[key] - s_ref[key]
        out["t80_err_pct"] = 100 * abs(s_red["t80_s"] - s_ref["t80_s"]) / s_ref["t80_s"]
        out["Q_cc_err_pct"] = 100 * (s_red["Q_cc_Ah"] - s_ref["Q_cc_Ah"]) / s_ref["Q_cc_Ah"]
    if ref_rec["protocol"] == "discharge":
        out["Q_err_pct"] = 100 * (s_red["Q_end_Ah"] - s_ref["Q_end_Ah"]) / s_ref["Q_end_Ah"]
    return out


def classify(err, thresholds):
    """Return 0 = adequate, 1 = marginal, 2 = inadequate (worst metric wins), and the limiting metric."""
    worst, limiting = 0, ""
    for key, (lo, hi) in thresholds.items():
        v = abs(err.get(key, np.nan))
        if not np.isfinite(v):
            continue
        lvl = 0 if v <= lo else (1 if v <= hi else 2)
        if lvl > worst:
            worst, limiting = lvl, key
    return worst, limiting
