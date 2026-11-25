"""
Accuracy sweep: SPM / SPMe / DFN (+ lumped thermal) over
  (1) CC-CV charge   : C-rate x ambient temperature
  (2) CC discharge   : C-rate x ambient temperature
  (3) UDDS drive     : load scale x ambient temperature

Usage (from the src folder):
    python run_sweep.py                  # everything
    python run_sweep.py --only charge    # one protocol
    python run_sweep.py --quick          # 2 x 2 smoke test

Outputs (results/):
    runs_<protocol>.csv        one row per simulation (status, timing, summary numbers)
    errors_<protocol>.csv      one row per reduced-model case: errors vs DFN + adequacy class
    traces_<protocol>.pkl      all time traces (used by make_figures.py and export_matlab.py)
"""
import argparse
import pickle
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import config as cfg
import battery
import metrics

def case_list(protocol, quick=False, h=None):
    if protocol == "charge":
        values, temps = cfg.CHARGE_C_RATES, cfg.AMBIENT_T_C
    elif protocol == "discharge":
        values, temps = cfg.DISCHARGE_C_RATES, cfg.AMBIENT_T_C
    elif protocol == "udds":
        values, temps = cfg.UDDS_SCALES, cfg.UDDS_T_C
    else:
        raise ValueError(protocol)
    if quick:
        values, temps = values[:1] + values[-1:], temps[:1] + temps[-1:]
    return [(m, protocol, v, T, h) for v in values for T in temps for m in cfg.MODELS]


def _worker(args):
    model, protocol, value, T, h = args
    rec = battery.run_case(model, protocol, value, T, h=h)
    return rec


def run_protocol(protocol, quick=False, workers=cfg.N_WORKERS, h=None, tag=""):
    cases = case_list(protocol, quick, h)
    # longest jobs first (DFN, high C / UDDS) for better load balancing
    cases.sort(key=lambda c: (c[0] != "DFN", -c[2]))
    print(f"[{protocol}] {len(cases)} simulations on {workers} workers ...", flush=True)
    t0 = time.time()
    with Pool(workers) as pool:
        recs = []
        for i, rec in enumerate(pool.imap_unordered(_worker, cases), 1):
            recs.append(rec)
            print(f"  {i:3d}/{len(cases)} {rec['model']:5s} v={rec['value']:<4} T={rec['T_amb_C']:>4} "
                  f"{rec['status']:6s} wall={rec.get('wall_s', np.nan):7.2f}s {rec['message'][:60]}", flush=True)
    print(f"[{protocol}] done in {time.time() - t0:.0f} s")

    by_key = {(r["model"], r["value"], r["T_amb_C"]): r for r in recs}
    with open(cfg.RESULTS / f"traces_{protocol}{tag}.pkl", "wb") as f:
        pickle.dump(by_key, f)
    return analyse(protocol, tag)


def analyse(protocol, tag=""):
    """Build runs_<protocol>.csv and errors_<protocol>.csv from the saved traces."""
    path = cfg.RESULTS / f"traces_{protocol}{tag}.pkl"
    if path.exists():
        with open(path, "rb") as f:
            by_key = pickle.load(f)
    else:  # large trace files are shipped gzip-compressed (e.g. traces_charge_h50.pkl.gz)
        import gzip
        with gzip.open(str(path) + ".gz", "rb") as f:
            by_key = pickle.load(f)
    recs = list(by_key.values())
    # -------- per-run table
    rows = []
    for r in recs:
        row = {k: r.get(k) for k in ("model", "protocol", "value", "T_amb_C", "status", "message",
                                     "wall_s", "solve_s", "termination")}
        row.update(metrics.single_run_summary(r))
        rows.append(row)
    runs = pd.DataFrame(rows).sort_values(["value", "T_amb_C", "model"])
    runs.to_csv(cfg.RESULTS / f"runs_{protocol}{tag}.csv", index=False)

    # -------- errors vs DFN
    thresholds = {"charge": cfg.THRESHOLDS_CHARGE, "discharge": cfg.THRESHOLDS_DISCHARGE,
                  "udds": cfg.THRESHOLDS_UDDS}[protocol]
    err_rows = []
    for (m, v, T), r in sorted(by_key.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
        if m == cfg.REFERENCE:
            continue
        ref = by_key[(cfg.REFERENCE, v, T)]
        row = {"model": m, "value": v, "T_amb_C": T, "status": r["status"], "ref_status": ref["status"]}
        if r["status"] == "ok" and ref["status"] == "ok":
            e = metrics.compare(ref, r)
            row.update(e)
            lvl, lim = metrics.classify(e, thresholds)
            # Model breakdown although the solver finished: negative electrolyte concentration
            # (non-physical) or a spurious early voltage cut-off caused by it.
            ce_red = metrics.single_run_summary(r).get("ce_min", np.inf)
            if ce_red < 0:
                lvl, lim = 3, "c_e < 0 (non-physical)"
            if protocol == "discharge" and e.get("Q_err_pct", 0) < -50:
                lvl, lim = 3, "premature cut-off (c_e -> 0)"
            row["class"] = lvl
            row["limiting_metric"] = lim
        elif ref["status"] != "ok":
            row["class"] = np.nan
            row["limiting_metric"] = "DFN failed"
        else:
            row["class"] = 3                    # reduced model failed to solve
            row["limiting_metric"] = "solver failure"
            if r["traces"] is not None:
                row["t_fail_s"] = float(r["traces"]["t"][-1])
        row["speedup_solve"] = (ref.get("solve_s", np.nan) / r["solve_s"]) if r.get("solve_s") else np.nan
        row["speedup_wall"] = (ref.get("wall_s", np.nan) / r["wall_s"]) if r.get("wall_s") else np.nan
        err_rows.append(row)
    errs = pd.DataFrame(err_rows)
    errs.to_csv(cfg.RESULTS / f"errors_{protocol}{tag}.csv", index=False)

    return runs, errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["charge", "discharge", "udds"], default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=cfg.N_WORKERS)
    ap.add_argument("--analyse-only", action="store_true", help="recompute CSV tables from saved traces")
    ap.add_argument("--h", type=float, default=None,
                    help="heat-transfer coefficient [W/m2/K] (default: Chen2020 value, 10); "
                         "outputs get the suffix _h<value>")
    a = ap.parse_args()
    tag = "" if a.h is None else f"_h{a.h:g}"
    for proto in ([a.only] if a.only else ["charge", "discharge", "udds"]):
        if a.analyse_only:
            runs, errs = analyse(proto, tag)
        else:
            runs, errs = run_protocol(proto, quick=a.quick, workers=a.workers, h=a.h, tag=tag)
        cols = [c for c in ["model", "value", "T_amb_C", "status", "V_rmse_mV", "V_rmse_cc_mV",
                            "Tpeak_err_K", "t80_err_pct", "Q_err_pct", "class", "limiting_metric"]
                if c in errs.columns]
        print(errs[cols].to_string(index=False))
