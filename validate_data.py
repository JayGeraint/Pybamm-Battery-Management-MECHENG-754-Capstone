"""Unfitted discharge check against Chen2020's published validation dataset.

Uses constant mean measured current, measured initial cell temperature, and mean
chamber temperature per discharge. Initial equilibrium state is inferred from
the preceding rested voltage. This is not an independent new-cell validation or
a fast-charge validation. No thermal parameters are fitted to these data.
"""
import os
os.environ.setdefault("PYBAMM_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pybamm
from run_study import environment
from study_contract import parameters, validate_config, source_hashes, RunRejected, evidence_json

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/baseline.json")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--steps", type=int, nargs="+", default=[17],
                        help="17 is ~1C; use 7 12 17 22 for ~0.1,0.5,1,1.5C")
    args = parser.parse_args()
    cfg = validate_config(json.loads(args.config.read_text()))
    files = sorted(args.data_dir.glob("LGM50_cell*.csv"))
    if not files or len(set(args.steps)) != len(args.steps):
        raise ValueError("Require input cells and unique discharge steps; no empty successful validation")
    args.out.mkdir(parents=True, exist_ok=False)
    evidence_json(args.out / "environment.json", dict(environment(), source_sha256=source_hashes()))
    evidence_json(args.out / "config.json", cfg)
    metrics = []
    for file in files:
        full = pd.read_csv(file, float_precision="round_trip")
        if not np.isfinite(full[["time_s", "voltage_v", "current_a", "ambient_c", "temperature_c"]].to_numpy()).all():
            raise ValueError(f"Nonfinite measurements: {file}")
        if np.any(np.diff(full.time_s) < 0):
            raise ValueError(f"Unordered measurements: {file}")
        for step in args.steps:
            measured = full[(full.step == step) & (full["mode"] == "D")].copy()
            measured = measured.drop_duplicates("time_s", keep="last")
            if measured.empty:
                raise ValueError(f"No discharge step {step} in {file}")
            previous = full[(full.time_s < measured.time_s.iloc[0]) & (full["mode"] == "R")]
            if previous.empty:
                raise ValueError(f"No preceding rest for step {step}: {file}")
            rest = previous[previous.step == previous.step.iloc[-1]]
            rest_v = float(rest.voltage_v.iloc[-1])
            rest_duration = float(rest.time_s.iloc[-1] - rest.time_s.iloc[0])
            if rest_duration < 3600:
                raise ValueError("Require >=1 h preceding rest for equilibrium initialization")
            measured["time_s"] -= measured.time_s.iloc[0]
            current = float(measured.current_a.mean())
            ambient = float(measured.ambient_c.mean())
            initial_temp = float(measured.temperature_c.iloc[0])
            duration = float(measured.time_s.iloc[-1])
            if len(measured) < 2 or duration <= 0 or current <= 0:
                raise ValueError("Invalid discharge duration or current")
            for name in ["SPM", "SPMe", "DFN"]:
                key = f"{file.stem}_step{step}_{name}"
                print("Data check", key, flush=True)
                try:
                    params = parameters(cfg["parameter_variant"])
                    params.update({"Initial temperature [K]": initial_temp + 273.15,
                                   "Ambient temperature [K]": ambient + 273.15,
                                   "Total heat transfer coefficient [W.m-2.K-1]": cfg["heat_transfer_w_m2_k"]})
                    experiment = pybamm.Experiment([
                        f"Discharge at {current} A for {duration*1.3:g} seconds or until 2.5 V"], period=f"{cfg['sample_period_s']} seconds")
                    sim = pybamm.Simulation(getattr(pybamm.lithium_ion, name)({"thermal": "lumped"}),
                        parameter_values=params, experiment=experiment,
                        var_pts={x: cfg["mesh_points"] if x.startswith("x_") else cfg["particle_mesh_points"]
                                 for x in ["x_n", "x_s", "x_p", "r_n", "r_p"]},
                        solver=pybamm.IDAKLUSolver(rtol=cfg["rtol"], atol=cfg["atol"], options={"num_threads":1}))
                    sol = sim.solve(initial_soc=f"{rest_v} V", calc_esoh=False)
                    if not str(sol.termination).startswith("event:"):
                        raise RunRejected(f"Did not reach voltage cutoff: {sol.termination}", "protocol_failure")
                    min_ce = float(np.min(sol["Electrolyte concentration [mol.m-3]"].entries))
                    if not np.isfinite(min_ce) or min_ce <= 0:
                        raise RunRejected(f"Nonphysical electrolyte concentration: {min_ce}")
                    end = min(duration, float(sol.t[-1]))
                    # Uniform grid avoids overweighting event-triggered measurement density.
                    grid = np.unique(np.r_[np.arange(0, end, cfg["sample_period_s"]), end])
                    vm = np.interp(grid, measured.time_s, measured.voltage_v)
                    tm = np.interp(grid, measured.time_s, measured.temperature_c)
                    vp = sol["Voltage [V]"](grid)
                    tp = sol["Volume-averaged cell temperature [K]"](grid) - 273.15
                    if end <= 0 or not np.isfinite(np.array([vm, tm, vp, tp])).all():
                        raise RunRejected("Empty comparison interval or nonfinite prediction")
                    err = vp - vm
                    pd.DataFrame({"time_s":grid,"measured_voltage_v":vm,"model_voltage_v":vp,
                                  "measured_surface_temperature_c":tm,"model_lumped_temperature_c":tp}).to_csv(args.out / (key+".csv"),index=False)
                    metrics.append({"case":key,"cell":file.stem,"model":name,"step":step,"status":"ok",
                        "parameter_variant":cfg["parameter_variant"],"minimum_electrolyte_mol_m3":min_ce,
                        "normalization":"raw measured voltage; no capacity or time rescaling",
                        "rate_c":current/5, "ambient_c":ambient,"initial_rest_voltage_v":rest_v,
                        "preceding_rest_s":rest_duration,"voltage_rmse_mv":float(np.sqrt(np.mean(err**2))*1000),
                        "voltage_max_abs_mv":float(np.max(np.abs(err))*1000),
                        "temperature_rmse_c":float(np.sqrt(np.mean((tp-tm)**2))),
                        "comparison_duration_s":end,"measured_duration_s":duration,
                        "coverage_pct":100*end/duration,"cutoff_time_error_s":float(sol.t[-1])-duration,
                        "current_approximation_max_abs_a":float(np.max(np.abs(measured.current_a-current))),
                        "provenance":"published parameterization validation data; no fitting; rested-voltage initialization"})
                except Exception as e:
                    metrics.append({"case":key,"status":"failed","error":repr(e),
                                    "run_category":getattr(e,"category","solver_or_execution_failure")})
                pd.DataFrame(metrics).to_csv(args.out / "validation_metrics.csv",index=False)
    failed = sum(m["status"] != "ok" for m in metrics)
    evidence_json(args.out / "status.json", {"cases":len(metrics),"expected_cases":len(files)*len(args.steps)*3,
                    "failures":failed,"execution_complete":True,"experimental_accuracy_is_not_a_pass_flag":True})
    if failed:
        raise RuntimeError(f"{failed} validation cases failed; see validation_metrics.csv")


if __name__ == "__main__":
    main()
