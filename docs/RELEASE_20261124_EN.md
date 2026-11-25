# Main corrections and reproducible release - 2026-11-24

This release updates main from `0eb1b1d65dbdc85df6b1f5fea9ce057633b80a2a`.
It repairs the findings applicable to main and ports the four-function transport
variant behind the existing runner. It does not import Joe's second repository
folder wholesale. Joe's branch, UDDS workflow, MATLAB handoff, second dataset and
its existing documents are outside this main update; their review findings remain
open until those components are integrated and verified.

## Issue-by-issue disposition

| Review issue | Change and evidence | Disposition |
|---|---|---|
| Mixed SOC conventions | `study_contract.capacity_basis` derives the electrode-window capacity from the same fresh-cell parameters used for initialization. New traces export `soc`, `soc_electrode_window` and `soc_nominal`; summaries export all three corresponding t80 fields. | Fixed for the benchmark without degradation |
| Parameter changes hidden inside a second runner | One `parameters()` function supplies charging and measured-discharge validation. Configurations name the variant explicitly. Default Chen2020 remains unchanged. | Fixed for the integrated CC-CV workflow |
| Solver failure confused with poor accuracy | Summaries distinguish physical/protocol/execution failure; completed cases receive a separate accuracy category. A failed case cannot enter a valid comparison. | Fixed; physical limitations remain visible |
| Missing metrics accepted; selector extrapolation | Missing, nonfinite or malformed mandatory metrics are invalid. The selector refuses nonfinite/off-grid inputs and fewer than five repetitions; it requires a completed DFN reference. | Fixed in main's new classifier/selector |
| Mismatched temperature and time metrics | Maximum pointwise temperature error and peak-temperature difference are separate columns. t80 errors include seconds and percent. | Fixed; 60 seconds and 5 percent are not globally ordered thresholds |
| Inadequate timing evidence | Five warm repetitions, median, quartiles, integrator time, first-solve and build cost; models execute sequentially on one machine. | Fixed for main's CC-CV benchmark; no UDDS speed claim |
| Validation windows/scaling | Measured voltage and current remain unscaled; uniform common-time comparison, coverage, cutoff-time error and current approximation error are explicit. New guards reject missing data/rest and nonphysical output; particle mesh now matches 40/160 production. | Fixed implementation; independent fast-charge validation remains open |
| Numerical evidence after changing transport | Plain and transport-variant DFN mesh/tolerance checks have separate output folders. | Evidence scoped to the tested conditions, not a universal operating boundary |
| CSV timestamp/float handling | Round-trip float parsing preserves near-equal switch times. One exact historical duplicate was removed with every retained byte unchanged; the original file and hashes remain in `results/archive_20261124/`. | Fixed with traceable archive |
| Stale release audits and English delivery | Current verification/language/manifest files replace the old audit entry points; original audits are retained in `docs/history/`. Formal outputs use English; only the designated guide is bilingual. | Updated for this release |
| Full degradation identification, cycle life, charge optimization absent | Added a runnable single-charge illustration and a concrete data/code/acceptance roadmap. The three original objectives remain explicitly false in `verification.json`. | Open research objectives; not claimed complete |

## Executed results

| Check | Result | Interpretation |
|---|---|---|
| Plain Chen2020 charging matrix | 33 completed / 36 attempted; SPMe failed at 3C at all three temperatures | Failed cases are excluded from valid comparisons and lookup candidates |
| Reduced-model accuracy screen, plain matrix | 6 adequate / 21 completed comparisons against DFN | Completion is not equivalent to accuracy acceptance |
| Transport variant, 1C and 3C at 25 C | 5 completed / 6 attempted; SPMe failed at 3C | Temperature-dependent transport does not guarantee high-rate SPMe validity |
| Numerical acceptance | 4/4 checks for plain parameters and 4/4 for the transport variant | Production mesh versus refinement and tighter solver tolerances at the two stated conditions |
| Measured-discharge comparisons | 9 completed per parameter variant, 18 total | Completion establishes evaluability; it is not an experimental-accuracy pass |
| DFN measured voltage RMSE, plain parameters | 62.07-70.07 mV across three cells; 100% time coverage | Unfitted reproduction on the parameterization study's data |
| DFN measured voltage RMSE, transport variant | 102.67-110.78 mV; 100% time coverage | Larger errors here; this variant is retained for sensitivity analysis, not promoted as a better calibrated model |
| Original-data preprocessing | All three source checksums pass; five processed files reproduce byte-for-byte | Existing measurement data were preserved |
| Single-charge degradation illustration | Both CC/CV events completed; electrolyte minimum 62.795 mol/m3; final current -0.25 A | Execution evidence only; peak temperature 66.698 C does not establish an acceptable charge policy |

The illustration's SEI-related capacity variable increased by about 0.000104805 Ah
and its plating-related variable by about 0.016935647 Ah. These are model state
outputs, not measured RPT losses; the plating variable includes reversible
inventory. No ageing parameters were fitted and no cycles, lifetime prediction
or charging search were executed. See the detailed trace and metrics in
`results/release_20261124/degradation_demo/`.

At 1C/25 C, plain SPMe has 6.8298 mV common-CC voltage RMSE against DFN,
15.4246 seconds selected-SOC t80 error, and an approximately 18.14x measured
median warm-solve speedup. These are model-comparison metrics on this machine,
not measured-cell accuracy or a portable timing guarantee.

For the transport-variant DFN at 3C/25 C, nominal-proxy t80 is 892.022 seconds
(14.867 minutes), but consistent electrode-window t80 is 940.497 seconds
(15.675 minutes). Peak temperature is 65.202 C and minimum separator anode
potential difference is -39.343 mV. This case does not establish a 15-minute
10-80% result or an acceptable charging policy.

## Scientific contract

- **Current and initial state:** positive current is discharge. Initial SOC is 0.1.
  1C remains 5 A. The reference fresh-cell electrode-window capacity is approximately
  5.153198326 Ah, derived from electrode stoichiometry limits, not fitted to a test
  record. At beginning of life without side reactions, `soc = initial_soc - Q_dis / Q_window`.
- **Target:** `time_to_80_soc_s` follows `soc_definition`; the release selects
  `electrode_window`. `time_to_80_nominal_soc_s` is a historical 5 Ah proxy and
  must not establish a 15-minute physical-SOC claim. No SOC is clipped to hide an
  overshoot. The definition does not apply unchanged to a degraded cell.
- **Parameters:** `Chen2020_OKane2022_transport` replaces negative/positive particle
  diffusivity, electrolyte diffusivity and electrolyte conductivity only. Names
  and source keys are in `study_contract.TRANSPORT_KEYS`. Full OKane2022 is used
  only in the separate degradation illustration. Neither is a new parameter fit.
- **Comparison:** primary voltage RMSE uses common CC time. Full-protocol voltage
  includes controller-imposed CV and is supplementary. Temperature maximum error
  uses pointwise differences on the common full interval; peak-temperature error
  compares the complete individual traces. Interpolation cannot extrapolate.
- **Project accuracy screen:** CC voltage RMSE <=20 mV, maximum temperature error
  <=1 degree C, absolute selected-SOC t80 error <=60 seconds. These are project
  thresholds, not cell operating limits or a safety standard.
- **Physical check:** electrolyte concentration must be finite and positive;
  complete CC/CV event termination and final cutoff current are required. Positive
  concentration alone does not prove full physical fidelity. The earlier empirical
  150 mol/m3 observation is not used as a universal acceptance threshold.
- **Benchmark:** build, first solve, warm solve and integrator times have different
  boundaries. Five warm repetitions reuse the built simulation and restart the
  same initial condition. Results describe this machine under ordinary desktop
  load, with single-thread solver/BLAS settings, rather than guaranteed real-time
  performance. No competing model simulations were scheduled during these timings.
- **Numerical screen:** DFN 20/80, 40/160 and 80/320 meshes at 1C/25 C and 3C/10 C;
  production-to-fine and tightened-tolerance comparisons require <2 mV maximum
  CC voltage error, <0.1 C maximum temperature error, <2 seconds CC end-time error
  and <2 mV maximum separator-potential error. These two conditions are a focused
  numerical check, not proof for arbitrary cooling, 0 C, other grids or ageing.

## Evidence locations and reproduction

All commands use the pinned environment and run from the repository root. Choose
new `results/my_*` directories; entry points refuse existing output directories.

```powershell
.\.venv\Scripts\python.exe -m unittest test_contracts -v
.\.venv\Scripts\python.exe run_study.py --config configs/sweep.json --out results/my_sweep
.\.venv\Scripts\python.exe run_study.py --config configs/baseline.json --convergence --out results/my_convergence
.\.venv\Scripts\python.exe run_study.py --config configs/transport_variant.json --out results/my_transport
.\.venv\Scripts\python.exe run_study.py --config configs/transport_variant.json --convergence --out results/my_transport_convergence
.\.venv\Scripts\python.exe validate_data.py --steps 17 --out results/my_validation
.\.venv\Scripts\python.exe validate_data.py --steps 17 --config configs/transport_variant.json --out results/my_transport_validation
.\.venv\Scripts\python.exe run_degradation_demo.py --out results/my_degradation_demo
.\.venv\Scripts\python.exe plot_results.py results/my_sweep
.\.venv\Scripts\python.exe plot_validation.py results/my_validation
.\.venv\Scripts\python.exe verify_release.py
```

The full plain-transport sweep intentionally returns exit code 2 when the three
SPMe stress cases fail. Inspect `failures.json`; do not suppress that status or
reinterpret it as 36 successful cases. `execution_complete` indicates the loop
finished; `all_cases_passed` is a separate field. Accuracy is assessed separately.

Each run has configuration/environment records and source hashes. The release
manifest covers all distributed files except itself and Git metadata. The
verification script checks code syntax, the locked environment, regression
checks, source hashes, retained timing repetitions, numerical screens, validation
coverage, trace monotonicity, selector behavior and English text. Numerical and
experimental conclusions have the boundaries stated above.

After the solves, the validation-plot caption was corrected to show the configured
parameter variant, and the audit was updated to record this distinction. The
original plotting/audit source snapshots are retained as `.py.txt` records in
`docs/history/`; the run-time hashes remain unchanged. The audit verifies those
snapshots and separately records the current tool hashes. No numerical runner,
parameter, configuration or model result changed during this figure correction.

Current outputs are under `results/release_20261124/`; historical results remain
under their original names and should not be pooled into current tables. For
how to obtain the still-missing ageing and optimization evidence, follow
[IMPLEMENTATION_EVIDENCE_EN.md](IMPLEMENTATION_EVIDENCE_EN.md).
