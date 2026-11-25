"""Choose a model only at an explicitly benchmarked grid point.

This is a numerical-fidelity lookup, not a safety controller or a charge optimizer.
No interpolation, extrapolation, or quick-run promotion is performed.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from study_contract import classify


def select(folder, rate, temperature):
    cfg = json.loads((folder / "config.json").read_text())
    if (not np.isfinite(rate) or not np.isfinite(temperature)
            or rate not in cfg["rates_c"] or temperature not in cfg["temperatures_c"]):
        return {"status": "out_of_domain", "model": None}
    if cfg.get("repeats", 0) < 5:
        return {"status": "insufficient_benchmark_repeats", "model": None}
    status = json.loads((folder / "run_status.json").read_text())
    if not status.get("execution_complete", False):
        return {"status": "incomplete_run", "model": None}
    summary = pd.read_csv(folder / "summary.csv", float_precision="round_trip")
    comparisons = pd.read_csv(folder / "comparisons.csv", float_precision="round_trip")
    valid = summary[(summary.rate_c == rate) & (summary.ambient_c == temperature) & (summary.status == "ok")]
    valid = valid[(valid.parameter_variant == cfg["parameter_variant"]) & (valid.soc_definition == cfg["soc_definition"])]
    valid = valid[np.isfinite(valid.warm_solve_wall_median_s) & (valid.warm_solve_wall_median_s > 0)]
    valid = valid[valid.warm_repeats_s.map(lambda s: len(json.loads(s)) >= 5)]
    if "DFN" not in valid.model.to_list():
        return {"status": "reference_unavailable", "model": None}
    eligible = ["DFN"]
    for row in comparisons.to_dict("records"):
        if (row["rate_c"] == rate and row["ambient_c"] == temperature
                and row.get("parameter_variant") == cfg["parameter_variant"]
                and row.get("soc_definition") == cfg["soc_definition"] and classify(row) == "adequate"):
            eligible.append(row["model"])
    chosen = valid[valid.model.isin(eligible)].sort_values("warm_solve_wall_median_s").iloc[0]
    return {"status": "selected", "model": str(chosen.model),
            "parameter_variant": cfg["parameter_variant"], "soc_definition": cfg["soc_definition"],
            "basis": "lowest measured median warm wall time among adequate models; DFN fallback",
            "scope": "numerical fidelity only; operating safety is not established"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--rate", type=float, required=True)
    parser.add_argument("--temperature", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(select(args.folder, args.rate, args.temperature), indent=2, allow_nan=False))
