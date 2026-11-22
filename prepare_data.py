"""Normalize the downloaded Chen et al. experimental files without hiding exclusions.

Original current is unsigned; Md=C/D determines direction. The PyBaMM convention
is discharge-positive. A row at a duplicate timestamp is retained in cleaned data
with a flag; individual validation steps remove exact duplicate timestamps.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def main():
    raw = ROOT / "data/raw"
    dest = ROOT / "data/processed"
    dest.mkdir(parents=True, exist_ok=True)
    record = json.loads((raw / "record_metadata.json").read_text(encoding="utf-8"))
    audits, steps = [], []
    checksums = {x["key"]: x["checksum"] for x in record["files"]}
    for file in sorted(raw.glob("LGM50_cell*.csv")):
        md5 = "md5:" + hashlib.md5(file.read_bytes()).hexdigest()
        if md5 != checksums[file.name]:
            raise ValueError(f"Checksum mismatch: {file}")
        lines = file.read_text(encoding="utf-8-sig").splitlines()
        header = next(i for i, line in enumerate(lines) if line.startswith("Rec,Cycle P"))
        d = pd.read_csv(file, skiprows=header)
        rename = {"Test Time [s]": "time_s", "Current [A]": "raw_current_a",
                  "Voltage [V]": "voltage_v", "Temperature Cell [degC]": "temperature_c",
                  "Temperature Chamber [degC]": "ambient_c", "Step": "step", "Md": "mode",
                  "Capacity [Ah]": "instrument_step_capacity_ah"}
        d = d.rename(columns=rename)
        known = d["mode"].isin(["C", "D", "R", "SBr", "O"])
        if not known.all():
            raise ValueError("Unknown current direction code")
        if (d.raw_current_a < 0).any():
            raise ValueError("This reader expects unsigned source currents")
        d["current_a"] = np.where(d["mode"] == "C", -d.raw_current_a,
                                  np.where(d["mode"] == "D", d.raw_current_a, 0.0))
        if (d.loc[~d["mode"].isin(["C", "D"]), "raw_current_a"].abs() > .01).any():
            raise ValueError("Nonzero current in unexpected mode")
        d["duplicate_time"] = d.time_s.duplicated(keep=False)
        d["cell_id"] = file.stem
        cols = ["cell_id", "time_s", "step", "mode", "current_a", "voltage_v",
                "temperature_c", "ambient_c", "instrument_step_capacity_ah", "duplicate_time"]
        numeric = ["time_s", "current_a", "voltage_v", "temperature_c", "ambient_c"]
        if not np.isfinite(d[numeric].to_numpy()).all() or (d.time_s.diff().dropna() < 0).any():
            raise ValueError("Invalid data values or reversed time")
        d[cols].to_csv(dest / file.name, index=False)
        for step, g in d.groupby("step", sort=False):
            steps.append({"cell_id": file.stem, "step": int(step),
                          "modes": ";".join(g["mode"].unique()), "rows": len(g),
                          "start_s": g.time_s.iloc[0], "end_s": g.time_s.iloc[-1],
                          "mean_current_a": g.current_a.mean(),
                          "mean_c_rate": g.current_a.mean()/5,
                          "start_voltage_v": g.voltage_v.iloc[0], "end_voltage_v": g.voltage_v.iloc[-1],
                          "mean_ambient_c": g.ambient_c.mean()})
        audits.append({"file": file.name, "rows": len(d), "header_line_1based": header + 1,
                       "duplicate_timestamp_rows": int(d.duplicate_time.sum()),
                       "md5": md5, "checksum_verified": True,
                       "time_reversed": False, "finite_required_values": True})
    pd.DataFrame(steps).to_csv(dest / "step_inventory.csv", index=False)
    (dest / "quality_audit.json").write_text(json.dumps(audits, indent=2))
    print(json.dumps(audits, indent=2))


if __name__ == "__main__":
    main()
