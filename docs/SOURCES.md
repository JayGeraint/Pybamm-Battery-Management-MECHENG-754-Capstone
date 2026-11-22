# Sources and evidence use

Verified for this deployment on November 17, 2026. The shared conversation supplies project context; it is not a substitute for primary scientific evidence.

1. **Project conversation.** [Claude shared chat](https://claude.ai/share/23665522-511d-4eb5-8baa-f448bef8e1e4). The final discussion selects Option A: model fidelity versus cost without degradation. Earlier plating/optimization suggestions were superseded in that discussion.
2. **Chen et al. (2020).** [Development of Experimental Techniques for Parameterization of Multi-scale Lithium-ion Battery Models](https://doi.org/10.1149/1945-7111/ab9050), Journal of The Electrochemical Society 167, 080534. Source of the LG M50 parameterization. The physical negative electrode is graphite–SiOx; the standard Chen2020 implementation represents it through effective electrode properties rather than a resolved two-phase composite model.
3. **Chen et al. dataset, version v1.** [Zenodo DOI 10.5281/zenodo.4032561](https://doi.org/10.5281/zenodo.4032561). Three cell files, CC-CV charging and several discharge rates, with current, voltage, cell-surface temperature and chamber temperature. CC BY 4.0 per repository metadata. Raw files and metadata are included with attribution; checksums match the repository. The source files show approximately 1.5 A charging, which is 0.3C for the 5 Ah cell.
4. **Marquis et al. (2019).** [An asymptotic derivation of a single particle model with electrolyte](https://doi.org/10.1149/2.0341915jes), Journal of The Electrochemical Society 166, A3693–A3706. [Author manuscript](https://arxiv.org/abs/1905.12553). Basis for explaining the systematic electrolyte correction and the conditions behind reduced-model approximations. Do not describe SPMe as simply having no spatial information.
5. **Sulzer et al. (2021).** [Python Battery Mathematical Modelling (PyBaMM)](https://doi.org/10.5334/jors.309), Journal of Open Research Software 9(1), 14. Software architecture and citation for the simulation platform.
6. **PyBaMM 26.10.1.1 model comparison.** [Compare lithium-ion battery models](https://docs.pybamm.org/en/pybamm-v26.10.1.1/source/examples/notebooks/models/compare-lithium-ion.html). Confirms existing SPM/SPMe/DFN implementations and that a basic comparison is established practice.
7. **PyBaMM 26.10.1.1 thermal models.** [Thermal models](https://docs.pybamm.org/en/pybamm-v26.10.1.1/source/examples/notebooks/models/thermal-models.html). Lumped energy balance and the role of heat-transfer coefficient, cooling area and volume. The locally installed Chen2020 parameter set was additionally inspected: both electrode entropic-change parameters are zero and h=10 W m^-2 K^-1 by default.
8. **PyBaMM experiments.** [Run experiments](https://docs.pybamm.org/en/latest/source/examples/notebooks/getting_started/tutorial-5-run-experiments.html). Documents CC/CV instructions, voltage/current termination and initial-value simulation workflows. Actual compatibility was verified with the pinned installed version.

## Claim boundaries

- DFN comparison measures model-to-model agreement, not experimental truth.
- The downloaded dataset checks lower-rate discharge response; it does not validate the entire fast-charge/temperature matrix.
- The present implementation has no SEI growth, lithium-plating kinetics, loss of active material, ageing cycles, observer, optimizer or closed-loop controller.
- The zero-anode-potential indicator is distinct from intercalation reaction overpotential and is not a measured plating rate.
- Novelty of a future journal manuscript would require a fuller literature review. This deployment does not claim the first comparison or a previously unstudied operating boundary.

## Suggested literature evidence matrix

For each additional paper, record: DOI; cell chemistry; parameter source; model equations/assumptions; operating range; measurements used; calibration split; held-out test; reported metric; and the exact claim it supports in this project. Distinguish author-reported findings from your inference.
