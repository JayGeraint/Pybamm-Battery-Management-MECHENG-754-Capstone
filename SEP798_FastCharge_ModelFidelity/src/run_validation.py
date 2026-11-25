"""
Terminal-voltage (and surface-temperature) validation against measured LG M50T data.

Data (data/m50t/): beginning-of-life LG M50T cell "D" at 25 degC
  * RPT0  : C/10 (0.5 A) constant-current discharge, 4.2 V -> 2.5 V
  * RPT1  : 0.5C hybrid CC-pulse discharge (2.5 A base current with periodic pulses)
The measured current is fed to each model; voltage and temperature are compared.
No parameter is fitted: this checks the Chen2020 parameter set as used in the study.

Two comparisons are reported:
  raw              : the measured current is applied as is.
  capacity-aligned : the measured current is multiplied by k = Q_model / Q_measured, where Q_model is
                     the model's C/10 capacity (4.2 -> 2.5 V) and Q_measured the capacity delivered in the
                     test.  This removes the ~5 % capacity / SOC-window mismatch between the Chen2020 cell
                     and this particular M50T cell (one scalar, no dynamic parameter is touched), so the
                     remaining error reflects OCV shape and dynamics.

Output: results/validation.csv, results/validation_traces.pkl
"""
import pickle
import numpy as np
import pandas as pd

import config as cfg
import battery

# name: (csv file, resample step [s], initial SOC of the model)
# To add e.g. a measured 1C / 3C charge, append an entry with the file path and the starting SOC.
DATASETS = {
    "C/10 discharge (RPT0)": (cfg.M50T_C10, 10.0, 1.0),
    "0.5C hybrid pulse discharge (RPT1)": (cfg.M50T_PULSE, 1.0, 1.0),
}


def model_capacity_c10(model="DFN"):
    """Model capacity for a C/10 discharge 4.2 V -> 2.5 V at 25 degC."""
    import pybamm
    p = battery.get_parameters(25.0)
    sim = pybamm.Simulation(battery.build_model(model), parameter_values=p,
                            experiment=pybamm.Experiment(["Discharge at C/10 until 2.5 V"], period="60 seconds"),
                            solver=battery.make_solver())
    sol = sim.solve(initial_soc=1.0)
    return float(sol["Discharge capacity [A.h]"].entries[-1])


def main():
    rows, store = [], {}
    q_model = model_capacity_c10()
    print(f"model C/10 capacity = {q_model:.3f} Ah", flush=True)
    for name, (path, dt, soc0) in DATASETS.items():
        data = battery.load_m50t(path, dt=dt)
        data["soc0"] = soc0
        k = q_model / abs(data["Q_Ah"][-1])
        aligned = dict(data, I=data["I"] * k)
        store[name] = {"data": data, "k": k}
        print(f"{name}: {len(data['t'])} samples, {data['t'][-1]:.0f} s, "
              f"Q = {data['Q_Ah'][-1]:.3f} Ah, T0 = {data['T_C'][0]:.2f} C, k = {k:.4f}", flush=True)
        for variant, dd in (("raw", data), ("capacity-aligned", aligned)):
            for m in cfg.MODELS:
                r = battery.run_case(m, "measured", dd, 25.0)
                store[name][m if variant == "raw" else m + "_aligned"] = r
                tr = r["traces"]
                if tr is None:
                    rows.append({"dataset": name, "variant": variant, "model": m, "status": r["status"],
                                 "message": r["message"]})
                    continue
                t_end = min(tr["t"][-1], data["t"][-1])
                mk = data["t"] <= t_end
                Vm = np.interp(data["t"][mk], tr["t"], tr["V"])
                Tm = np.interp(data["t"][mk], tr["t"], tr["T_C"])
                err = Vm - data["V"][mk]
                # same comparison restricted to the 0-90 % depth-of-discharge window (excludes the end-of-discharge knee)
                dod = data["Q_Ah"][mk] / data["Q_Ah"][-1]
                w = dod <= 0.9
                rows.append({
                    "dataset": name, "variant": variant, "k_scale": k if variant != "raw" else 1.0,
                    "model": m, "status": r["status"],
                    "V_rmse_mV": 1e3 * np.sqrt(np.mean(err ** 2)),
                    "V_rmse_DOD0-90_mV": 1e3 * np.sqrt(np.mean(err[w] ** 2)),
                    "V_mean_err_mV": 1e3 * np.mean(err[w]),
                    "V_maxerr_mV": 1e3 * np.max(np.abs(err)),
                    "T_rmse_K": np.sqrt(np.mean((Tm - data["T_C"][mk]) ** 2)),
                    "Tpeak_model_C": float(np.max(tr["T_C"])), "Tpeak_meas_C": float(np.max(data["T_C"])),
                    "Q_model_Ah": float(tr["Q_dis"][-1]), "Q_meas_Ah": float(data["Q_Ah"][-1]),
                    "t_end_model_s": float(tr["t"][-1]), "t_end_meas_s": float(data["t"][-1]),
                    "wall_s": r.get("wall_s"), "solve_s": r.get("solve_s"),
                })
                print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(cfg.RESULTS / "validation.csv", index=False)
    with open(cfg.RESULTS / "validation_traces.pkl", "wb") as f:
        pickle.dump(store, f)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
