"""Execute one illustrative DFN charge with SEI and partially reversible plating.

Full OKane2022 parameters; not the default Chen2020 fidelity benchmark. This
demonstrates executable side-reaction physics, not identification, validated
cycle life, irreversible RPT capacity loss, or optimized charging.
"""
import argparse
import copy
import json
from pathlib import Path
import time
from run_study import environment
from study_contract import source_hashes, evidence_json
import numpy as np
import pandas as pd
import pybamm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    cfg = {"parameter_set":"OKane2022", "initial_soc":.1, "rate_c":3,
           "temperature_c":25, "heat_transfer_w_m2_k":10,
           "voltage_limit_v":4.2, "cv_cutoff_c":.05, "mesh_x":40, "mesh_r":160,
           "rtol":1e-6, "atol":1e-8, "sample_period_s":2,
           "options":{"thermal":"lumped", "SEI":"solvent-diffusion limited",
                      "lithium plating":"partially reversible"}}
    evidence_json(args.out / "config.json", cfg)
    evidence_json(args.out / "environment.json", dict(environment(), source_sha256=source_hashes()))
    start = time.perf_counter()
    try:
        model = pybamm.lithium_ion.DFN(copy.deepcopy(cfg["options"]))
        params = pybamm.ParameterValues(cfg["parameter_set"])
        params.update({"Ambient temperature [K]":298.15, "Initial temperature [K]":298.15,
                       "Total heat transfer coefficient [W.m-2.K-1]":10.})
        experiment = pybamm.Experiment([("Charge at 3 C for 1 hour or until 4.2 V",
            "Hold at 4.2 V for 4 hours or until C/20")], period="2 seconds")
        sim = pybamm.Simulation(model, parameter_values=params, experiment=experiment,
            var_pts={"x_n":40, "x_s":40, "x_p":40, "r_n":160, "r_p":160},
            solver=pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8, options={"num_threads":1}))
        sol = sim.solve(initial_soc=.1, calc_esoh=False)
        steps = sol.cycles[0].steps
        if len(steps) != 2 or not all(s is not None and str(s.termination).startswith("event:") for s in steps):
            raise ValueError("Both CC and CV must finish at their requested events")
        ce_min = float(np.min(sol["Electrolyte concentration [mol.m-3]"].entries))
        if not np.isfinite(ce_min) or ce_min <= 0:
            raise ValueError("Nonphysical electrolyte concentration")
        variables = {"voltage_v":"Voltage [V]", "current_a":"Current [A]",
            "temperature_k":"Volume-averaged cell temperature [K]",
            "sei_capacity_variable_ah":"Loss of capacity to negative SEI [A.h]",
            "plating_capacity_variable_ah":"Loss of capacity to negative lithium plating [A.h]"}
        t = np.unique(sol.t)
        frame = pd.DataFrame(dict(time_s=t, **{k:np.asarray(sol[v](t)).reshape(-1) for k,v in variables.items()}))
        if not np.isfinite(frame.to_numpy()).all() or np.any(np.diff(t) <= 0):
            raise ValueError("Invalid output trace")
        if abs(frame.current_a.iloc[-1] + .25) > .005 or frame.voltage_v.max() > 4.202:
            raise ValueError("Voltage or final current violates the protocol")
        frame.to_csv(args.out / "trace.csv", index=False)
        evidence_json(args.out / "metrics.json", {"execution_status":"completed",
            "wall_s":time.perf_counter()-start, "integrator_s":float(sol.solve_time.value),
            "minimum_electrolyte_mol_m3":ce_min,
            "peak_temperature_c":float(frame.temperature_k.max()-273.15),
            "final_current_a":float(frame.current_a.iloc[-1]),
            "end_s":float(t[-1]), "step_terminations":[str(s.termination) for s in steps],
            "final_sei_capacity_variable_ah":float(frame.sei_capacity_variable_ah.iloc[-1]),
            "final_plating_capacity_variable_ah":float(frame.plating_capacity_variable_ah.iloc[-1]),
            "initial_sei_capacity_variable_ah":float(frame.sei_capacity_variable_ah.iloc[0]),
            "initial_plating_capacity_variable_ah":float(frame.plating_capacity_variable_ah.iloc[0]),
            "delta_sei_capacity_variable_ah":float(frame.sei_capacity_variable_ah.iloc[-1]-frame.sei_capacity_variable_ah.iloc[0]),
            "delta_plating_capacity_variable_ah":float(frame.plating_capacity_variable_ah.iloc[-1]-frame.plating_capacity_variable_ah.iloc[0]),
            "scope":"single-charge execution evidence only; no fit, cycling, RPT, lifetime or optimization",
            "interpretation":"plating variable includes reversible lithium inventory; not measured irreversible capacity loss"})
    except Exception as exc:
        evidence_json(args.out / "failure.json", {"execution_status":"failed", "error":repr(exc)})
        raise
    print("Single-charge degradation illustration completed:", args.out)


if __name__ == "__main__":
    main()
