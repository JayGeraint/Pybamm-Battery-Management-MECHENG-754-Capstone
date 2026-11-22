# PyBaMM Battery Management — MECHENG 754 Capstone

This package provides a runnable SPM/SPMe/DFN charging comparison using Chen2020 parameters and a lumped thermal model, with numerical checks, operating-condition sweeps, measured-discharge comparisons and team task assignments.

All deliverables are in English except [GUIDE_ZH_EN.md](docs/GUIDE_ZH_EN.md), which retains Chinese–English parallel explanations.

## Start here

1. Read [ABSTRACT_REVIEW_EN.md](docs/ABSTRACT_REVIEW_EN.md) for the scope decision and replacement abstract.
2. Read [GUIDE_ZH_EN.md](docs/GUIDE_ZH_EN.md) for the detailed bilingual workflow and portable setup commands.
3. Open [RESULTS_SUMMARY_EN.md](docs/RESULTS_SUMMARY_EN.md) for the results actually obtained in this deployment.
4. Share [TEAM_TASKS_EN.md](docs/TEAM_TASKS_EN.md) with your two teammates, together with this package.

## Included results

The supplied production sweep completed **33 of 36 cases**. SPMe at 3C failed at all three temperatures (10, 25 and 40 degrees C); the original failure records are retained. These are existing study results, not a new simulation run performed during repository organization. See the [results summary](docs/RESULTS_SUMMARY_EN.md) and [failure records](results/sweep/failures.json).

![Model accuracy and computational cost](results/sweep/figures/accuracy_cost_map.png)

## Files

| File or folder | Purpose |
|---|---|
| `run_study.py` | Three-model CC-CV simulations, metrics, timing and convergence |
| `plot_results.py` | Figures from exported charging results |
| `prepare_data.py` | Source checksum validation, data cleaning and step inventory |
| `validate_data.py` | Unfitted model-to-measurement discharge comparisons |
| `diagnose_spme.py` | Separate mesh/tolerance investigation of incomplete 3C cases |
| `audit_physics.py` | Positive-electrolyte check for completed production cases |
| `plot_validation.py` | Experimental comparison plots |
| `configs/` | Baseline and 36-case sweep configurations |
| `requirements-lock.txt` | Exact installed dependency versions |
| `setup.ps1` | Teammate environment setup; equivalent manual commands below |
| `data/raw/` | Three unchanged public LG M50 source files and repository metadata |
| `data/processed/` | Normalized current signs, quality audit and step inventory |
| `results/sweep/` | Production simulation results, configuration and environment |
| `results/convergence_refined/` | Accepted production-grid numerical checks |
| `results/validation_1C/` | Three-cell measured 1C discharge comparison |
| `results/baseline/`, `results/convergence/` | Earlier coarser deployment checks, retained as audit history |
| [SOURCES.md](docs/SOURCES.md) | Primary references and evidence boundaries |

## Fresh environment

The original study was tested on Windows with Python 3.10.11. Clone this repository and run all commands from its root directory:

```powershell
git clone https://github.com/JayGeraint/Pybamm-Battery-Management-MECHENG-754-Capstone.git
cd Pybamm-Battery-Management-MECHENG-754-Capstone
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe run_study.py --config configs/baseline.json --out results/my_baseline
.\.venv\Scripts\python.exe plot_results.py results/my_baseline
```

No activation or execution-policy change is required. The packaged virtual environment is not distributed; each teammate creates their own.

## Full run

For a routine run without the known 3C stress-case failures, use `--config configs/core.json` (27 combinations already exercised successfully in the full sweep). The full matrix intentionally retains the failed stress cases as research evidence.

```powershell
.\.venv\Scripts\python.exe run_study.py --config configs/baseline.json --convergence --out results/my_convergence
.\.venv\Scripts\python.exe run_study.py --config configs/sweep.json --out results/my_sweep
.\.venv\Scripts\python.exe plot_results.py results/my_sweep
.\.venv\Scripts\python.exe prepare_data.py
.\.venv\Scripts\python.exe validate_data.py --steps 17 --out results/my_validation
.\.venv\Scripts\python.exe plot_validation.py results/my_validation
```

Choose new output folder names on each run. Failed cases are recorded and produce a nonzero process exit. Inspect them before interpreting a summary.

## Interpretation

Voltage error is primarily reported over the common CC interval; CV voltage is imposed by the controller. DFN is a numerical reference. Charging time uses the documented nominal 5 Ah coulomb-counted SOC proxy. Runtime is a repeated warm simulation measurement on this machine, with build and first-solve cost reported separately. No degradation, plating amount, cycle-life prediction or real-time safety claim is implemented.

Experimental files are CC BY 4.0, with attribution and modification notes in `data/README.md`. Do not redistribute the original user report or personal details with this package; they are not included.

## Repository organization and reproducibility

- `docs/` contains the research scope, bilingual guide, results summary, team plan and references.
- Python entry points remain at the repository root so their existing data paths and commands continue to work.
- `data/` and `results/` retain the supplied datasets, figures and numerical evidence.
- `parameter_audit.json`, `verification.json` and `LANGUAGE_AUDIT.json` are historical records from the original deployment; they are not new verification claims for this upload.
- `MANIFEST_SHA256.json` records the SHA-256 of every distributed file except itself and Git metadata. It was regenerated after documentation organization.
- Local environments, caches, credentials and new `results/my_*` runs are excluded by `.gitignore`. Use those output names for local experiments; intentionally tracked study results remain in Git.

See [repository preparation notes](docs/REPOSITORY_PREPARATION.md) for the changes and checks performed during upload preparation.
