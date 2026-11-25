# Revised abstract (aligned with Plan A)

**Suggested title:** When Is a Single-Particle Model Good Enough for Fast Charging? Fidelity and Cost of SPM, SPMe and DFN for a 21700 Cell

## Abstract (≈ 320 words)

Fast charging of electric-vehicle batteries is limited by electrolyte transport, heat generation and the risk of lithium plating, so a battery management system needs models that are both fast and trustworthy in exactly these conditions. Reduced-order electrochemical models such as the single particle model (SPM) and the single particle model with electrolyte (SPMe) are attractive for real-time use, but the range of conditions over which they remain faithful to the Doyle–Fuller–Newman (DFN) model is rarely quantified. This study asks, for a commercial 21700 cell (LG M50, Chen2020 parameter set in PyBaMM, no recalibration), when SPM and SPMe stop being adequate substitutes for DFN during constant-current constant-voltage (CC-CV) charging, and how much computation each saves. All three models share the same lumped thermal model with Arrhenius-dependent kinetics and transport, and are simulated for 0.5C–3C charging at 0–40 °C ambient temperature (99 conditions), complemented by constant-current discharge and a UDDS drive cycle. With DFN as the reference, each reduced model is scored on terminal-voltage RMSE, peak-temperature error, time to 80 % state of charge and solver time, and the negative-electrode potential at the separator is used as a lithium-plating risk indicator. The parameter set is checked against measured LG M50T terminal voltage and surface temperature. SPM is never fully adequate for charging: its voltage error reaches 158 mV, it under-predicts peak temperature by up to 24 K, and it reports a safe anode potential in 48 of the 69 conditions where DFN predicts plating risk. SPMe stays within 16 mV and 0.8 K of DFN wherever it remains physical, and its plating indicator errs on the conservative side, but it fails abruptly once DFN predicts severe electrolyte depletion (minimum concentration below about 150 mol m⁻³), which for this cell happens from 1.5C at 0 °C and from 2.5C at 25 °C. SPM and SPMe solve a CC-CV charge about 10× and 3× faster than DFN, and a drive cycle about 200× and 21× faster. The resulting adequacy map gives a simple rule: use SPMe up to the electrolyte-depletion boundary and DFN beyond it, and do not rely on SPM for fast-charge thermal or plating-risk predictions.

## Short version (≈ 190 words, if the conference template has a word limit)

Reduced-order battery models are attractive for fast-charge control, but it is rarely quantified where they stop agreeing with the Doyle–Fuller–Newman (DFN) model. For an LG M50 21700 cell (PyBaMM, Chen2020 parameters, no recalibration), the single particle model (SPM), the single particle model with electrolyte (SPMe) and DFN, all coupled to the same lumped thermal model, are compared for CC-CV charging at 0.5C–3C and 0–40 °C (99 conditions), plus constant-current discharge and a UDDS drive cycle. Each reduced model is scored against DFN on terminal voltage, peak temperature, charge time, an anode-potential plating-risk indicator and solver time, and the parameter set is checked against measured LG M50T data. SPM is never fully adequate for charging: voltage errors reach 158 mV, peak temperature is under-predicted by up to 24 K, and plating risk is missed in 48 of 69 conditions. SPMe stays within 16 mV and 0.8 K of DFN, but fails abruptly once electrolyte depletion sets in (from 1.5C at 0 °C, 2.5C at 25 °C). SPM and SPMe are about 10× and 3× faster than DFN for a charge and 200× and 21× faster for a drive cycle.

## Keywords
Lithium-ion battery; fast charging; reduced-order model; single particle model; Doyle–Fuller–Newman; PyBaMM; model fidelity; lithium plating risk

---

## 每个数字的出处（方便你核对）

| 摘要中的数字 | 含义 | 来源文件 |
|---|---|---|
| 99 conditions | 11 个充电倍率 (0.5C–3C, 步长 0.25C) × 9 个环境温度 (0–40 °C, 步长 5 °C) | `src/config.py` |
| 158 mV | SPM 恒流段电压 RMSE 的最大值 (3C, 0 °C) | `results/errors_charge.csv`, 列 `V_rmse_cc_mV` |
| 24 K | SPM 峰值温度误差的最大值 | 同上, 列 `Tpeak_err_K` |
| 48 of 69 | DFN 判定有析锂风险的 69 个工况里, SPM 有 48 个没发现 | 同上, 列 `plating_missed` |
| 16 mV / 0.8 K | SPMe 在没有崩溃的 64 个工况里的最大电压 / 温度误差 | 同上 |
| ≈ 150 mol m⁻³ | SPMe 能算的工况 DFN 最低电解液浓度都 ≥ 158, 崩溃的工况都 ≤ 145 | `results/runs_charge.csv`, 列 `ce_min` |
| 1.5C at 0 °C, 2.5C at 25 °C | SPMe 开始崩溃的倍率 | 图 `figures/fig02_adequacy_map_charge.png` |
| 10× / 3× | 充电求解器时间加速比 (4 个基准工况: SPM 8–11×, SPMe 3–4×) | `results/benchmark_summary.csv`, 列 `speedup_solve` |
| 200× / 21× | UDDS 一个循环的求解器时间加速比 | 同上 |

注意：加速比是“求解器时间”（积分器内部时间）。如果算上建模、离散化等固定开销（`speedup_wall`），充电时只有约 4× 和 1.5×。报告里要写清楚用的是哪一个。

---

## 与你原来摘要不一致的地方（中文说明）

你原来的摘要写的是一个“退化 + 可辨识性 + 标定 + 充电优化”的大项目，而现在按方案 A 实际做的是“三种模型在快充下的保真度与计算成本比较（不含退化）”。下面逐句列出需要删除或改写的地方。

| # | 原摘要中的内容 | 问题 | 方案 A 中怎么处理 |
|---|---|---|---|
| 1 | “accelerates the capacity degradation … through lithium plating and the growth of SEI film” 作为全文出发点 | 项目里没有任何 SEI 或析锂模型，也没有容量衰减 | 改为以“快充受电解液传输、产热和析锂风险限制，BMS 需要又快又可信的模型”为出发点；SEI/析锂退化放到 future work |
| 2 | “combining SEI growth, under CC-CV charging at different C-rates …” | 语法不通（两句话拼在一起），而且 SEI 没做 | 已改写成一个完整的研究问题：“when SPM and SPMe stop being adequate substitutes for DFN … and how much computation each saves” |
| 3 | “able to diagnose unusual capacity degradation caused by extreme fast charging” | 没有做诊断 | 删除 |
| 4 | “based on 21700 lithium-ion battery datasets to analyze … reference capacity changing trajectory” | 没有用容量衰减轨迹数据；只用了 LG M50T 初始寿命的 C/10 放电和 0.5C 脉冲放电数据做端电压验证 | 改为 “The parameter set is checked against measured LG M50T terminal voltage and surface temperature” |
| 5 | “apply identifiability analysis which attenuation parameters can be constrained …” | 没有做可辨识性分析 | 删除，可以放 future work |
| 6 | “The DFN model was calibrated based on the measured capacity change trajectory and incremental capacity characteristics” | 没有标定，直接用 Chen2020 参数（方案 A 明确说“不做标定”）；也没有做 ICA | 改为 “Chen2020 parameter set in PyBaMM, no recalibration”；并在报告的局限性里说明参数与实测电池有约 5% 的容量差 |
| 7 | 比较指标中的 “lithium deposition rate” 和 “predicted capacity decay inflection point cycle times” | 没有析锂速率（没有析锂模型），也没有循环寿命 / 衰减拐点 | 改为：端电压 RMSE、峰值温度误差、80% SOC 时间、负极/隔膜界面电位（析锂风险指标）、求解时间 |
| 8 | “the multi-stage constant current charging protocol was optimized … to achieve 80% SOC within 15 minutes” | 没有做充电策略优化 | 删除；改为给出“模型适用范围图”和模型选择规则。多阶段充电优化可放 future work，并说明它应该在 SPMe 的适用区域内做 |
| 9 | 时态混乱（“proposes … will … was calibrated … was optimized”） | 最终报告应统一用过去时 / 一般现在时描述已完成的工作 | 新摘要统一用一般现在时陈述结果 |
| 10 | 没提热模型、放电和 UDDS 工况 | 这些是实际做了的内容，而且热模型是 SPM 不适用的主要原因之一 | 新摘要已加入 “same lumped thermal model”、“constant-current discharge and a UDDS drive cycle” |
| 11 | 没有任何定量结果 | 会议论文摘要需要给出主要数字 | 新摘要给出了 158 mV、24 K、48/69、16 mV、0.8 K、150 mol m⁻³、10×/3×、200×/21× |

另外两点提醒：
- 方案 A 原本提到用 M50T 的 1C/3C 充电和 UDDS 实测数据做验证，但这些数据所在的网站（Zenodo / Mendeley / OSF）我这边打不开，所以实际验证用的是 C/10 放电和 0.5C 混合脉冲放电。报告里要照实写；如果你能下载到那份数据，在 `src/run_validation.py` 顶部加一行就可以重跑。
- 实测数据的来源和引用（我判断是 Kirkaldy et al., J. Power Sources 2024 的 LG M50T 老化数据集）请你在引用前核实，详见 `data/m50t/SOURCE.md`。

## 中文对照（仅供理解，不用放进报告）

快充受电解液传输、产热和析锂风险限制，因此电池管理系统需要在这些工况下既快又可信的模型。SPM 和 SPMe 等降阶模型适合实时使用，但它们在多大的工况范围内与 DFN 一致，很少被定量研究。本研究针对 LG M50 21700 电池（PyBaMM 的 Chen2020 参数，不做标定），回答：在 CC-CV 充电下，SPM 和 SPMe 什么时候不再能替代 DFN，以及各自能节省多少计算量。三种模型使用相同的集总热模型，动力学和传输参数随温度按 Arrhenius 关系变化，在 0.5C–3C、0–40 °C 环境温度（99 个工况）下充电仿真，并补充恒流放电和 UDDS 工况。以 DFN 为基准，比较端电压 RMSE、峰值温度误差、80% SOC 时间和求解时间，并用负极在隔膜处的电位作为析锂风险指标。参数用 LG M50T 实测端电压和表面温度检验。结果：SPM 在充电时从不完全适用，电压误差最高 158 mV，峰值温度低估最多 24 K，在 DFN 判定有析锂风险的 69 个工况里有 48 个报告“安全”。SPMe 在能正常求解的区域内与 DFN 相差不超过 16 mV 和 0.8 K，析锂指标偏保守，但一旦 DFN 预测电解液严重耗尽（最低浓度低于约 150 mol/m³）就会突然失效：0 °C 时从 1.5C 开始，25 °C 时从 2.5C 开始。SPM 和 SPMe 充电时比 DFN 快约 10 倍和 3 倍，UDDS 工况快约 200 倍和 21 倍。由此得到简单规则：在电解液耗尽边界以内用 SPMe，超出后用 DFN，快充的温度和析锂风险预测不要依赖 SPM。
