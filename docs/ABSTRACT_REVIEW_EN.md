# Abstract review and research scope

## Recommendation

Proceed with Option A from the final part of the shared conversation: compare SPM, SPMe and DFN for CC-CV charging, quantify accuracy and computational cost, and examine anode-potential indicators. This is a feasible three-person capstone. The current abstract combines this benchmark with degradation diagnosis, identifiability analysis, lifetime-knee prediction and charge optimization, which require substantially different evidence and implementation.

## Suggested title

**Accuracy and Computational Cost of Electrochemical Models for Lithium Ion Battery Fast Charging in PyBaMM**

The proposed title matches the implemented study. A control claim would require a controller and closed-loop evaluation. A 15-minute claim must specify the SOC window and demonstrate the target. The deployed study starts at 10% SOC and examines 0.5–3C CC-CV charging without presupposing a 15-minute result. For a 10–80% window, the ideal average current is 0.7/0.25 = 2.8C, before accounting for CV tapering. A 3C current limit alone therefore does not demonstrate the target.

## Specific revisions

| Current claim | Revision and reason |
|---|---|
| SEI growth and unusual capacity degradation | Move to future work. The main model includes neither SEI growth nor plating kinetics and cannot predict capacity fade. |
| Identifiability analysis of degradation parameters | Remove from the current scope. Published Chen2020 parameters are used without degradation fitting. |
| DFN was calibrated against capacity and IC | Do not present unperformed calibration as completed work. The deployment reproduces a published parameter set and compares outputs with data. |
| Lithium deposition rate and knee-point cycle | Remove. Potential indicators do not provide deposition rates or lifetime predictions. |
| MSCC was optimized to 80% in 15 minutes | Make this a possible later extension after the fixed CC-CV benchmark. |
| Real-time charging control | Use offline simulation or computational cost. Desktop timing does not establish embedded real-time controller feasibility. |
| An embedded question beginning with “when does SPM …” | Use a grammatical declarative phrase such as “to quantify the operating conditions under which …”. |
| “solid electrolyte interface” | Use the standard term “solid-electrolyte interphase” when discussing future degradation work. |
| Claims of rare validation or a first systematic comparison | State the specific study objective without an unsupported novelty claim. Official comparison examples and reduced-model studies already exist. |

The supplied filename identifies SEP 754, whereas the cover identifies SEP 798. Confirm the correct course code before submission. Replace “December 10rd” with “December 10th” or “December 10, 2026”, and repair corrupted hyphens or symbols. The original Word file has not been overwritten.

## Scope-based abstract

Electrochemical battery models offer different balances between physical resolution and computational cost, making model selection important for fast-charge simulation. This capstone project develops a reproducible PyBaMM framework to compare the Single Particle Model (SPM), the Single Particle Model with electrolyte (SPMe), and the Doyle–Fuller–Newman (DFN) model for an LG M50 21700 cell. All models use the Chen2020 parameter set and a lumped thermal formulation under matched constant-current–constant-voltage charging policies. The study examines charging rates from 0.5C to 3C and ambient temperatures of 10, 25, and 40 °C. Reduced-model fidelity is evaluated against a numerically checked DFN reference using constant-current voltage error, temperature differences, charging time, delivered charge, and computational cost. Separate reporting of constant-current and constant-voltage behavior avoids masking model differences through the imposed voltage limit. Mean and separator-interface negative-electrode potential differences are examined as model-based indicators of charging conditions. Published LG M50 discharge measurements provide an additional check of terminal-voltage response within the dataset’s operating range. The project aims to identify conditions in which reduced models provide a useful accuracy–cost trade-off and to distinguish terminal-voltage agreement from agreement in internal electrochemical indicators.

This version states the project scope without quantitative findings. For a final report, use the results-based version below after reconciling it with the final configuration, additional team validation and course word limit.

## Value and feasibility

The contribution is a reproducible model-selection study with controlled parameters and thermal conditions, a numerically checked DFN reference, phase-specific metrics, explicit timing definitions and reproducible figures. Implementing three existing models is not itself a new modelling theory. A capstone can make a useful engineering contribution through this benchmark; a later paper would benefit from independent measurements, parameter uncertainty, or a specific application decision.

Define the indicator precisely: Δφₙ = φₛ,ₙ − φₑ,ₙ differs from the intercalation overpotential ηₙ = Δφₙ − Uₙ. A value near or below zero can indicate modelled conditions favorable to plating, but it does not quantify lithium deposition or certify safety without plating kinetics and independent measurements. The deployed SPMe exposes an approximate separator-interface potential difference, so its spatial fidelity must be assessed rather than assumed absent.

## Abstract incorporating the executed results

The quantitative statements below come from the executed production sweep, not performance figures quoted from the literature. Update this draft if the accepted configuration or validation evidence changes.

Electrochemical model selection for battery charging requires balancing computational cost against agreement in both terminal response and internal indicators. This project implements SPM, SPMe and DFN models in PyBaMM using the Chen2020 LG M50 parameter set and a common lumped thermal formulation. CC-CV charging is examined at 0.5C, 1C, 2C and 3C and ambient temperatures of 10, 25 and 40 °C, with DFN used as a numerically checked reference. At the sampled 0.5C and 1C conditions, SPMe achieves constant-current voltage RMSEs of 2.81–7.39 mV and maximum temperature differences below 0.49 °C relative to DFN, with warm simulation speedups of 15.58–22.75 on the tested machine. At 2C, voltage RMSE increases to 52.56–56.99 mV, while the 3C SPMe configurations produce nonphysical electrolyte states and do not complete the charging protocol. A 1C case also shows that close terminal-voltage agreement can coexist with different signs of the minimum separator-interface anode-potential indicator. Separate checks against three published 1C discharge records yield DFN voltage RMSEs of 62.12–70.13 mV without parameter fitting. These results identify a useful reduced-model operating range within the tested configuration and distinguish model-to-model fidelity from agreement with measurements.

## Sources

- [Shared project conversation](https://claude.ai/share/23665522-511d-4eb5-8baa-f448bef8e1e4): the final discussion selects Option A.
- [Official PyBaMM model-comparison example](https://docs.pybamm.org/en/pybamm-v26.10.1.1/source/examples/notebooks/models/compare-lithium-ion.html): establishes that a basic three-model comparison already exists.
- [Chen et al. 2020 parameterization paper](https://doi.org/10.1149/1945-7111/ab9050): parameter source and cell characterization.
- [Marquis et al. 2019 SPMe derivation](https://doi.org/10.1149/2.0341915jes): electrolyte corrections and reduced-model assumptions.
- [Chen et al. experimental data](https://doi.org/10.5281/zenodo.4032561): source of the three-cell discharge checks.
