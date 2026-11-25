# Verified deployment results

Historical record: the numbers below use the November 17 code and nominal-SOC
time metric. For the current implementation, consistent electrode-window SOC,
fresh benchmarks and validation, see [the November 24 release](RELEASE_20261124_EN.md).

Date: November 17, 2026. The numbers below come from executed simulations and measured-data comparisons, not proposed targets. Production charging results are in `results/sweep`, with configuration and environment records.

## Completed work

- Established a project virtual environment with PyBaMM 26.10.1.1, IDAKLU and pinned dependencies.
- Executed the three-model baseline, DFN mesh/tolerance checks at two conditions, and all 36 planned charging combinations.
- Completed 33 combinations. SPMe at 3C and 10, 25 and 40°C did not complete; these cases are recorded separately and excluded from valid error/timing comparisons.
- Rechecked electrolyte concentration in all 33 completed cases; every minimum was positive. The lowest value was approximately 7.05 mol/m³ in SPMe at 2C, indicating proximity to electrolyte depletion. Positive concentration alone does not establish full physical validity.
- Downloaded, checksum-verified and normalized three public LG M50 files. Completed nine measured 1C discharge comparisons across three cells and three models.
- Generated twelve six-panel charging figures, an accuracy/cost map and three experimental-comparison figures.

## Production baseline at 1C and 25°C

Matched conditions: initial SOC 0.1, nominal capacity 5 Ah, 4.2 V/C/20 CC-CV charging, h=10 W m⁻² K⁻¹, x=40 and r=160, IDAKLU, and the median of three warm solves.

| Metric | SPM | SPMe | DFN |
|---|---:|---:|---:|
| CC voltage RMSE relative to DFN / mV | 62.09 | 6.83 | Reference |
| Maximum temperature difference relative to DFN / °C | 5.47 | 0.455 | Reference |
| Warm wall time / s | 0.0457 | 0.1068 | 1.8128 |
| Speedup relative to DFN | 39.64× | 16.98× | 1× |
| Peak lumped temperature / °C | 32.30 | 37.61 | 37.51 |
| Time to nominal 80% SOC / min | 42.00 | 43.07 | 42.81 |
| Minimum separator-interface anode potential difference / mV | 19.63 | −8.19 | 1.77 |

SPMe agrees closely with DFN in terminal voltage in this case, yet the minimum separator-interface indicators differ in sign. This illustrates why terminal-voltage agreement does not guarantee agreement in an internal indicator. No plating reaction is solved and no anode potential is measured here; neither value is an experimental plating observation.

Timing is specific to this machine and discretization. SPMe's earlier coarse-grid baseline speedup was approximately 8.30×, compared with 16.98× in this production case. Do not mix those configurations or timing results. `final_smoke` checks the finalized runner; its timing is not the formal benchmark because other diagnostic work was running concurrently.

## Sweep findings

| Model and sampled conditions | Observed finding |
|---|---|
| SPMe, 0.5C and 1C, at 10/25/40°C | CC voltage RMSE of 2.81–7.39 mV; maximum temperature differences of 0.080–0.482°C; warm speedups of 15.58–22.75×. |
| SPMe, 2C, at 10/25/40°C | CC voltage RMSE of 52.56–56.99 mV; maximum temperature differences of 5.84–6.93°C; low electrolyte concentrations. The lower-rate accuracy finding does not extend to these cases. |
| SPMe, 3C, at all three temperatures | CC-CV did not complete. Returned partial states included negative electrolyte concentrations. No valid complete-protocol RMSE or speedup is reported. |
| SPM, across the sampled 0.5–3C grid | CC voltage RMSE of 30.51–223.15 mV. Computation is fast, but the model does not satisfy the project's 20 mV screening threshold. |

These findings apply to sampled conditions, not a universal or precisely located rate boundary. An additional 1.25/1.5/1.75C sweep, retaining the same parameters and numerical checks, could refine the transition without adding new physics.

All twelve IDAKLU diagnostic combinations remained incomplete after tightening tolerances, refining the through-cell mesh or changing the particle mesh. See `results/spme_idaklu_diagnostics/diagnostics.csv`. This supports reporting a configuration-specific admissibility/solver failure; it does not establish the time of a real-cell failure. An alternative-solver exploration did not yield a completed result and is not an accepted workaround.

The DFN 3C cases require approximately 25.20, 23.62 and 22.55 minutes to reach the nominal 80% SOC proxy at ambient temperatures of 10, 25 and 40°C, respectively. They do not demonstrate a 15-minute target. The 3C/40°C case reaches a modelled peak of 77.81°C. The implementation has no thermal-runaway or hardware-protection logic, so numerical completion is not a validated charging recommendation.

## Numerical checks

Changes from the production mesh to the finer x/r=80/320 mesh were:

| Condition | Maximum CC voltage change | Maximum temperature change | CC transition change | Maximum separator indicator change |
|---|---:|---:|---:|---:|
| 1C / 25°C | 0.301 mV | 0.0128°C | 0.568 s | 0.096 mV |
| 3C / 10°C | 0.880 mV | 0.0291°C | 0.397 s | 0.285 mV |

Both production-to-fine checks and both solver-tolerance checks passed the preset project criteria. Earlier unsuccessful coarse-grid checks are preserved in `results/convergence`. This is numerical evidence at selected conditions, not a mathematical convergence proof over every possible input.

## Preliminary measurement comparison

The table reports 1C discharge voltage RMSE in mV. Initial equilibrium states were inferred from preceding rested voltages without parameter fitting. Each comparison covers 100% of the corresponding measured discharge duration.

| Cell | SPM | SPMe | DFN |
|---|---:|---:|---:|
| cell02 | 121.74 | 73.36 | 70.13 |
| cell03 | 114.82 | 66.90 | 63.54 |
| cell04 | 113.48 | 65.47 | 62.12 |

This is a preliminary reproduction check on the parameterization study's data, using a separately documented 40/40 mesh, mean measured discharge current and mean chamber temperature. It does not support an experimental error below 20 mV. The 6.83 mV model-to-model result must not be presented as agreement with measurements.

Teammate A's next task is to examine lower rates, initialization, measured-current replay and thermal assumptions before deciding whether a small held-out calibration exercise is justified.

## Project decision

The scoped study is feasible and already has a working evidence chain. Frame the main contribution as model accuracy and computational cost over the tested conditions, retain 3C as a demanding applicability case, and present measured-data agreement as a separate evidence layer. Improve validation and interpretation before expanding into ageing or control optimization.
