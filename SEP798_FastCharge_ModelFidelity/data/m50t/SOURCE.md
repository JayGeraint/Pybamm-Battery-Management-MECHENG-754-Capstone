# Measured LG M50T data used for validation

Files
- `cellD_RPT0_C10_discharge.csv` — beginning-of-life C/10 (0.5 A) constant-current discharge, 4.2 V → 2.5 V, 25 °C chamber.
- `cellD_RPT1_hybrid_pulse_0p5C_discharge.csv` — 0.5C (2.5 A) hybrid constant-current + pulse discharge, 25 °C chamber.

Columns: `Time (s), Voltage (V), Current (mA), Charge (mA.h), Temperature (degC)` (negative current = discharge; temperature is a surface thermocouple).

Where they came from
- Downloaded on 2026-11-18 from the public GitHub repository
  `Sa2908/ES60208-Recharge-Battery-Modelling-Project` (files `cell_D_RPT0.csv` and
  `cell D_RPT1_Hybrid CC-Pulse 0.5C discharge data.csv`), where they are used as LG M50T reference data.
- The file naming (cell D, RPT0/RPT1, "Hybrid CC-Pulse") and column format match the LG M50T ageing dataset of
  Kirkaldy et al., *"Lithium-ion battery degradation: comprehensive cycle ageing data and analysis for commercial 21700 cells"*,
  Journal of Power Sources (2024). **Please check this attribution against the original dataset before citing it in the report.**

Why not the 1C/3C charge + UDDS M50T data mentioned in Plan A?
- The data repositories that host it (Zenodo, Mendeley Data, OSF) were not reachable from the environment used to build this project.
  `src/run_validation.py` accepts any CSV with the same five columns, so if you download that dataset you can add it to
  the `DATASETS` dictionary at the top of `run_validation.py` and re-run.
