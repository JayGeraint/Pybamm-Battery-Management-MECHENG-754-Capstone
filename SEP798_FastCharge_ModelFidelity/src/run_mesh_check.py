"""
Is the DFN reference itself converged?  Compare the default mesh (20 points per domain /
particle) with a refined mesh (40 points) for the hardest charge cases and a gentle one.
If the default-mesh DFN differs from the fine-mesh DFN by much less than the SPM/SPMe
errors, the default DFN is a valid reference.

Output: results/mesh_check.csv
"""
import numpy as np
import pandas as pd

import config as cfg
import battery
import metrics

CASES = [(1.0, 25.0), (3.0, 25.0), (3.0, 0.0), (2.0, 0.0)]


def main():
    rows = []
    for c, T in CASES:
        coarse = battery.run_case("DFN", "charge", c, T, var_pts=cfg.VAR_PTS)
        fine = battery.run_case("DFN", "charge", c, T, var_pts=cfg.VAR_PTS_FINE)
        e = metrics.compare(fine, coarse) if coarse["status"] == fine["status"] == "ok" else {}
        s_c, s_f = metrics.single_run_summary(coarse), metrics.single_run_summary(fine)
        rows.append({"C_rate": c, "T_amb_C": T,
                     "status_coarse": coarse["status"], "status_fine": fine["status"],
                     "V_rmse_mV": e.get("V_rmse_mV"), "V_rmse_cc_mV": e.get("V_rmse_cc_mV"),
                     "Tpeak_err_K": e.get("Tpeak_err_K"), "t80_err_pct": e.get("t80_err_pct"),
                     "phi_sep_min_coarse_mV": 1e3 * s_c.get("phi_sep_min_V", np.nan),
                     "phi_sep_min_fine_mV": 1e3 * s_f.get("phi_sep_min_V", np.nan),
                     "wall_coarse_s": coarse.get("wall_s"), "wall_fine_s": fine.get("wall_s"),
                     "solve_coarse_s": coarse.get("solve_s"), "solve_fine_s": fine.get("solve_s")})
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(cfg.RESULTS / "mesh_check.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
