# Team responsibilities and delivery plan

November 24 update: this remains the core fidelity-study plan. The independent
ageing-data and cycling-extension assignments, with concrete handoffs and
acceptance evidence, are in [IMPLEMENTATION_EVIDENCE_EN.md](IMPLEMENTATION_EVIDENCE_EN.md).
Use [RELEASE_20261124_EN.md](RELEASE_20261124_EN.md) for current code and results.

This plan assigns you the modelling and integration lead, with two independent workstreams for teammates who can handle data analysis and literature writing. It provisionally uses the report's December 10, 2026 deadline, which has not been separately confirmed. No messages have been sent to teammates.

| Owner | Approximate share | Independent scope | Deliverables |
|---|---:|---|---|
| You | 45% | Modelling, numerical verification, charging sweep, shared parameters and integration | Frozen code and configuration, 36-case outcome set, main methods section and final report |
| Teammate A | 30% | Experimental-data audit, measured-response comparisons and error analysis | Data dictionary, cleaning audit, validation figures and validation section |
| Teammate B | 25% | Literature synthesis, model assumptions and analysis of exported results | Evidence matrix, model-comparison table, accuracy/cost maps, introduction and discussion drafts |

Assign the A/B labels to the two teammates as convenient. Both can start from the supplied experimental data, cleaning scripts and simulation outputs without waiting for new model development.

## Task brief for teammate A

**Goal:** Determine how closely the unfitted parameter set reproduces measured discharge voltage, and identify the operating conditions supported by the data.

1. Read `data/README.md` and run `prepare_data.py`. Check the MD5 hashes, the header on line 14, C/D current-direction codes, duplicate timestamps and temperature units. Deliver a data dictionary and a one-page quality assessment.
2. Inspect steps 7, 12, 17 and 22. Confirm that they represent approximately 0.1C, 0.5C, 1C and 1.5C discharge, with approximately two hours of preceding rest. Do not label the approximately 0.3C charging steps as 3C.
3. Run `validate_data.py --steps 7 12 17 22 --out results/teamA_validation`. Report voltage RMSE, maximum error, comparison-time coverage and cutoff-time error for every cell, rate and model. Do not extrapolate beyond model termination.
4. Prepare measured/modelled voltage overlays and residual plots for the near-room-temperature measurements. Treat temperature comparison as exploratory, distinguishing measured surface temperature from modelled volume-average temperature.
5. Draft a 600–900-word validation section explaining initialization, the current approximation, thermal boundaries and the relationship between the dataset and the parameterization paper. Before fitting any parameters, propose a split using cell02 for calibration and cell03/04 for evaluation. Retain the unfitted results as the baseline.

**Acceptance criteria:** Results can be regenerated from the original files; each figure states the cell ID, step, rate, temperature and units; failed or incompletely covered cases remain in the results table; no claim implies that these data validate fast-charge lithium plating.

## Task brief for teammate B

**Goal:** Explain the physical reasons for model differences and turn the sweep outputs into evidence that answers the research question.

1. Start with the primary sources in `SOURCES.md`. Prepare an evidence matrix covering 6–8 relevant papers or official resources. Include the research question, model assumptions, cell/parameter source, operating conditions, validation method, usable finding and DOI. Prioritize the SPMe derivation, Chen parameterization paper and PyBaMM paper.
2. Build an SPM/SPMe/DFN comparison table covering particle diffusion, electrolyte dynamics, through-electrode reaction distributions, thermal treatment and computational cost. Do not describe SPMe as having no spatial information.
3. Analyze the exported CSV files and use `plot_results.py` to generate figures. Use `comparisons.csv` for CC voltage-RMSE maps, temperature differences, timing distributions and model-selection tables. Identify DFN as a numerical reference and the primary voltage-evaluation interval as the common CC interval.
4. Select two cases illustrating differences between terminal-voltage agreement and anode-interface indicators. Check that mean and interface quantities are not confused, and document numerical uncertainty and parameter assumptions near zero potential.
5. Draft a 500–700-word introduction and a 500–700-word discussion. Frame the contribution as operating-condition-dependent model selection. Avoid claiming the first three-model comparison or assuming one model must outperform the others on every metric.

**Acceptance criteria:** Physical and literature claims have accessible sources; figures derive from the frozen CSV outputs; timing distinguishes first and warm solves and identifies the hardware; unfavorable outcomes remain visible.

## Your integration responsibilities

1. Confirm the research question and title. Maintain `configs/` and `run_study.py` as the shared model definition, avoiding three independently modified versions.
2. Review mesh and solver-tolerance results and freeze the production configuration. Use accepted result directories for final claims, and label diagnostic or failed cases explicitly.
3. Own the charge-rate and temperature sweep. If an extension is useful, prioritize heat-transfer sensitivity at h=5/10/20 W m⁻² K⁻¹ or common-current replay before adding SEI mechanisms or an optimizer.
4. Combine A's measured-data evidence with B's physical interpretation. Write the methods, central results narrative and conclusion.
5. Organize a rehearsal with five minutes per person: A explains the data, B explains the model assumptions, and you explain the experiment design and interpretation boundaries.

## Suggested schedule

All dates below are in 2026.

| Dates | You | Teammate A | Teammate B | Integration gate |
|---|---|---|---|---|
| Nov 17–19 | Reproduce setup and confirm scope | Data dictionary and quality audit | Core literature and model assumptions | Each person can run their entry point |
| Nov 20–23 | Numerical checks and main sweep | Four-rate measured-data comparisons | Baseline plots and evidence matrix | Freeze methods |
| Nov 24–28 | One focused sensitivity, if needed | Residual and initialization checks | Accuracy/cost maps and interpretation | Freeze main results |
| Nov 29–Dec 3 | Integrate methods and results | Finalize validation section | Finalize introduction and discussion | Complete first draft |
| Dec 4–7 | Check figures, numbers and claims | Audit data and units | Audit citations and model table | Cross-review |
| Dec 8–10 | Rehearse and submit | Prepare data questions and answers | Prepare physical explanations | No additional model scope |

## Collaboration contract

- You maintain the shared model and configuration. A owns `prepare_data.py` and `validate_data.py`; B owns figures and literature/discussion drafts. Record any shared parameter change before integrating it.
- Use a new output directory for each run. Exchange configurations, versions, CSV files and figures rather than screenshots alone.
- Every two days, report completed deliverables, findings or problems, and concrete dependencies. Reading a number of papers is not itself an acceptance criterion.
- Measure formal performance on the same machine with the same configuration. Teammates' machines support reproduction checks; do not pool their timings into one speedup claim.
- Prepare all deliverables in English. The implementation guide may retain Chinese–English parallel explanations.
