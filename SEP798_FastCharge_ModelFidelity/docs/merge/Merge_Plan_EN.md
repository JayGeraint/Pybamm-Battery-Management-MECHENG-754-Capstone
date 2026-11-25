# Merging the two PyBaMM fast-charge studies: comparison and plan

Prepared 25 November 2026 for the MECHENG 754 / SEP798 team.

- **Study J (Jay):** `JayGeraint/Pybamm-Battery-Management-MECHENG-754-Capstone`, commit `0eb1b1d` (22 Nov 2026)
- **Study W (Joe):** `SEP798_FastCharge_ModelFidelity` (Plan A package)

## 1. Summary

1. **The repository does not yet contain Joe's work.** No file in it is identical to any file in Study W, and none of W's protocols (UDDS, M50T validation, h = 50 cooling, adequacy maps, fast-charge window) appear in it. The two studies answer the same question (SPM vs SPMe vs DFN accuracy and cost for CC-CV charging of the LG M50 with Chen2020 and lumped thermal) and were developed independently.
2. **Where they overlap, they agree at low rate and disagree at 2C to 3C.** At 0.5C and 1C, DFN charge time, peak temperature and SPMe error agree closely. At 2C and 3C, Study J's DFN takes 4 to 9 minutes longer to reach 80% SOC, and its SPMe error at 2C is 5 to 7 times larger.
3. **The disagreement has one main cause, and we checked it by re-running PyBaMM.** Study J uses the plain Chen2020 set, whose particle diffusivities and electrolyte diffusivity and conductivity do not depend on temperature. Study W uses the Arrhenius versions of the same functions (shipped in PyBaMM's OKane2022 set). The cell heats to 50 to 78 °C at 2C to 3C, so W's transport improves as it warms and J's does not. When we re-ran DFN 2C at 25 °C, J's parameters gave t80 = 26.46 min on both meshes (40/160 and 20/20). W's parameters gave 21.73 min. The mesh therefore does not explain the difference; the parameters do.
4. **The speed-ups differ because they measure different things, not because one is wrong.** J reports the warm re-solve time on a fine mesh (x = 40, r = 160). W reports integrator time and total wall time including model build, on a 20/20 mesh. Our re-run at 1C and 25 °C shows SPMe warm speed-up of 4.8× at 20/20 and 24× at 40/160. The SPMe speed-up mainly reflects how finely the particles in DFN are resolved.
5. **Recommendation.** Merge into one GitHub repository (Jay's), with one frozen configuration: Chen2020 plus Arrhenius transport, the 99-condition grid, J's strict completion checks and timing split, and both validation datasets. Then re-run everything once from that configuration so that the paper has a single set of numbers.

## 2. Side-by-side comparison of set-up

| Item | Study J (Jay) | Study W (Joe) | Proposed merged choice |
|---|---|---|---|
| Models | SPM, SPMe, DFN + lumped thermal | Same | Same |
| Parameter set | Chen2020, transport properties **independent of T** | Chen2020 + Arrhenius particle and electrolyte transport (OKane2022 functions) | **W** (otherwise the temperature sweep only affects kinetics and entropic heat) |
| Heat transfer h | 10 W m⁻² K⁻¹ | 10, plus a sensitivity run at 50 | 10 baseline, keep the h = 50 sensitivity |
| Mesh | x = 40, r = 160 | x = 20, r = 20 (checked against 40/40) | 40/160 for accuracy (section 5); report speed-up at both |
| Solver | IDAKLU, rtol 1e-6, atol 1e-8, 1 thread | IDAKLU, rtol 1e-6, atol 1e-8 | Same |
| Protocol | CC-CV 4.2 V, C/20 cut-off, from 10% SOC | Same | Same |
| Grid | 4 rates × 3 T = 36 | 11 rates (0.5 to 3C) × 9 T (0 to 40 °C) = 99 | **W** grid (contains J's 12 conditions) |
| Other load cases | none | CC discharge 0.5 to 3C, UDDS ×1 and ×2 | Keep W's |
| Voltage metric | RMSE over common CC interval | RMSE over DFN CC interval | Same idea; use J's "common CC" definition |
| Screening thresholds | 20 mV, 1 °C, 60 s | 20/40 mV, 2/4 K, 5/10% t80 (adequate / marginal / inadequate) | W's three classes; state J's values as a stricter variant |
| Failure handling | Run rejected if c_e ≤ 0, steps incomplete or time-limited; failures kept | SPMe flagged non-physical when its solution breaks down | J's checks plus W's flag |
| Timing | Build, first solve, warm-solve median of 3, integrator | Wall (build + solve) and integrator, median of 4 | Report all four: build, first solve, warm solve, integrator |
| Plating indicator | min φ_s − φ_e at separator, mean value | Same, plus count of missed plating-risk cases | Same |
| Validation data | Chen2020 Zenodo, 3 × LG M50 cells, 1C discharge | LG M50T cell D, C/10 and 0.5C pulse discharge | **Both** (they are complementary) |
| Reproducibility | Lock file, SHA-256 manifest, environment record | requirements.txt, run_all scripts, MATLAB post-processing | J's practices + W's MATLAB folder |
| Degradation / optimisation | Explicitly removed from scope | Not implemented; agreed team plan assigns degradation to the teammate and GA optimisation to both | **Team decision needed** (section 6) |

## 3. Results at the 12 shared conditions

DFN reference values and reduced-model CC voltage RMSE. Full table: `merge_comparison.csv`.

| C-rate | T (°C) | DFN t80 (min) J / W | DFN peak T (°C) J / W | DFN min φ_sep (mV) J / W | SPM V-RMSE (mV) J / W | SPMe V-RMSE (mV) J / W |
|---|---|---|---|---|---|---|
| 0.5 | 10 | 84.0 / 84.1 | 15.2 / 15.5 | 0.3 / −2.0 | 30.5 / 34.7 | 2.8 / 4.0 |
| 1 | 10 | 44.0 / 44.2 | 24.7 / 24.9 | −17.5 / −17.0 | 60.5 / 53.5 | 6.3 / 7.2 |
| 2 | 10 | 28.0 / 23.7 | 41.7 / 42.0 | −58.3 / −42.2 | 126.5 / 85.7 | 52.6 / non-physical |
| 3 | 10 | 25.2 / 16.2 | 50.9 / 56.4 | −123.2 / −123.1 | 209.0 / 122.1 | failed / non-physical |
| 0.5 | 25 | 84.0 / 84.1 | 29.1 / 29.0 | 20.5 / 21.4 | 31.2 / 27.5 | 2.9 / 2.6 |
| 1 | 25 | 42.8 / 42.2 | 37.5 / 36.5 | 1.8 / 1.1 | 62.1 / 44.3 | 6.8 / 5.6 |
| 2 | 25 | 26.5 / 21.7 | 54.3 / 52.0 | −40.1 / −10.0 | 131.7 / 69.3 | 54.8 / 11.7 |
| 3 | 25 | 23.6 / 15.0 | 64.4 / 65.2 | −105.7 / −39.6 | 216.4 / 94.8 | failed / non-physical |
| 0.5 | 40 | 84.0 / 84.0 | 43.2 / 42.8 | 38.7 / 42.9 | 31.7 / 22.0 | 3.2 / 2.0 |
| 1 | 40 | 42.2 / 42.0 | 50.6 / 48.8 | 16.8 / 20.0 | 63.2 / 37.5 | 7.4 / 4.1 |
| 2 | 40 | 25.4 / 21.1 | 66.9 / 62.3 | −23.4 / 7.0 | 136.0 / 59.5 | 57.0 / 8.0 |
| 3 | 40 | 22.6 / 14.3 | 77.8 / 74.3 | −90.1 / 0.7 | 223.2 / 79.5 | failed / 15.1 |

What the table shows:

- **Agreement at 0.5C and 1C.** t80 is within 0.6 min, peak temperature within about 2 °C, and SPMe error within a few mV. Both studies reach the same conclusion here: SPMe is adequate and SPM is not.
- **Divergence at 2C and 3C.** With T-independent transport (J), electrolyte depletion is more severe. Charging hits 4.2 V earlier and spends longer in CV, so t80 is longer, the anode potential goes further negative, and SPMe breaks down already at 2C.
- **Same mechanism in both studies.** In W, SPMe breaks down when the DFN minimum electrolyte concentration falls below about 150 mol m⁻³. J's SPMe failures at 3C and its large 2C errors fit the same rule; J's parameters simply reach depletion at lower rates. This is a useful joint finding: **where SPMe fails depends on the transport parameters, so the adequacy boundary is parameter-sensitive.**
- **The 15-minute claim depends on the choice.** With W's parameters, CC-CV reaches 80% in about 15 min at 3C and 25 °C or higher (`fig12`). With J's parameters, no condition gets below 22 min. The team must settle the parameter choice before writing about the 15-minute target.

## 4. Cross-check runs (re-run in PyBaMM 26.10.1.1, 25 Nov 2026)

| Run (DFN, 2C, 25 °C) | t80 (min) | Peak T (°C) | min φ_sep (mV) | min c_e (mol m⁻³) |
|---|---|---|---|---|
| J parameters, mesh 40/160 | 26.46 | 54.3 | −40.1 | 131.6 |
| J parameters, mesh 20/20 | 26.46 | 54.2 | −40.3 | 131.0 |
| W parameters, mesh 20/20 | 21.73 | 52.0 | −10.0 | 222.6 |

The J-parameter runs reproduce J's published values, and the W-parameter run reproduces W's. **The difference comes from the parameters, not the mesh.**

| Warm solve, 1C, 25 °C | SPM (s) | SPMe (s) | DFN (s) | SPMe speed-up | SPM speed-up |
|---|---|---|---|---|---|
| Mesh 20/20 | 0.040 | 0.068 | 0.325 | 4.8× | 8.2× |
| Mesh 40/160 | 0.102 | 0.162 | 3.943 | 24× | 39× |

These timings were measured on the cloud machine, so absolute times differ from J's Windows machine. The ratios are the point. W's lower "wall" speed-up (about 1.4×) also counts model build and discretisation (about 0.4 s for SPM and 1.1 to 1.4 s for SPMe and DFN), which dominates at 20/20.

## 5. Proposed merged method (one frozen configuration)

1. **Parameters:** Chen2020 with Arrhenius particle diffusivities and electrolyte diffusivity and conductivity (OKane2022 functions, same reference values). State this explicitly in Methods, and keep J's plain-Chen2020 sweep as a short sensitivity result: "the adequacy boundary moves to lower C-rates if transport is T-independent".
2. **Mesh:** J's convergence study accepts x = 40, r = 160 under a strict screen (max CC voltage change < 2 mV). Under that screen, going from 20 to 40 points fails at 3C and 10 °C. W's own mesh check finds that 20/20 differs from 40/40 by at most 6 mV CC voltage RMSE (at 3C, 0 °C) and 0.05 K. That is small next to the 20 mV adequacy threshold, but it is not negligible. Suggestion: run the accuracy sweep at 40/160 for the final paper, since DFN is still only a few seconds per run and this removes the mesh question. Report timing at both 20/20 and 40/160, so readers see that the speed-up depends on resolution.
3. **Grid and load cases:** W's 99-condition CC-CV grid, CC discharge and UDDS, h = 50 sensitivity.
4. **Run checks:** J's `extract()` checks (positive c_e, completed CC and CV, event termination, cut-off reached), with failures kept in a failure table. Add W's "non-physical SPMe" flag where SPMe returns a solution with c_e ≤ 0.
5. **Metrics:** J's common-CC voltage RMSE and full-protocol RMSE; temperature, t80 and charge-added errors; plating indicator agreement; W's adequate / marginal / inadequate classes.
6. **Timing:** J's split (build, first solve, warm-solve median, integrator), single-threaded, one machine, nothing else running.
7. **Validation:** both datasets. Chen2020 LG M50 1C discharge, three cells (J), and LG M50T C/10 and 0.5C pulse (W). State clearly that neither covers fast charging.
8. **Outputs:** CSV + PNG from Python, plus W's `matlab/` post-processing (course requirement for MATLAB).

## 6. Scope decision needed from the team

Study J's abstract review removes degradation and charge optimisation. The team framework from 18 Nov (`Team_Framework_Merged.pptx`) kept them, as Part 2 (SEI + plating degradation, teammate) and Part 3 (15-min GA optimisation, both). Pick one before writing:

- **Option A (recommended given the Dec 10 deadline):** fidelity vs cost as the core paper (Parts 1 + validation). Add one short degradation demonstration (DFN + SEI + partially reversible plating, OKane2022, one 3C charge, already shown to solve in under 1 s) to connect the plating indicator to a lithium-plating amount. Optimisation goes to future work.
- **Option B:** full three-part framework. Feasible only if the degradation part is started now and the optimiser is kept small (for example, 2 to 3 current stages and a coarse search on DFN).

## 7. Repository and work plan

| Step | Who | When |
|---|---|---|
| Add Joe as a collaborator on the GitHub repository | Jay | now |
| Agree on sections 5 and 6 (parameters, mesh, scope) | all | by 27 Nov |
| Port W's Arrhenius parameter function, discharge and UDDS protocols, adequacy classes, h = 50 run and M50T validation into the repository via a pull request (`src/` modules, keep J's entry points) | Joe | 27–29 Nov |
| Merge J's run checks and timing split into the shared runner; regenerate the manifest | Jay | 27–29 Nov |
| Re-run the full frozen sweep once on one machine; tag the commit used for the paper | one person | 30 Nov |
| Regenerate all figures and tables from that run only (Python + MATLAB) | Joe | 1–2 Dec |
| Degradation demonstration (if Option A) or Part 2 (if Option B) | teammate | 27 Nov – 3 Dec |
| Paper draft, cross-review, rehearsal | all | 3–10 Dec |

Rules: one shared configuration file; every change goes through a pull request; all numbers in the paper come from the tagged run; failed and non-physical cases stay visible in the tables.

## 8. What each study brings

- **From Study J:** git repository, pinned environment, SHA-256 manifest, strict completion checks, clear timing definitions, DFN convergence study at three meshes, three-cell Chen2020 validation, careful abstract and claim wording.
- **From Study W:** temperature-dependent transport, a much denser 99-condition grid (gives a continuous adequacy map), discharge and UDDS cases, cooling sensitivity, plating-risk miss counts, M50T validation, the 15-minute window figure, MATLAB post-processing, slides.
