# PyBaMM 项目分阶段实施指南 PyBaMM implementation guide

本指南说明如何运行已部署的三模型研究、理解比较指标、验证结果并完成报告。核心问题是：在给定倍率、环境温度和热边界下，SPM 或 SPMe 能以多大的误差替代 DFN，计算成本又是多少？所有充电扫描都是数值仿真；另有单独的真实放电数据比较入口。

This guide explains the deployed models, reproducible execution, metrics, verification and report preparation. The central question is how SPM and SPMe trade prediction differences against computational cost relative to DFN under specified charging and thermal conditions. Charging sweeps are simulations; measured-discharge comparisons are handled separately.

## 阶段一 固定研究问题 Stage 1 Define the study

**中文操作：** 采用相同 Chen2020 参数的 SPM、SPMe、DFN，全部开启 lumped thermal。初始 SOC=0.1，初始温度等于环境温度，恒流充至 4.2 V，再恒压至 C/20。主矩阵为 4 个倍率 × 3 个温度 × 3 个模型，共 36 个组合。先完成这一主线，退化、状态估计器和充电优化属于后续范围。

**English:** Use the same Chen2020 parameters and lumped thermal option for all three models. Start at SOC 0.1 and ambient temperature, charge at constant current to 4.2 V, then hold 4.2 V until C/20. The main matrix contains 36 combinations: four rates, three temperatures and three models. Complete this study before adding degradation, observers or charge optimization.

| 固定项 Item | 设置 Setting | 含义 Meaning |
|---|---|---|
| Cell/parameters | LG M50 / Chen2020 | 同一电芯参数 Same parameterized cell |
| Nominal capacity | 5 Ah | 1C=5 A，3C=15 A |
| Charge rates | 0.5, 1, 2, 3C | 模型研究工况，不是实物电芯操作建议 Simulation conditions |
| Ambient and initial temperature | 10, 25, 40°C | 每次重新初始化 Fresh initialization |
| Initial SOC | 0.1 | PyBaMM 电极化学计量初始化 Stoichiometric initialization |
| CC/CV limits | 4.2 V / C/20 | 各模型相同控制规则 Same control policy |
| Heat transfer h | 10 W m⁻² K⁻¹ | 固定假设，需报告 Fixed modelling assumption |
| Cooling area / volume | 0.00531 m² / 2.42×10⁻⁵ m³ | Chen2020 的集总热输入 Thermal inputs |
| Solver | IDAKLU, one thread | 固定求解器配置 Controlled solver settings |
| Tolerances | rtol 10⁻⁶, atol 10⁻⁸ | 另外做加严检查 Tightening check provided |
| Production mesh | xₙ/xₛ/xₚ = 40 each; rₙ/rₚ = 160 each | 全模型使用同一离散设置，相应维度按模型启用 Same requested resolution |
| Output period | 2 s | 输出采样间隔，不是固定积分步长 Output sampling, not solver timestep |

**完成标准 Completion criterion：** 能用一句话解释项目问题，并明确 36 个工况是如何得到的。不要把不同模型的仿真输出称为三个不同实测数据集。

## 阶段二 环境与入口 Stage 2 Environment and entry points

原部署在 Windows / Python 3.10.11、PyBaMM 26.10.1.1 与 IDAKLU 上完成测试。仓库保留完整依赖锁定文件；每台电脑都应创建自己的虚拟环境。以下命令均在仓库根目录运行。

The original deployment was tested on Windows with Python 3.10.11, PyBaMM 26.10.1.1 and IDAKLU. Create a separate environment on each machine using the included dependency lock. Run all commands from the repository root, not from `docs/`.

**克隆后在仓库根目录运行 Run from the cloned repository root:**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe run_study.py --config configs/baseline.json --out results/my_baseline
.\.venv\Scripts\python.exe plot_results.py results/my_baseline
$pybammPython = (Resolve-Path -LiteralPath '.\.venv\Scripts\python.exe').Path
```

无需激活环境，直接指定解释器即可。如果 PowerShell 不允许 `.ps1`，用上面这些 Python 命令，不必更改系统执行策略。Windows/Python 3.10 是本次实测平台；其他 Python/操作系统需先跑基线。

Activation is optional because the commands call the environment's interpreter explicitly. If PowerShell blocks scripts, use the commands above without changing execution policy. Windows with Python 3.10 is the tested platform; verify the baseline on other platforms.

`run_study.py` 拒绝覆盖已存在的输出目录。重复运行请使用 `results/my_baseline_2` 等新名称。现成结果可直接阅读，不必先重跑全部扫描。

The runner refuses existing output directories to preserve provenance. Choose a new directory for reruns. Supplied results can be inspected immediately.

## 阶段三 理解三个模型 Stage 3 Understand the models

| 模型 Model | 保留的物理 Physics retained | 本项目用途 Role |
|---|---|---|
| SPM | 每个电极的代表性颗粒径向扩散和反应；电解液影响高度简化。Representative-particle diffusion and reaction, simplified electrolyte treatment. | 最低计算成本的比较基线 Low-cost baseline |
| SPMe | SPM 结构加电解液输运与电势修正，提供近似空间重构。Adds electrolyte transport/potential corrections. | 主降阶候选 Main reduced model |
| DFN | 电极厚度方向与颗粒半径方向耦合、局部反应及电解液输运。Resolves through-cell transport and local reaction coupled to particle diffusion. | 数值参考 Numerical reference |

三者都调用成熟的 PyBaMM 模型，不需要从头编写 PDE。SPMe 的简化限制并不等于“完全没有 x 方向信息”；本版本可输出负极隔膜界面处的固液相电势差。应比较实际输出，不能先认定它一定与 DFN 一致或一定失效。

Use PyBaMM's implementations rather than rewriting the PDEs. SPMe provides approximate through-cell information; assess its predictions instead of presupposing agreement or failure.

报告中可用颗粒扩散方程说明共同基础：

\[
\frac{\partial c_s}{\partial t}=\frac{1}{r^2}\frac{\partial}{\partial r}
\left(D_s r^2\frac{\partial c_s}{\partial r}\right).
\]

DFN 在不同电极厚度位置求解相应颗粒与局部反应；SPM/SPMe 采用代表颗粒与相应降阶闭合关系。英文解释可写：All three models describe solid-state lithium diffusion, while differing in their treatment of electrolyte transport and spatially distributed electrode reactions.

集总热平衡为：

\[
C_{th}\frac{dT}{dt}=\dot Q_{gen}-hA(T-T_{amb}).
\]

所有模型使用相同的热边界，但内部产热随模型改变。Chen2020 中正负极 OCP 熵变输入均为 0，因此该配置不包含非零可逆熵热。默认固相扩散参数还存在简化，温度扫描不能等同于全面验证了真实材料的温度依赖性。报告应记录这些参数，而不是只写 “thermal model enabled”。

All models share cooling conditions, but their generated heat can differ. In this parameter configuration the electrode entropic coefficients are zero. Thermal and transport parameter assumptions must therefore accompany temperature-dependent findings. See the parameter audit and the official thermal-model documentation in `SOURCES.md`.

## 阶段四 跑通基线 Stage 4 Run and inspect the baseline

**中文步骤：** 运行 baseline 配置；确认 `failures.json` 为空；打开 `summary.csv` 和六联图；检查充电电流为负、CC 段电压上升、CV 段电压约为 4.2 V 且电流幅值下降。终止电流应约为 −0.25 A。脚本检查数值有限、时间递增、充电符号、截止电压及 CC/CV 的事件终止。

**English:** Run the baseline and check that no cases failed. Inspect voltage, current, temperature, nominal SOC and anode indicators. Charging current is negative; the CV stage should remain near 4.2 V as current magnitude falls toward 0.25 A. The runner checks finite values, increasing time, current sign and successful event termination.

原始 `results/baseline` 是首次 40/40 网格的部署检查，作为过程记录保留；正式分析使用 `results/sweep` 中 40/160 网格的 1C/25°C 案例。目录中的 `config.json` 是判定某次结果使用哪套设置的依据。

The original baseline folder retains the initial coarse deployment check. Use the 1C/25°C case in the production sweep for final findings. Each folder's `config.json` identifies its actual settings.

**SOC 特别说明 SOC definition：** `initial_soc=0.1` 用于电极初态；输出 `soc_nominal = 0.1 + Q_added/5 Ah` 是名义容量库仑计量代理，不是独立 SOC 估计或真实可用容量测量。没有副反应时，同一恒流下该量由输入决定，不能把相同 SOC 曲线当作模型精度优势。它在满充末端可能略超过 1，不应偷偷裁剪。`time_to_80_nominal_soc_s` 指这一明确口径达到 0.8 的时间。

The reported nominal SOC is a coulomb-counted proxy based on 5 Ah. It is not an independent state estimate and can exceed unity slightly because nominal capacity and the parameterized stoichiometric capacity are not identical. Do not silently clip it or claim SOC-estimation accuracy from it.

## 阶段五 数值验证 Stage 5 Numerical verification

```powershell
& $pybammPython run_study.py --config configs/baseline.json --convergence --out results/my_convergence
```

脚本在 1C/25°C 与 3C/10°C 比较三层网格：x/r = 20/80、40/160、80/320，再在生产网格加严到 rtol=10⁻⁸、atol=10⁻¹⁰。检查共同恒流段电压最大差 <2 mV、温度最大差 <0.1°C、CC 截止时刻差 <2 s、界面负极电位最大差 <2 mV。这里是项目自行设定的数值标准。

The convergence routine compares three mesh levels and tighter solver tolerances at a baseline and a cold/high-rate corner. Acceptance depends on production-to-fine changes and tolerance sensitivity, not on every coarse-grid comparison passing. These are project-specific numerical criteria, not an industry standard.

已经执行的 `convergence_refined` 表明生产网格通过上述两个检查点。它不证明每个任意工况都收敛；若改到 4C、更低温或新参数集，应补做对应角点的网格检查。`convergence` 是此前 40/40 网格未全部达标的记录，不作为正式参考。

The accepted checks support the deployed range at the sampled conditions. New extremes or parameter changes require new numerical checks. Keep the earlier failed checks as an audit record, and do not use them as the accepted reference.

## 阶段六 工况扫描与计时 Stage 6 Sweep and timing

日常先用 `configs/core.json`，它包含已在正式扫描中成功的 27 个 0.5–2C 组合。`configs/sweep.json` 加入 3C 压力案例，当前预计会记录 3 个 SPMe 失败并返回非零状态；这三个点应留在研究结果中。

For routine execution, `configs/core.json` contains the 27 successful 0.5–2C combinations. The full sweep adds the 3C stress cases and is expected to report three SPMe failures with a nonzero exit status. Retain these stress-case outcomes in the study.

```powershell
& $pybammPython run_study.py --config configs/sweep.json --out results/my_sweep
& $pybammPython plot_results.py results/my_sweep
```

每个组合独立构建；首次求解后，在同一已构建 Simulation 上从同一初态重复三次，不传入 `starting_solution`，取热运行墙钟时间中位数。分别保存 build、first solve、warm solve 与求解器内部时间。导出 CSV、计算指标及画图不计入 solve wall time。PyBaMM 导入时间也不在 build 计时内。

Each combination is built independently. After a first solve, the built simulation is solved three times from the same initial state. The median warm wall time is the primary timing metric; build, first-solve and integrator times are recorded separately. Export, metric calculation, plotting and Python import are excluded from that solve timing.

`speedup = t_DFN / t_model`；`saved_pct = (1 − t_model/t_DFN) ×100%`。相同 C-rate/温度配对比较，不能用不同工况的最快时间拼出加速比。尽量关闭其他繁重计算。计时结果反映当前网格、求解器和硬件；它不是内在模型常数，也不证明嵌入式实时控制可用。

Pair timings within the same operating condition. Runtime depends on hardware, solver, mesh and simulation duration. The comparison uses matched discretization settings, not independently optimized meshes for each model. Report that design choice when interpreting speedup.

每个案例结束即写结果，失败时保留错误并继续其他案例；最后返回非零状态。必须先看 `failures.json`、`run_status.json` 和预期 36 行，再解释汇总图。失败的案例不能被当作零误差或最佳性能。

Results are saved case by case. Failed cases remain explicit, and the final process returns a nonzero status when failures occur. Check completeness before interpreting maps.

## 阶段七 评价指标 Stage 7 Metrics and interpretation

电压主指标在双方共同恒流区间，以均匀 2 s 时间网格计算：

\[
RMSE_V=\sqrt{\frac{1}{N}\sum_i(V_{model}(t_i)-V_{DFN}(t_i))^2}.
\]

Uniform resampling prevents adaptive solver output density from weighting the metric. Interpolation is restricted to the shared interval; no extrapolation beyond an endpoint is used.

| 输出列 Metric | 应如何解释 Interpretation |
|---|---|
| voltage_cc_mv_rmse | 共同恒流输入下的主要电压误差 Primary voltage metric under common CC current |
| voltage_full_mv_rmse | 辅助指标；CV 固定电压会压低它 Secondary metric diluted by imposed CV voltage |
| temperature_c_max_abs | 全共同区间的集总温度最大差 Maximum lumped-temperature difference |
| current_a_rmse | CV 电流轨迹与切换时机差异 Includes CV-current and switching differences |
| cc_end_error_s | 转入 CV 的时间误差 CC-to-CV transition difference |
| charge_end_error_s | C/20 终止时刻误差 End-of-charge difference |
| time_to_80_error_s | 名义 SOC 代理达到 80% 的时间差 Time-to-target under the documented proxy |
| charge_added_error_ah / pct | 各自终止时累计充入电量差，不是循环容量衰退 Delivered-charge difference, not capacity fade |
| anode_mean_mv / anode_separator_mv | 同一位置定义的模型内部指标差 Model-internal indicator differences |
| warm_wall_speedup | 已构建模型的重复求解加速比 Warm simulation speedup |

进入 CV 后模型电流不再相同。因此完整曲线比较回答“同一充电规则产生的响应差异”，不等同于全程相同输入下的模型误差。若需要严格相同输入，下一步可回放同一实测电流，或回放 DFN 电流并单独处理触发电压事件的提前终止。

During CV the models generate different currents. Full-trajectory differences therefore measure behavior under the same control policy, not identical current input. A common-current replay is a useful optional extension.

项目示例筛选线为 CC RMSE≤20 mV、温度最大差≤1°C、到 80% 时间误差≤60 s。`meets_project_screen` 只是这三项条件的合取，不包含负极电位的安全判定。应同时给连续误差值，避免把阈值附近变化说成普遍的“模型失效”。这些阈值可在最终实验设计讨论中解释，但不能看完结果后为让模型通过而随意修改。

The screening thresholds are illustrative project criteria, not safety standards. Report continuous errors alongside pass/fail labels. A model passing external-response criteria may still disagree on internal indicators.

## 阶段八 实测数据比较 Stage 8 Measured-data comparison

```powershell
& $pybammPython prepare_data.py
& $pybammPython validate_data.py --steps 17 --out results/my_validation_1C
# 全部放电倍率 Full discharge set
& $pybammPython validate_data.py --steps 7 12 17 22 --out results/my_validation_all
```

已下载原始数据并校验 MD5，三个文件各约 6300 行。清洗时读取真正表头、用 Md 列转换电流方向、保留重复时间标志。该数据的放电覆盖约 0.1、0.5、1、1.5C；充电约 0.3C，不能验证主扫描的 2C/3C 快充。

The downloaded files are checksum-verified. Cleaning identifies the actual header, derives current sign from the operating mode and flags duplicate timestamps. Discharge rates cover approximately 0.1–1.5C, while charging is approximately 0.3C.

验证脚本用放电前静置电压映射模型平衡初态，初温来自测量，环境温度取该段平均值，电流取该恒流段实测均值。这个做法包含初始化假设，并未重新拟合电化学参数。记录电流均值近似的最大偏差；只在共有时间上算电压 RMSE，并报告覆盖率、截止时刻误差。若只覆盖大部分区间，应同时展示遗漏尾段，不能仅挑低误差部分。

The validation script infers the initial equilibrium state from preceding rested voltage and uses measured initial temperature, mean chamber temperature and mean discharge current. It performs no parameter fitting. Shared-interval errors are accompanied by time coverage and cutoff-time error, preventing an early model termination from being hidden.

这些是参数化论文配套的验证数据。它们可用于复现与配置检查，但不是独立化学体系的外部验证。若之后调参，先指定校准电芯与留出电芯；不要把同一条已拟合轨迹再称为预测验证。

These measurements belong to the parameterization study. They support a reproduction check, not an independent validation on a new chemistry. Any calibration extension needs an explicit held-out-cell protocol.

## 阶段九 图表与报告 Stage 9 Figures and report

建议报告正文围绕以下顺序展开：研究问题与模型选择价值 → 统一方法 → 数值检查 → 实测放电检查 → 36 工况精度与计算成本 → 负极指标案例 → 工程含义。完整英文分工见 `TEAM_TASKS_EN.md`，英文摘要审阅与改稿见 `ABSTRACT_REVIEW_EN.md`，英文结果说明见 `RESULTS_SUMMARY_EN.md`。只有本操作指南保留中英对照。

Organize the report around the question, controlled methods, numerical verification, measured-data checks, accuracy/cost maps and selected internal-state cases. The English-only handoff documents are `TEAM_TASKS_EN.md`, `ABSTRACT_REVIEW_EN.md` and `RESULTS_SUMMARY_EN.md`. This implementation guide is the only bilingual deliverable.

推荐 6 张主图：研究流程及模型假设图；代表性充电六联图；网格/容差变化表或图；实测放电电压与残差；倍率温度精度地图；运行时间与负极指标案例。图题说明参数集、SOC 口径、工况、网格、DFN 参考及计时定义。

Suggested main figures are the workflow/model assumptions, representative charging trajectories, numerical checks, measured-voltage overlays/residuals, operating-condition error maps and timing/internal-indicator comparisons. Every figure should state enough context to be interpreted independently.

结论只使用已完成结果：不要写容量寿命、析锂量、真实安全边界或控制器实时能力。未来扩展优先热边界敏感性、公共电流回放或小规模参数不确定性；当前模型主线不需要加入 SEI 才能完成课程报告。

Conclusions should describe completed comparisons. Thermal-boundary sensitivity, common-current replay or focused parameter uncertainty are natural extensions after the core study is complete.
