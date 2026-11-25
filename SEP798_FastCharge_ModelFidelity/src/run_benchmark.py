"""
Computational-cost benchmark (run serially, nothing else running, so timings are clean).

For each benchmark case and model, the simulation is built and solved BENCH_REPEATS times.
Two times are recorded:
  wall_s  : Simulation set-up (parameter processing, discretisation, solver set-up) + solve
  solve_s : time spent inside the time integrator only (PyBaMM's solution.solve_time)
The UDDS benchmark uses one 1370 s UDDS cycle.

Output: results/benchmark.csv, results/benchmark_summary.csv
"""
import platform
import numpy as np
import pandas as pd

import config as cfg
import battery


def main():
    rows = []
    for proto, val, T in cfg.BENCH_CASES:
        for m in cfg.MODELS:
            n = cfg.BENCH_REPEATS if not (proto == "udds" and m == "DFN") else max(2, cfg.BENCH_REPEATS // 2)
            for k in range(n):
                r = battery.run_case(m, proto, val, T, udds_repeats=1)
                rows.append({"protocol": proto, "value": val, "T_amb_C": T, "model": m, "repeat": k,
                             "status": r["status"], "wall_s": r.get("wall_s"), "solve_s": r.get("solve_s")})
                print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(cfg.RESULTS / "benchmark.csv", index=False)

    # median over repeats (first repeat dropped: includes one-off import / JIT warm-up)
    df2 = df[(df.repeat > 0) & (df.status == "ok")] if (df.repeat > 0).any() else df
    summ = (df2.groupby(["protocol", "value", "T_amb_C", "model"])[["wall_s", "solve_s"]]
            .median().reset_index())
    for col in ("wall_s", "solve_s"):
        ref = summ[summ.model == cfg.REFERENCE].set_index(["protocol", "value", "T_amb_C"])[col]
        summ[f"speedup_{col[:-2]}"] = [ref.loc[(p, v, t)] / x for p, v, t, x in
                                       zip(summ.protocol, summ.value, summ.T_amb_C, summ[col])]
    summ["machine"] = f"{platform.processor() or platform.machine()} | {platform.system()} | python {platform.python_version()}"
    summ.to_csv(cfg.RESULTS / "benchmark_summary.csv", index=False)
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
