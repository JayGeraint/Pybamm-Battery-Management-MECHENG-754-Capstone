"""
Export all simulation traces to MATLAB .mat files (results/matlab/), so the
results can be post-processed with the MATLAB scripts in ../matlab/.

Each file holds a struct array `runs` with fields
    model, protocol, value (C-rate or UDDS scale), T_amb_C, status, message,
    wall_s, solve_s, t, V, I, T_C, SOC, Q_dis, phi_sep, ce_min
(signals are column vectors; current is + for discharge, as in PyBaMM)
"""
import pickle
import numpy as np
import pandas as pd
from scipy.io import savemat

import config as cfg

FIELDS = ["t", "V", "I", "T_C", "SOC", "Q_dis", "phi_sep", "ce_min"]


def _struct(rec):
    s = {"model": rec["model"], "protocol": rec["protocol"], "value": float(rec["value"]),
         "T_amb_C": float(rec["T_amb_C"]), "status": rec["status"], "message": rec.get("message", ""),
         "wall_s": float(rec.get("wall_s") or np.nan), "solve_s": float(rec.get("solve_s") or np.nan)}
    tr = rec.get("traces")
    for f in FIELDS:
        v = None if tr is None else tr.get(f)
        s[f] = np.asarray(v, dtype=float).reshape(-1, 1) if v is not None else np.zeros((0, 1))
    return s


def main():
    out = cfg.RESULTS / "matlab"
    out.mkdir(exist_ok=True)
    for proto in ("charge", "discharge", "udds"):
        p = cfg.RESULTS / f"traces_{proto}.pkl"
        if not p.exists():
            continue
        with open(p, "rb") as f:
            recs = pickle.load(f)
        keys = sorted(recs, key=lambda k: (k[1], k[2], cfg.MODELS.index(k[0])))
        # a 1xN struct array in MATLAB
        dt = [(f, object) for f in _struct(recs[keys[0]]).keys()]
        sa = np.empty((1, len(keys)), dtype=dt)
        for i, k in enumerate(keys):
            for f, v in _struct(recs[k]).items():
                sa[0, i][f] = v
        savemat(out / f"traces_{proto}.mat", {"runs": sa}, do_compression=True)
        print("wrote", out / f"traces_{proto}.mat", len(keys), "runs")

    # ---- numeric grids for the adequacy maps (no readtable needed in MATLAB)
    maps = {}
    for proto, values, temps, vcol in (("charge", cfg.CHARGE_C_RATES, cfg.AMBIENT_T_C, "V_rmse_cc_mV"),
                                       ("discharge", cfg.DISCHARGE_C_RATES, cfg.AMBIENT_T_C, "V_rmse_mV")):
        f = cfg.RESULTS / f"errors_{proto}.csv"
        if not f.exists():
            continue
        e = pd.read_csv(f)
        g = {"Crate": np.array(values, float).reshape(-1, 1), "T_amb_C": np.array(temps, float).reshape(1, -1),
             "class_legend": "0 adequate, 1 marginal, 2 inadequate, 3 model breakdown; rows = C-rate, cols = T"}
        for m in ("SPM", "SPMe"):
            for col, name in (("class", "class"), (vcol, "Vrmse_mV"), ("Tpeak_err_K", "Tpeak_err_K"),
                              ("t80_err_pct", "t80_err_pct"), ("Q_err_pct", "Q_err_pct"),
                              ("phi_sep_min_err_mV", "phi_sep_min_err_mV")):
                if col not in e.columns:
                    continue
                Z = np.full((len(values), len(temps)), np.nan)
                for i, v in enumerate(values):
                    for j, T in enumerate(temps):
                        row = e[(e.model == m) & np.isclose(e.value, v) & np.isclose(e.T_amb_C, T)]
                        if len(row):
                            Z[i, j] = row[col].values[0]
                g[f"{name}_{m}"] = Z
        r = pd.read_csv(cfg.RESULTS / f"runs_{proto}.csv")
        for col, name in (("phi_sep_min_V", "phi_sep_min_V"), ("Tpeak_C", "Tpeak_C"), ("ce_min", "ce_min")):
            Z = np.full((len(values), len(temps)), np.nan)
            for i, v in enumerate(values):
                for j, T in enumerate(temps):
                    row = r[(r.model == "DFN") & np.isclose(r.value, v) & np.isclose(r.T_amb_C, T)]
                    if len(row):
                        Z[i, j] = row[col].values[0]
            g[f"{name}_DFN"] = Z
        maps[proto] = g
    if maps:
        savemat(out / "adequacy_maps.mat", maps, do_compression=True)
        print("wrote", out / "adequacy_maps.mat")
    f = cfg.RESULTS / "benchmark_summary.csv"
    if f.exists():
        b = pd.read_csv(f)
        savemat(out / "benchmark.mat", {"bench": {c: (b[c].values.reshape(-1, 1) if b[c].dtype != object
                                                      else np.array(b[c].astype(str).tolist(), dtype=object).reshape(-1, 1))
                                                  for c in b.columns}}, do_compression=True)
        print("wrote", out / "benchmark.mat")

    p = cfg.RESULTS / "validation_traces.pkl"
    if p.exists():
        with open(p, "rb") as f:
            st = pickle.load(f)
        val = {}
        for j, (name, d) in enumerate(st.items()):
            key = "C10" if "C/10" in name else "pulse"
            entry = {"name": name, "data_t": d["data"]["t"].reshape(-1, 1), "data_I": d["data"]["I"].reshape(-1, 1),
                     "data_V": d["data"]["V"].reshape(-1, 1), "data_T_C": d["data"]["T_C"].reshape(-1, 1),
                     "data_Q_Ah": d["data"]["Q_Ah"].reshape(-1, 1)}
            for m in cfg.MODELS:
                r = d.get(m)
                if r and r["traces"] is not None:
                    entry[m] = {f: np.asarray(r["traces"][f], float).reshape(-1, 1) for f in ("t", "V", "T_C", "Q_dis")}
            val[key] = entry
        savemat(out / "validation.mat", val, do_compression=True)
        print("wrote", out / "validation.mat")


if __name__ == "__main__":
    main()
