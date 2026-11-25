# Evidence needed for degradation, cycle life and charge optimization

Status date: 2026-11-24. These three original research objectives remain open.
The release adds an executed single-charge side-reaction illustration, with
source, configuration, trace and metrics in `results/release_20261124/degradation_demo/`.
That closes a runnable-demonstration milestone only.

## What qualifies as project implementation evidence

For each claim, retain a repository revision, executable entry point, environment,
input-data identifiers and checksums, configuration, full output, evaluation code
and a command that another teammate can reproduce. A proposal, slide, library
feature or external paper establishes a route to implementation; it does not
establish that this project has executed or validated that route.

| Objective | Present project evidence | Evidence still needed | Feasibility |
|---|---|---|---|
| Coupled degradation execution | `run_degradation_demo.py`: DFN, full OKane2022, solvent-diffusion-limited SEI, partially reversible plating, one CC-CV charge | Mechanisms matched to the cell and experiment; numerical checks across ageing states | Runnable now, but only an illustration |
| Degradation parameter identification | No fitted ageing parameters or identification results | Datasets, parameter bounds, fitting objective, retained optimization runs, uncertainty, identifiability and held-out evaluation | A limited identifiable parameter subset is feasible; unique identification of every mechanism is not guaranteed |
| Cycle-life prediction | No cycling/RPT/EOL predictions in main | Repeated ageing with carried-over state, periodic reference-performance tests (RPTs), measured capacity/resistance versus throughput, held-out EOL error | Numerically feasible; predictive accuracy requires suitable long-term data |
| Charge optimization | CC-CV benchmarks and model-fidelity lookup only | Executed search, candidate histories, objective/constraints, identical baseline, refined-DFN verification, robustness checks | A bounded simulated optimization is feasible; experimental benefit and safe use need further evidence |

The demo's plating-related capacity variable includes reversible inventory. It
must not be interpreted as measured irreversible capacity loss. Its high peak
temperature is an output to report, not a passed operating constraint. It uses
full OKane2022; the fidelity benchmark's four-function transport substitution is
a different parameterization. The beginning-of-life terminal-charge SOC formula
in `run_study.py` must not be copied into an ageing optimizer without accounting
for side reactions and the chosen available-capacity definition.

## Verified external starting points

1. **Executable mechanisms:** the [official PyBaMM coupled-degradation example](https://docs.pybamm.org/en/v25.4.1/source/examples/notebooks/models/coupled-degradation.html)
   demonstrates interacting mechanisms and cycling. Adapt it to the pinned
   environment and reproduce it locally before adding project claims. It is a
   model example, not calibration to the cells in this repository.
2. **Ageing measurements:** [Kirkaldy et al., Zenodo 10637534](https://zenodo.org/records/10637534)
   provides LG M50T cycling at 10, 25 and 40 degrees C, several SOC windows,
   performance summaries, RPT time series and degradation-mode analysis. Its
   cycling uses 0.3C charge; it does not directly validate 3C fast-charge ageing.
   Inspect `experiment_metadata.xlsx`, the example notebook and one condition's
   summary/RPT files first. The full record is about 49.4 GB; select the needed
   condition rather than treating the whole archive as a prerequisite. Match cell
   chemistry, electrode representation, cooling and protocol before reusing
   parameters; LG M50T and the existing Chen2020 records are not interchangeable.
3. **Published reproduction package:** [Li et al., Zenodo 14995785](https://zenodo.org/records/14995785)
   lists `Scripts_to_reproduce_paper.zip` (2.6 MB), `Source_Data.zip` (10.8 MB) and
   a larger experiment/simulation archive (835.1 MB). These are concrete code and
   data entry points for lifetime modelling. Their existence and file list were
   verified; their scripts have not been ported or executed in this release.
4. **Why capacity fit alone is insufficient:** [Li et al., arXiv:2311.05482](https://arxiv.org/abs/2311.05482)
   shows that different mechanism combinations can fit capacity/resistance while
   disagreeing on degradation modes. Include available lithium-inventory and
   active-material-loss information when evaluating mechanism claims.

Record downloaded file checksums and attribution. Review the original archive's
license before redistributing it. External code must remain attributed and
distinguished from this team's extensions.

## Implementation sequence and acceptance evidence

### 1. Establish a small, auditable ageing dataset

Select one temperature and ageing condition with multiple cells and repeated
RPTs. Preserve cell IDs, timestamps, SOC window, current sign/units, thermal
boundary, RPT capacity and resistance definitions, and cycle versus throughput
definitions. Split by entire cell, condition or a predeclared later-life window;
randomly splitting neighbouring samples leaks trajectory information.

Deliver `Ageing_Data_Manifest.csv`, `Ageing_Protocol_EN.md`, processed RPT curves,
and a reproducible ingestion script. Acceptance requires checksum checks, capacity
integration against the reported RPT values and an explicit untouched holdout.
The existing three fresh-cell discharge records cannot substitute for these data.

### 2. Fit only the parameters supported by the observations

Start from one published model and fix measured geometry and fresh-cell parameters.
Screen candidate degradation parameters for sensitivity and correlated effects.
Fit a small justified subset using training-cell RPT capacity, resistance and
available degradation-mode observations. Save parameter bounds, units, residual
weights, initial guesses and all candidate histories. Compare multiple starts and
use profile likelihood or another stated uncertainty analysis to identify weakly
constrained directions. Synthetic parameter recovery is useful for debugging,
but cannot replace experimental identification.

Deliver `Fitted_Parameters.csv`, `Fit_History.csv`, `Identifiability_EN.md` and
`Heldout_Degradation_Metrics.csv`. If two mechanisms cannot be distinguished,
report that result and reduce the fitted parameter set; do not claim complete
mechanism identification from a low voltage or capacity RMSE.

### 3. Demonstrate cycling before making a life prediction

Carry the ageing state from one cycle to the next. Do not reinitialize a fresh
cell for each cycle. Insert comparable low-rate RPTs at planned intervals and
report discharge capacity relative to the initial RPT, resistance, lithium
inventory, active-material loss and failure/termination reasons. Save checkpoints
and run a mesh/tolerance check at both fresh and aged states.

First execute a short cycling demonstration and label it as such. Then reproduce
the selected experimental duration. If EOL is defined as 80% of initial RPT
capacity, a run that never crosses that threshold must be reported as not reaching
EOL, rather than assigned a lifetime from a short extrapolation. A capacity knee
claim also needs a declared knee estimator and observed data around the knee.

Deliver `Cycle_Metrics.csv`, `RPT_Traces/`, `Cycle_Run_Status.json` and held-out
capacity/EOL errors. Passing a few simulated cycles proves continuity of the
implementation, not validated cycle life.

### 4. Build and verify a constrained charging search

Define a small parameterized protocol, such as two or three current stages plus
CV. Specify the initial state, target SOC convention, objective and operating
constraints before searching. Record every candidate, including failed/infeasible
ones, and compare against CC-CV under the same model, thermal boundary, target and
delivered charge. A numerical-fidelity selector is not this optimizer.

Use declared voltage, temperature, current and local plating-overpotential or
plating-inventory constraints appropriate to the selected model. Separator or
mean anode potential alone does not establish the worst local condition. Check
constraints over the entire trajectory and account for numerical tolerances.
Verify the best candidates on refined DFN, across initial-SOC/temperature and
parameter perturbations, and with the calibrated ageing model if claiming ageing
benefits. Reaching 80% within 900 seconds is a feasibility question, not a promised
result. If no candidate satisfies all constraints, publish that outcome.

Deliver `Optimization_Config.json`, `Candidate_History.csv`,
`Baseline_vs_Optimized.csv`, traces and `Constraint_Checks.csv`. Independent
fast-charge experiments are needed before claiming measured charging or lifetime
improvement. The Kirkaldy 0.3C ageing data alone do not provide that evidence.

## Independent team assignments

| Owner | Independent work package | Handoff | Completion criterion |
|---|---|---|---|
| Jay | Main integration, consistent SOC, solver checks, fitting interface and final constrained search | Versioned runnable code, configurations and release audit | Reproducible commands and truthful claim/evidence mapping |
| Joe | Reproduce the external cycling example in the pinned environment; adapt the protocol and export RPT/cycle metrics | Isolated cycling script, source attribution, short-run traces and continuation checks | State carries across cycles; no silent failures; outputs do not claim calibrated lifetime |
| Third teammate | Ageing-data lineage, condition selection, holdout split, RPT processing and literature evidence | Data manifest, processed training/holdout data, protocol and evidence table | Capacity and units verified; no per-record scaling fitted to the evaluation target |

Jay can begin interface work while the other two work independently. Parameter
fitting depends on the data handoff; lifetime validation and ageing-aware
optimization depend on the fit. If the remaining schedule cannot support these
dependencies, retain the validated fidelity/cost study as the core and explicitly
present degradation and optimization as incomplete extensions. Do not count the
new single-charge demo as completing the three original objectives.
