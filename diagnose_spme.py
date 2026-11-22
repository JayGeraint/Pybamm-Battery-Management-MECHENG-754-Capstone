"""Investigate 3C SPMe failures without changing the production benchmark.

Changing numerical settings is a diagnostic, not a validation of physical safety.
Partial solutions are explicitly marked incomplete and never scored as complete
CC-CV runs. This script is separate from performance timing.
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
import pybamm
from run_study import make_sim, extract


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--variants", nargs="+", choices=["default", "tighter_tolerance", "fine_x", "coarse_r"], default=["default", "tighter_tolerance", "fine_x", "coarse_r"])
    a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parent
    base=json.loads((root/"configs/sweep.json").read_text())
    records=[]
    for temp in [10.,25.,40.]:
        for variant in a.variants:
            cfg=dict(base)
            if variant=="tighter_tolerance": cfg.update(rtol=1e-8,atol=1e-10)
            if variant=="fine_x": cfg.update(mesh_points=80)
            if variant=="coarse_r": cfg.update(particle_mesh_points=80)
            row={"ambient_c":temp,"rate_c":3.,"variant":variant,"complete":False,
                 "mesh_x":cfg["mesh_points"],"mesh_r":cfg["particle_mesh_points"],
                 "rtol":cfg["rtol"],"atol":cfg["atol"]}
            try:
                sim=make_sim("SPMe",3.,temp,cfg)
                row["solver_class"]=type(sim.solver).__name__
                sol=sim.solve(initial_soc=cfg["initial_soc"],calc_esoh=False)
                row["returned_end_s"]=float(sol.t[-1])
                row["returned_termination"]=str(sol.termination)
                row["returned_min_electrolyte_mol_m3"]=float(np.min(sol["Electrolyte concentration [mol.m-3]"].entries))
                row["returned_peak_temperature_c"]=float(np.max(sol["Volume-averaged cell temperature [K]"].entries)-273.15)
                # A partial Experiment solution may return the completed CC step
                # after a later solver failure. extract rejects missing CV.
                extract(sol,cfg)
                row["complete"]=True
            except Exception as exc:
                row["error"]=repr(exc)
            records.append(row)
            pd.DataFrame(records).to_csv(a.out/"diagnostics.csv",index=False)
            print(row,flush=True)
    (a.out/"interpretation.txt").write_text(
        "A partial solution's minimum concentration is not the concentration at the failed integration step. "
        "These diagnostics test numerical robustness; failure does not prove a physical battery failure. "
        "Do not replace missing production metrics with diagnostic results without rerunning a consistently defined benchmark.\n")


if __name__=="__main__": main()
