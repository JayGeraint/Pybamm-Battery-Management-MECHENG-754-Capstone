"""Reproducible CC-CV model comparison. All outputs are simulations, not cell tests.

Positive current denotes discharge. DFN is a numerical reference, not ground truth.
Dependencies are pinned in requirements-lock.txt. Run --help for entry points.
"""
from __future__ import annotations
import os
os.environ.setdefault("PYBAMM_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import pybamm
from study_contract import (parameters, capacity_basis, validate_config, classify,
                            RunRejected, source_hashes)

VARIABLES = {
    "voltage_v": "Voltage [V]",
    "current_a": "Current [A]",
    "temperature_k": "Volume-averaged cell temperature [K]",
    "discharge_capacity_ah": "Discharge capacity [A.h]",
    "anode_mean_v": "X-averaged negative electrode surface potential difference [V]",
    "anode_separator_v": "Negative electrode surface potential difference at separator interface [V]",
}


def environment():
    return {"python": sys.version, "platform": platform.platform(),
            "processor": platform.processor(), "logical_cpu_count": os.cpu_count(),
            "packages": {n: importlib.metadata.version(n) for n in
                         ["pybamm", "pybammsolvers", "numpy", "scipy", "pandas", "matplotlib"]},
            "threads": {n: os.environ.get(n) for n in
                        ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]}}


def make_sim(model_name, rate, temp, cfg, mesh=None, solver=None):
    model = getattr(pybamm.lithium_ion, model_name)(
        {"thermal": "lumped", "cell geometry": "arbitrary"})
    params = parameters(cfg.get("parameter_variant", "Chen2020"))
    params.update({"Ambient temperature [K]": temp + 273.15,
                   "Initial temperature [K]": temp + 273.15,
                   "Total heat transfer coefficient [W.m-2.K-1]": cfg["heat_transfer_w_m2_k"]})
    n = mesh or cfg["mesh_points"]
    nr = int(n * cfg.get("particle_mesh_points", cfg["mesh_points"]) / cfg["mesh_points"])
    points = {"x_n": n, "x_s": n, "x_p": n, "r_n": nr, "r_p": nr}
    # Explicit generous limits; completion is checked against event termination.
    experiment = pybamm.Experiment([(
        f"Charge at {rate} C for {max(2 / rate, 1):g} hours or until {cfg['voltage_limit_v']} V",
        f"Hold at {cfg['voltage_limit_v']} V for 4 hours or until {cfg['cv_cutoff_c']} C",
    )], period=f"{cfg['sample_period_s']} seconds")
    if solver is None:
        solver = pybamm.IDAKLUSolver(rtol=cfg["rtol"], atol=cfg["atol"],
                                   options={"num_threads": 1})
    sim = pybamm.Simulation(model, parameter_values=params, experiment=experiment,
                            var_pts=points, solver=solver)
    return sim


def extract(sol, cfg):
    min_ce = float(np.min(sol["Electrolyte concentration [mol.m-3]"].entries))
    if not np.isfinite(min_ce) or min_ce <= 0:
        raise RunRejected(f"Nonphysical electrolyte concentration: minimum {min_ce:g} mol/m3")
    t = np.asarray(sol.t)
    # Preserve both sides of a switch in raw solver output; drop exact duplicates.
    t = np.unique(t)
    data = {"time_s": t}
    for col, var in VARIABLES.items():
        data[col] = np.asarray(sol[var](t)).reshape(-1)
    data["temperature_c"] = data["temperature_k"] - 273.15
    basis = capacity_basis(cfg.get("parameter_variant", "Chen2020"))
    data["soc_nominal"] = cfg["initial_soc"] - data["discharge_capacity_ah"] / basis["nominal_capacity_ah"]
    data["soc_electrode_window"] = cfg["initial_soc"] - data["discharge_capacity_ah"] / basis["electrode_window_capacity_ah"]
    data["soc"] = data["soc_nominal" if cfg.get("soc_definition") == "nominal_5Ah" else "soc_electrode_window"]
    data["charge_added_ah"] = -data["discharge_capacity_ah"]
    frame = pd.DataFrame(data)
    if not np.isfinite(frame.to_numpy()).all():
        raise RunRejected("Non-finite model output")
    if np.any(np.diff(t) <= 0):
        raise RunRejected("Time is not strictly increasing", "protocol_failure")
    if frame.current_a.max() > 1e-6:
        raise RunRejected("Expected charge-negative current", "protocol_failure")
    if frame.voltage_v.max() > cfg["voltage_limit_v"] + 0.002:
        raise RunRejected("Voltage limit exceeded by more than numerical allowance", "protocol_failure")
    steps = sol.cycles[0].steps
    if len(steps) != 2 or any(s is None for s in steps):
        raise RunRejected("Expected completed CC and CV steps", "protocol_failure")
    if not all(str(s.termination).startswith("event:") for s in steps):
        raise RunRejected("Charge reached a time limit or an unexpected termination: "
                          + str([s.termination for s in steps]), "protocol_failure")
    if abs(frame.current_a.iloc[-1] + cfg["cv_cutoff_c"] * basis["nominal_capacity_ah"]) > 0.005:
        raise RunRejected("CV current cutoff was not reached", "protocol_failure")
    return frame, float(steps[0].t[-1]), [s.termination for s in steps]


def time_to_soc(frame, target, column="soc"):
    s = frame[column].to_numpy()
    if not np.isfinite(target) or not np.isfinite(s).all() or np.any(np.diff(s) < -1e-10):
        raise ValueError("SOC target and charge trajectory must be finite and monotonic")
    if target > s.max() or target < s.min():
        return float("nan")
    return float(np.interp(target, s, frame.time_s))


def run_one(name, rate, temp, cfg, mesh=None):
    start = time.perf_counter()
    sim = make_sim(name, rate, temp, cfg, mesh)
    sim.build_for_experiment(initial_soc=cfg["initial_soc"])
    build_s = time.perf_counter() - start
    start = time.perf_counter()
    sol = sim.solve(initial_soc=cfg["initial_soc"], calc_esoh=False)
    cold_s = time.perf_counter() - start
    # Reject incomplete or physically inadmissible first solves before timing repeats.
    extract(sol, cfg)
    timings, integrator = [], []
    # Reuse the built simulation; no starting_solution, so every run starts fresh.
    for _ in range(cfg["repeats"]):
        start = time.perf_counter()
        sol = sim.solve(initial_soc=cfg["initial_soc"], calc_esoh=False)
        timings.append(time.perf_counter() - start)
        integrator.append(float(sol.solve_time.value))
    frame, cc_end, terminations = extract(sol, cfg)
    meta = {"model": name, "rate_c": rate, "ambient_c": temp,
            "parameter_variant": cfg.get("parameter_variant", "Chen2020"),
            "soc_definition": cfg.get("soc_definition", "electrode_window"),
            "electrode_window_capacity_ah": capacity_basis(cfg.get("parameter_variant", "Chen2020"))["electrode_window_capacity_ah"],
            "run_category": "completed", "physical_checks_passed": True,
            "mesh_points": mesh or cfg["mesh_points"], "status": "ok",
            "particle_mesh_points": int((mesh or cfg["mesh_points"]) * cfg.get("particle_mesh_points",cfg["mesh_points"]) / cfg["mesh_points"]),
            "minimum_electrolyte_mol_m3": float(np.min(sol["Electrolyte concentration [mol.m-3]"].entries)),
            "build_s": build_s, "first_solve_wall_s": cold_s,
            "warm_solve_wall_median_s": float(np.median(timings)),
            "warm_solve_wall_q25_s": float(np.quantile(timings, .25)),
            "warm_solve_wall_q75_s": float(np.quantile(timings, .75)),
            "integrator_median_s": float(np.median(integrator)),
            "warm_repeats_s": timings, "cc_end_s": cc_end,
            "charge_end_s": float(frame.time_s.iloc[-1]),
            "time_to_80_soc_s": time_to_soc(frame, .8),
            "time_to_80_nominal_soc_s": time_to_soc(frame, .8, "soc_nominal"),
            "time_to_80_electrode_window_soc_s": time_to_soc(frame, .8, "soc_electrode_window"),
            "charge_added_ah": float(frame.charge_added_ah.iloc[-1]),
            "peak_temperature_c": float(frame.temperature_c.max()),
            "min_anode_mean_v": float(frame.anode_mean_v.min()),
            "min_anode_separator_v": float(frame.anode_separator_v.min()),
            "terminations": terminations}
    return frame, meta


def error_on_grid(a, b, column, end, dt=2):
    if not np.isfinite(end) or end <= 0 or not np.isfinite(dt) or dt <= 0:
        raise ValueError("No common time interval")
    for f in (a, b):
        if len(f) < 2 or not np.isfinite(f[["time_s", column]].to_numpy()).all():
            raise ValueError("Nonfinite or empty comparison data")
        if np.any(np.diff(f.time_s) <= 0) or f.time_s.iloc[0] > 0 or f.time_s.iloc[-1] < end:
            raise ValueError("Comparison would require unordered data or extrapolation")
    grid = np.unique(np.r_[np.arange(0, end, dt), end])
    err = np.interp(grid, a.time_s, a[column]) - np.interp(grid, b.time_s, b[column])
    return float(np.sqrt(np.mean(err**2))), float(np.max(np.abs(err)))


def compare(frame, reference, meta, refmeta, cfg):
    # Voltage in CV is controller-imposed. Primary voltage metric is common CC.
    cc = min(meta["cc_end_s"], refmeta["cc_end_s"])
    end = min(meta["charge_end_s"], refmeta["charge_end_s"])
    row = {"model": meta["model"], "rate_c": meta["rate_c"], "ambient_c": meta["ambient_c"],
           "parameter_variant": cfg.get("parameter_variant", "Chen2020"),
           "soc_definition": cfg.get("soc_definition", "electrode_window"),
           "cc_common_end_s": cc, "full_common_end_s": end}
    for col, label, scale, limit in [
        ("voltage_v", "voltage_cc_mv", 1000, cc),
        ("voltage_v", "voltage_full_mv", 1000, end),
        ("temperature_c", "temperature_c", 1, end),
        ("current_a", "current_a", 1, end),
        ("anode_mean_v", "anode_mean_mv", 1000, end),
        ("anode_separator_v", "anode_separator_mv", 1000, end),
    ]:
        rmse, maximum = error_on_grid(frame, reference, col, limit, cfg["sample_period_s"])
        row[label + "_rmse"] = rmse * scale
        row[label + "_max_abs"] = maximum * scale
    row.update({
        "cc_end_error_s": meta["cc_end_s"] - refmeta["cc_end_s"],
        "charge_end_error_s": meta["charge_end_s"] - refmeta["charge_end_s"],
        "time_to_80_error_s": meta["time_to_80_soc_s"] - refmeta["time_to_80_soc_s"],
        "time_to_80_error_pct": 100 * (meta["time_to_80_soc_s"] / refmeta["time_to_80_soc_s"] - 1),
        "peak_temperature_error_c": meta["peak_temperature_c"] - refmeta["peak_temperature_c"],
        "charge_added_error_ah": meta["charge_added_ah"] - refmeta["charge_added_ah"],
        "charge_added_error_pct": 100 * (meta["charge_added_ah"] / refmeta["charge_added_ah"] - 1),
        "warm_wall_speedup": refmeta["warm_solve_wall_median_s"] / meta["warm_solve_wall_median_s"],
        "warm_wall_saved_pct": 100 * (1 - meta["warm_solve_wall_median_s"] / refmeta["warm_solve_wall_median_s"]),
    })
    # Project screening thresholds, not a standard or safety criterion.
    row["accuracy_category"] = classify(row)
    row["meets_project_screen"] = row["accuracy_category"] == "adequate"
    return row


def slug(rate, temp, name):
    return f"{name}_{rate:g}C_{temp:g}degC"


def run_sweep(cfg, out):
    traces = out / "traces"
    traces.mkdir(parents=True)
    summaries, comparisons, failures = [], [], []
    for temp in cfg["temperatures_c"]:
        for rate in cfg["rates_c"]:
            results = {}
            for name in cfg["models"]:
                key = slug(rate, temp, name)
                print("Running", key, flush=True)
                try:
                    frame, meta = run_one(name, rate, temp, cfg)
                    results[name] = (frame, meta)
                    frame.to_csv(traces / (key + ".csv"), index=False)
                    summaries.append(meta)
                    print(f"  CC {meta['cc_end_s']:.1f}s; Tpeak {meta['peak_temperature_c']:.2f}C; "
                          f"warm wall {meta['warm_solve_wall_median_s']:.3f}s", flush=True)
                except Exception as exc:
                    failure = {"case": key, "model": name, "rate_c": rate,
                               "ambient_c": temp, "status": "failed", "error": repr(exc),
                               "run_category": getattr(exc, "category", "solver_or_execution_failure"),
                               "parameter_variant": cfg.get("parameter_variant", "Chen2020"),
                               "soc_definition": cfg.get("soc_definition", "electrode_window")}
                    failures.append(failure)
                    summaries.append(failure)
                    print("  FAILED", repr(exc), flush=True)
                pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
                (out / "failures.json").write_text(json.dumps(failures, indent=2))
            if "DFN" in results:
                ref, rm = results["DFN"]
                for name in results:
                    if name != "DFN":
                        f, m = results[name]
                        comparisons.append(compare(f, ref, m, rm, cfg))
            pd.DataFrame(comparisons).to_csv(out / "comparisons.csv", index=False)
    return failures


def convergence(cfg, out):
    # Three refinement levels at baseline and the cold, high-rate corner.
    rows = []
    for rate, temp in [(1., 25.), (3., 10.)]:
        local = dict(cfg, repeats=1)
        results = {}
        for n in [20, 40, 80]:
            print(f"Convergence DFN {rate}C {temp}C mesh={n}", flush=True)
            frame, meta = run_one("DFN", rate, temp, local, n)
            results[n] = (frame, meta)
            frame.to_csv(out / f"dfn_{rate:g}C_{temp:g}degC_n{n}.csv", index=False)
        for coarse, fine in [(20, 40), (40, 80)]:
            a, am = results[coarse]
            b, bm = results[fine]
            row = compare(a, b, am, bm, cfg)
            end = min(am["charge_end_s"], bm["charge_end_s"])
            _, sepmax = error_on_grid(a, b, "anode_separator_v", end)
            row.update(coarse=coarse, fine=fine, separator_max_abs_mv=sepmax * 1000)
            row["passes_numerical_screen"] = bool(row["voltage_cc_mv_max_abs"] < 2
                and row["temperature_c_max_abs"] < .1 and abs(row["cc_end_error_s"]) < 2
                and row["separator_max_abs_mv"] < 2)
            rows.append(row)
        # Tighten tolerances at production mesh, isolate solver sensitivity.
        tight_cfg = dict(local, rtol=1e-8, atol=1e-10)
        tight, tm = run_one("DFN", rate, temp, tight_cfg, 40)
        a, am = results[40]
        row = compare(a, tight, am, tm, cfg)
        row.update(coarse="tol_default", fine="tol_tight", separator_max_abs_mv=
                   error_on_grid(a, tight, "anode_separator_v", min(am["charge_end_s"],tm["charge_end_s"]))[1]*1000)
        row["passes_numerical_screen"] = bool(row["voltage_cc_mv_max_abs"] < 2
            and row["temperature_c_max_abs"] < .1 and abs(row["cc_end_error_s"]) < 2
            and row["separator_max_abs_mv"] < 2)
        rows.append(row)
        pd.DataFrame(rows).to_csv(out / "convergence.csv", index=False)
    # Coarse-to-production rows are informative. Production-to-fine and tightened
    # solver tolerances are the acceptance checks for the production configuration.
    return [r for r in rows if str(r["coarse"]) != "20" and not r["passes_numerical_screen"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.json"))
    parser.add_argument("--out", type=Path, required=True, help="New output folder (existing folders refused)")
    parser.add_argument("--convergence", action="store_true")
    args = parser.parse_args()
    cfg = validate_config(json.loads(args.config.read_text()))
    if args.out.exists():
        raise FileExistsError(f"Choose a new output folder to preserve results: {args.out}")
    args.out.mkdir(parents=True)
    (args.out / "config.json").write_text(json.dumps(cfg, indent=2))
    provenance = environment()
    provenance["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    provenance["source_sha256"] = source_hashes()
    provenance["capacity_basis"] = capacity_basis(cfg["parameter_variant"])
    provenance["source_type"] = "model_simulation; DFN numerical reference; no experimental validation"
    (args.out / "environment.json").write_text(json.dumps(provenance, indent=2))
    problems = convergence(cfg, args.out) if args.convergence else run_sweep(cfg, args.out)
    (args.out / "run_status.json").write_text(json.dumps({"execution_complete": True,
        "all_cases_passed": not problems, "problem_count": len(problems),
        "accuracy_screen_is_separate": True}, indent=2))
    if problems:
        print(f"Completed with {len(problems)} failed cases/checks. Inspect output.")
        sys.exit(2)
    print("Completed successfully:", args.out)


if __name__ == "__main__":
    main()
