"""Check positive electrolyte concentration in completed production cases.

This targeted check follows a negative-concentration finding in failed 3C SPMe
runs. It does not prove that every physical assumption of a model is valid.
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from run_study import make_sim, extract


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    a=p.parse_args()
    cfg=json.loads((a.folder/"config.json").read_text())
    s=pd.read_csv(a.folder/"summary.csv")
    rows=[]
    for _,row in s[s.status=="ok"].iterrows():
        print("Audit",row.model,row.rate_c,row.ambient_c,flush=True)
        sim=make_sim(row.model,row.rate_c,row.ambient_c,cfg)
        sol=sim.solve(initial_soc=cfg["initial_soc"],calc_esoh=False)
        extract(sol,cfg)
        ce=sol["Electrolyte concentration [mol.m-3]"].entries
        minimum=float(np.min(ce))
        rows.append({"model":row.model,"rate_c":row.rate_c,"ambient_c":row.ambient_c,
                     "minimum_electrolyte_mol_m3":minimum,"positive_electrolyte":minimum>0})
        pd.DataFrame(rows).to_csv(a.folder/"physical_validity_audit.csv",index=False)
    if not all(row["positive_electrolyte"] for row in rows):
        raise ValueError("Nonpositive concentration found in completed cases; revise admissible comparisons")


if __name__=="__main__": main()
