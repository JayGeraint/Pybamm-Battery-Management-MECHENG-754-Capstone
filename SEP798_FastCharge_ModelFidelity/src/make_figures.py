"""
All figures for the report / slides.  Run after run_sweep.py, run_benchmark.py,
run_mesh_check.py and run_validation.py.   Output: figures/*.png
"""
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm, LinearSegmentedColormap
from matplotlib.patches import Patch

import config as cfg

# ----------------------------------------------------------------------------- style
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
COL = {"DFN": INK, "SPMe": "#2a78d6", "SPM": "#eb6834", "Measured": "#9a9893"}
LW = {"DFN": 2.2, "SPMe": 1.6, "SPM": 1.6, "Measured": 3.5}
LS = {"DFN": "-", "SPMe": "-", "SPM": "--", "Measured": "-"}
STATUS = ["#0ca30c", "#fab219", "#d03b3b", "#6f6e69"]       # adequate, marginal, inadequate, failed
STATUS_LBL = ["Adequate", "Marginal", "Inadequate", "Model breakdown (c_e → 0)"]
BLUES = LinearSegmentedColormap.from_list("blues", ["#f4f8fe", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
DPI = 200

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "legend.fontsize": 9,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF,
    "savefig.bbox": "tight", "font.family": "DejaVu Sans",
})


def load(proto):
    with open(cfg.RESULTS / f"traces_{proto}.pkl", "rb") as f:
        tr = pickle.load(f)
    errs = pd.read_csv(cfg.RESULTS / f"errors_{proto}.csv")
    runs = pd.read_csv(cfg.RESULTS / f"runs_{proto}.csv")
    return tr, errs, runs


def save(fig, name):
    fig.savefig(cfg.FIGURES / name, dpi=DPI)
    plt.close(fig)
    print("saved", name)


def plot_models(ax, recs, key, xscale=1 / 60, yfun=None, models=cfg.MODELS[::-1]):
    for m in models:
        r = recs.get(m)
        if r is None or r["traces"] is None:
            continue
        t = r["traces"]
        y = t[key] if yfun is None else yfun(t)
        lbl = m + (" (failed)" if r["status"] != "ok" else "")
        ax.plot(t["t"] * xscale, y, LS[m], color=COL[m], lw=LW[m], label=lbl)


# ============================================================================ charge
def fig_cccv_traces(tr):
    cases = [(1.0, 25.0), (2.0, 10.0), (3.0, 0.0)]
    fig, axs = plt.subplots(4, 3, figsize=(13, 10.5), sharex="col")
    for j, (c, T) in enumerate(cases):
        recs = {m: tr.get((m, c, T)) for m in cfg.MODELS}
        plot_models(axs[0, j], recs, "V")
        plot_models(axs[1, j], recs, "I", yfun=lambda t: -t["I"])
        plot_models(axs[2, j], recs, "T_C")
        plot_models(axs[3, j], recs, "SOC", yfun=lambda t: 100 * t["SOC"])
        axs[0, j].set_title(f"{c:g}C CC-CV charge, ambient {T:g} °C")
        r_e = recs.get("SPMe")
        if r_e is not None and r_e["status"] != "ok" and r_e["traces"] is not None:
            axs[0, j].annotate(f"SPMe breaks down at t = {r_e['traces']['t'][-1]:.0f} s\n(electrolyte concentration → 0)",
                               xy=(r_e["traces"]["t"][-1] / 60, 4.2), xytext=(0.35, 0.35),
                               textcoords="axes fraction", fontsize=8.5, color=COL["SPMe"],
                               arrowprops=dict(arrowstyle="->", color=COL["SPMe"], lw=1))
        axs[3, j].set_xlabel("Time [min]")
        axs[3, j].axhline(80, color=INK2, lw=0.8, ls=":")
    for i, lab in enumerate(["Terminal voltage [V]", "Charge current [A]", "Cell temperature [°C]", "SOC [%]"]):
        axs[i, 0].set_ylabel(lab)
    axs[0, 0].legend(loc="lower right", frameon=False)
    fig.suptitle("CC-CV charge from 10 % SOC: DFN (reference) vs SPMe vs SPM, all with lumped thermal model",
                 fontsize=12, color=INK)
    fig.tight_layout()
    save(fig, "fig01_cccv_traces.png")


def _grid(errs, model, col, values, temps):
    Z = np.full((len(values), len(temps)), np.nan)
    for i, v in enumerate(values):
        for j, T in enumerate(temps):
            row = errs[(errs.model == model) & np.isclose(errs.value, v) & np.isclose(errs.T_amb_C, T)]
            if len(row):
                Z[i, j] = row[col].values[0]
    return Z


def fig_adequacy_map(errs, proto="charge", values=None, temps=None, fname="fig02_adequacy_map_charge.png",
                     ylabel="Charge C-rate", annot="V_rmse_cc_mV", title_extra=""):
    values = values or cfg.CHARGE_C_RATES
    temps = temps or cfg.AMBIENT_T_C
    cmap = ListedColormap(STATUS)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], 4)
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.6))
    for ax, m in zip(axs, ["SPM", "SPMe"]):
        Z = _grid(errs, m, "class", values, temps)
        A = _grid(errs, m, annot, values, temps)
        ax.imshow(Z, cmap=cmap, norm=norm, origin="lower", aspect="auto",
                  extent=[-0.5, len(temps) - 0.5, -0.5, len(values) - 0.5])
        for i in range(len(values)):
            for j in range(len(temps)):
                if Z[i, j] == 3:
                    txt = "fail"
                elif np.isfinite(A[i, j]):
                    txt = f"{A[i, j]:.0f}"
                else:
                    txt = ""
                ax.text(j, i, txt, ha="center", va="center", fontsize=7.5,
                        color="white" if Z[i, j] in (2, 3) else INK)
        ax.set_xticks(range(len(temps)), [f"{t:g}" for t in temps])
        ax.set_yticks(range(len(values)), [f"{v:g}" for v in values])
        ax.set_xlabel("Ambient temperature [°C]")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{m} vs DFN{title_extra}")
        ax.grid(False)
        for j in range(len(temps) + 1):
            ax.axvline(j - 0.5, color="white", lw=1.5)
        for i in range(len(values) + 1):
            ax.axhline(i - 0.5, color="white", lw=1.5)
    handles = [Patch(color=STATUS[k], label=STATUS_LBL[k]) for k in range(4)]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    lab = {"V_rmse_cc_mV": "voltage RMSE during the CC phase [mV]", "V_rmse_mV": "voltage RMSE [mV]"}.get(annot, annot)
    fig.suptitle("Where is the reduced model an adequate substitute for DFN?   "
                 f"(number in cell = {lab})", fontsize=12)
    fig.tight_layout(rect=[0, 0.05, 1, 0.97])
    save(fig, fname)


def fig_error_heatmaps(errs):
    values, temps = cfg.CHARGE_C_RATES, cfg.AMBIENT_T_C
    cols = [("V_rmse_cc_mV", "Voltage RMSE, CC phase [mV]", 1.0),
            ("Tpeak_err_K", "|Peak temperature error| [K]", 1.0),
            ("t80_err_pct", "|Time-to-80 % SOC error| [%]", 1.0),
            ("SOC_maxerr_pct", "Max SOC error over charge [%-pts]", 1.0)]
    fig, axs = plt.subplots(2, 4, figsize=(17, 7.6))
    for k, (col, lab, _) in enumerate(cols):
        Zs = {m: np.abs(_grid(errs, m, col, values, temps)) for m in ["SPM", "SPMe"]}
        vmax = np.nanmax([np.nanmax(Z) for Z in Zs.values()])
        for i, m in enumerate(["SPM", "SPMe"]):
            ax = axs[i, k]
            Z = Zs[m]
            im = ax.imshow(Z, cmap=BLUES, vmin=0, vmax=vmax, origin="lower", aspect="auto")
            cls = _grid(errs, m, "class", values, temps)
            for a in range(len(values)):
                for b in range(len(temps)):
                    if cls[a, b] == 3:
                        ax.add_patch(plt.Rectangle((b - .5, a - .5), 1, 1, facecolor="#d9d8d4", hatch="///",
                                                   edgecolor="#6f6e69", lw=0))
                    elif np.isfinite(Z[a, b]):
                        ax.text(b, a, f"{Z[a, b]:.1f}" if Z[a, b] < 10 else f"{Z[a, b]:.0f}", ha="center",
                                va="center", fontsize=6.5, color="white" if Z[a, b] > 0.55 * vmax else INK)
            ax.set_xticks(range(len(temps)), [f"{t:g}" for t in temps], fontsize=8)
            ax.set_yticks(range(len(values)), [f"{v:g}" for v in values], fontsize=8)
            ax.grid(False)
            ax.set_title(f"{m}: {lab}", fontsize=9.5)
            if k == 0:
                ax.set_ylabel("Charge C-rate")
            if i == 1:
                ax.set_xlabel("Ambient T [°C]")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    fig.suptitle("CC-CV charge: errors of SPM and SPMe relative to DFN (hatched = solver failure)", fontsize=12)
    fig.tight_layout()
    save(fig, "fig03_error_heatmaps_charge.png")


def fig_plating(tr, errs, runs):
    cases = [(1.0, 25.0), (2.0, 10.0), (3.0, 0.0)]
    fig = plt.figure(figsize=(15, 8.5))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05])
    for j, (c, T) in enumerate(cases):
        ax = fig.add_subplot(gs[0, j])
        recs = {m: tr.get((m, c, T)) for m in cfg.MODELS}
        plot_models(ax, recs, "phi_sep", yfun=lambda t: 1e3 * t["phi_sep"])
        ax.axhline(0, color=STATUS[2], lw=1.2, ls=":")
        ax.text(0.98, 0, "plating possible below 0 mV ", transform=ax.get_yaxis_transform(),
                ha="right", va="top", fontsize=8, color=STATUS[2],
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1))
        ax.set_title(f"{c:g}C charge, {T:g} °C")
        ax.set_xlabel("Time [min]")
        ax.set_xlim(0, min(40, ax.get_xlim()[1]))
        if j == 0:
            ax.set_ylabel("φs − φe at negative/separator\ninterface vs Li/Li⁺ [mV]")
            ax.legend(frameon=False, loc="upper right")
    # bottom: DFN minimum and the SPMe / SPM error in it
    values, temps = cfg.CHARGE_C_RATES, cfg.AMBIENT_T_C
    Zd = np.full((len(values), len(temps)), np.nan)
    for i, v in enumerate(values):
        for k, T in enumerate(temps):
            r = runs[(runs.model == "DFN") & np.isclose(runs.value, v) & np.isclose(runs.T_amb_C, T)]
            if len(r):
                Zd[i, k] = 1e3 * r.phi_sep_min_V.values[0]
    div = LinearSegmentedColormap.from_list("div", ["#b8302f", "#e66767", "#f6c9c8", "#f0efec", "#cde2fb", "#3987e5", "#1c5cab"])
    lim = np.nanmax(np.abs(Zd))
    panels = [("DFN: minimum potential [mV]", Zd, div, -lim, lim)]
    for m in ["SPMe", "SPM"]:
        E = _grid(errs, m, "phi_sep_min_err_mV", values, temps)
        lim_e = np.nanmax(np.abs(E))
        panels.append((f"{m} − DFN: error in minimum [mV]\n(red = optimistic, can miss plating;  blue = conservative)", E, div.reversed(), -lim_e, lim_e))
    for j, (title, Z, cm, vmin, vmax) in enumerate(panels):
        ax = fig.add_subplot(gs[1, j])
        im = ax.imshow(Z, cmap=cm, vmin=vmin, vmax=vmax, origin="lower", aspect="auto")
        for a in range(len(values)):
            for b in range(len(temps)):
                if np.isfinite(Z[a, b]):
                    ax.text(b, a, f"{Z[a, b]:.0f}", ha="center", va="center", fontsize=6.5, color=INK)
                elif j > 0:
                    ax.add_patch(plt.Rectangle((b - .5, a - .5), 1, 1, facecolor="#d9d8d4", hatch="///",
                                               edgecolor="#6f6e69", lw=0))
        if j == 0:
            cs = ax.contour(Zd, levels=[0], colors=[INK], linewidths=1.5)
            ax.clabel(cs, fmt="0 mV", fontsize=7)
        ax.set_xticks(range(len(temps)), [f"{t:g}" for t in temps], fontsize=8)
        ax.set_yticks(range(len(values)), [f"{v:g}" for v in values], fontsize=8)
        ax.grid(False)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Ambient T [°C]")
        if j == 0:
            ax.set_ylabel("Charge C-rate")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    fig.suptitle("Lithium-plating risk indicator: negative-electrode potential at the separator side", fontsize=12)
    fig.tight_layout()
    save(fig, "fig05_plating_indicator.png")


def fig_profiles():
    """Through-thickness gradients that the averaged models cannot represent (re-simulated here)."""
    import battery
    fig, axs = plt.subplots(1, 3, figsize=(15.5, 4.6))
    for ax, (c, T, tt) in zip(axs[:2], [(2.0, 25.0, 300.0), (1.25, 0.0, 300.0)]):
        for m in cfg.MODELS[::-1]:
            r = battery.run_case(m, "charge", c, T, profile_times=[tt])
            p = r.get("profiles", {})
            if "phi_n" not in p:
                continue
            ax.plot(p["x_n_um"], 1e3 * p["phi_n"][0], LS[m], color=COL[m], lw=LW[m], label=m)
        ax.axhline(0, color=STATUS[2], lw=1, ls=":")
        ax.set_xlabel("Distance from negative current collector [µm]")
        ax.set_ylabel("φs − φe vs Li/Li⁺ [mV]")
        ax.set_title(f"Negative electrode, {c:g}C charge at {T:g} °C, t = {tt:.0f} s")
        ax.annotate("separator →", xy=(0.98, 0.92), xycoords="axes fraction", ha="right", fontsize=8, color=INK2)
        ax.legend(frameon=False, fontsize=8, loc="center left")
    ax = axs[2]
    c, T = 3.0, 0.0
    shades = {5.0: 0.45, 15.0: 0.75, 20.0: 1.0}
    for m, ls in [("DFN", "-"), ("SPMe", "--")]:
        r = battery.run_case(m, "charge", c, T, profile_times=list(shades))
        p = r.get("profiles", {})
        if "c_e" not in p:
            continue
        for k, tt in enumerate(shades):
            ax.plot(p["x_um"], p["c_e"][k], ls, color=COL[m], lw=LW[m], alpha=shades[tt],
                    label=f"{m}, t = {p['times'][k]:.0f} s")
    ax.axhline(0, color=STATUS[2], lw=1, ls=":")
    ax.axvspan(0, 85.2, color="#f0efec", zorder=0)
    ax.text(42, 1550, "negative", ha="center", fontsize=8, color=INK2)
    ax.set_xlabel("Through-cell position x [µm]")
    ax.set_ylabel("Electrolyte concentration [mol/m³]")
    ax.set_title("Electrolyte depletion, 3C charge at 0 °C")
    ax.legend(frameon=False, fontsize=7.5, ncol=2, loc="lower right")
    fig.suptitle("Gradients across the electrode thickness that SPM ignores and SPMe only partly captures", fontsize=12)
    fig.tight_layout()
    save(fig, "fig06_through_thickness_profiles.png")


def fig_thermal_breakdown(tr):
    c, T = 3.0, 25.0
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.3))
    recs = {m: tr.get((m, c, T)) for m in cfg.MODELS}
    plot_models(axs[0], recs, "Q_tot", yfun=lambda t: t["Q_tot"] / 1e3)
    axs[0].set_ylabel("Volume-averaged total heat source [kW/m³]")
    axs[0].set_title(f"Total heat generation, {c:g}C charge at {T:g} °C")
    axs[0].legend(frameon=False)
    plot_models(axs[1], recs, "Q_ohm", yfun=lambda t: t["Q_ohm"] / 1e3)
    axs[1].set_ylabel("Ohmic heat source [kW/m³]")
    axs[1].set_title("Ohmic (electronic + ionic) part")
    for ax in axs:
        ax.set_xlabel("Time [min]")
        ax.set_xlim(0, 30)
    fig.suptitle("SPM has no electrolyte, so it misses the electrolyte Ohmic heat and under-predicts temperature",
                 fontsize=11.5)
    fig.tight_layout()
    save(fig, "fig07_heat_generation.png")


# ============================================================================ cost
def fig_cost(errs_charge):
    try:
        b = pd.read_csv(cfg.RESULTS / "benchmark_summary.csv")
    except FileNotFoundError:
        print("no benchmark yet")
        return
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axs[0]
    labels = [f"{p}\n{v:g}{'C' if p != 'udds' else 'x'} @ {T:g}°C" for p, v, T in
              b[["protocol", "value", "T_amb_C"]].drop_duplicates().itertuples(index=False)]
    cases = b[["protocol", "value", "T_amb_C"]].drop_duplicates().values.tolist()
    w = 0.26
    for k, m in enumerate(cfg.MODELS):
        ys = [b[(b.protocol == p) & (b.value == v) & (b.T_amb_C == T) & (b.model == m)].solve_s.values[0]
              for p, v, T in cases]
        xs = np.arange(len(cases)) + (k - 1) * w
        ax.bar(xs, ys, w * 0.92, color=COL[m], label=m)
        for x, y in zip(xs, ys):
            ax.text(x, y * 1.08, f"{y:.2g}", ha="center", fontsize=7, color=INK2)
    ax.set_yscale("log")
    ax.set_xticks(range(len(cases)), labels, fontsize=8)
    ax.set_ylabel("Solver time [s]  (median, log scale)")
    ax.set_title("Computational cost (IDAKLU, rtol 1e-6, 20 mesh points/domain)")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    # accuracy vs cost
    ax = axs[1]
    ch = b[b.protocol == "charge"].groupby("model").solve_s.median()
    for m in ["SPM", "SPMe"]:
        e = errs_charge[(errs_charge.model == m) & (errs_charge["class"] < 3)].V_rmse_cc_mV
        ax.errorbar(ch[m], e.median(), yerr=[[e.median() - e.quantile(0.1)], [e.quantile(0.9) - e.median()]],
                    fmt="o", ms=9, color=COL[m], capsize=4, label=f"{m} (median, 10–90 % range)")
        ax.annotate(f"{m}\n{ch['DFN'] / ch[m]:.0f}× faster", (ch[m], e.median()), xytext=(10, 6),
                    textcoords="offset points", fontsize=8.5)
    ax.plot(ch["DFN"], 0, "s", ms=9, color=COL["DFN"], label="DFN (reference)")
    ax.set_xscale("log")
    ax.set_xlabel("Median solver time, CC-CV charge [s]")
    ax.set_ylabel("Voltage RMSE vs DFN, CC phase [mV]")
    ax.set_title("Accuracy–cost trade-off (all charge cases)")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    save(fig, "fig04_cost_vs_accuracy.png")


# ============================================================================ discharge / UDDS
def fig_discharge(tr, errs):
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.6))
    for ax, T in zip(axs[:2], [25.0, 0.0]):
        for c in cfg.DISCHARGE_C_RATES:
            for m in cfg.MODELS[::-1]:
                r = tr.get((m, c, T))
                if r is None or r["traces"] is None:
                    continue
                t = r["traces"]
                ax.plot(t["Q_dis"], t["V"], LS[m], color=COL[m], lw=LW[m] * 0.8,
                        label=m if c == cfg.DISCHARGE_C_RATES[0] else None)
            rr = tr.get(("DFN", c, T))
            if rr is not None and rr["traces"] is not None:
                ax.text(rr["traces"]["Q_dis"][-1], 2.47, f"{c:g}C", fontsize=8, ha="center", va="top", color=INK2)
        ax.set_xlabel("Discharged capacity [Ah]")
        ax.set_ylabel("Terminal voltage [V]")
        ax.set_title(f"CC discharge at {T:g} °C (0.5C, 1C, 2C, 3C)")
        ax.set_ylim(2.35, 4.25)
        ax.legend(frameon=False, loc="lower left")
    fig_tmp = None
    ax = axs[2]
    temps = cfg.AMBIENT_T_C
    for m, mk in [("SPM", "o"), ("SPMe", "s")]:
        for c, a in zip(cfg.DISCHARGE_C_RATES, [0.35, 0.55, 0.75, 1.0]):
            e = [errs[(errs.model == m) & np.isclose(errs.value, c) & np.isclose(errs.T_amb_C, T)].V_rmse_mV.values
                 for T in temps]
            e = [x[0] if len(x) else np.nan for x in e]
            ax.plot(temps, e, mk + ("--" if m == "SPM" else "-"), color=COL[m], alpha=a, ms=4,
                    label=f"{m} {c:g}C")
    ax.axhline(cfg.THRESHOLDS_DISCHARGE["V_rmse_mV"][0], color=INK2, lw=0.8, ls=":")
    ax.set_yscale("log")
    ax.set_xlabel("Ambient temperature [°C]")
    ax.set_ylabel("Voltage RMSE vs DFN [mV]")
    ax.set_title("Discharge voltage error (dotted = 20 mV)")
    ax.legend(frameon=False, fontsize=7, ncol=2)
    fig.tight_layout()
    save(fig, "fig08_cc_discharge.png")


def fig_udds(tr, errs):
    fig, axs = plt.subplots(2, 2, figsize=(14, 7.2))
    for j, T in enumerate([25.0, 0.0]):
        recs = {m: tr.get((m, 2.0, T)) for m in cfg.MODELS}
        ax = axs[0, j]
        plot_models(ax, recs, "V")
        ax.set_xlim(1370 * 2 / 60, 1370 * 3 / 60)
        ax.set_title(f"UDDS x2 load at {T:g} °C — third cycle")
        ax.set_ylabel("Terminal voltage [V]")
        ax.set_xlabel("Time [min]")
        if j == 0:
            ax.legend(frameon=False, loc="lower left")
        ax = axs[1, j]
        ref = recs["DFN"]["traces"] if recs.get("DFN") and recs["DFN"]["traces"] is not None else None
        if ref is not None:
            for m in ["SPMe", "SPM"]:
                r = recs.get(m)
                if r is None or r["traces"] is None:
                    continue
                e = 1e3 * (np.interp(ref["t"], r["traces"]["t"], r["traces"]["V"]) - ref["V"])
                ax.plot(ref["t"] / 60, e, color=COL[m], lw=0.8, label=f"{m} − DFN")
        ax.set_ylabel("Voltage error vs DFN [mV]")
        ax.set_xlabel("Time [min]")
        ax.set_title(f"Error over all four cycles, {T:g} °C", fontsize=10)
        ax.legend(frameon=True, framealpha=0.95, edgecolor="none", loc="upper right")
    fig.suptitle("UDDS drive cycle (course profile, scaled to the 5 Ah cell, x2 load, 4 repeats from 80 % SOC)",
                 fontsize=12)
    fig.tight_layout()
    save(fig, "fig09_udds.png")


# ============================================================================ validation
def fig_validation():
    try:
        with open(cfg.RESULTS / "validation_traces.pkl", "rb") as f:
            st = pickle.load(f)
    except FileNotFoundError:
        print("no validation yet")
        return
    names = list(st.keys())
    fig, axs = plt.subplots(2, 4, figsize=(20, 8.4))
    for i, name in enumerate(names):
        d = st[name]["data"]
        k = st[name].get("k", 1.0)
        Qm = d["Q_Ah"][-1]
        for j, (suffix, lab, scale) in enumerate([("", "as measured", Qm), ("_aligned", f"capacity-aligned (I × {k:.3f})", Qm * k)]):
            ax = axs[i, j]
            ax.plot(d["Q_Ah"] / Qm, d["V"], color=COL["Measured"], lw=LW["Measured"], label="Measured (LG M50T)")
            for m in cfg.MODELS[::-1]:
                r = st[name].get(m + suffix)
                if r and r["traces"] is not None:
                    ax.plot(r["traces"]["Q_dis"] / scale, r["traces"]["V"], LS[m], color=COL[m], lw=LW[m] * 0.8, label=m)
            ax.set_xlabel("Depth of discharge [-]")
            ax.set_ylabel("Terminal voltage [V]")
            ax.set_title(f"{name}\n{lab}", fontsize=10)
            ax.legend(frameon=False, loc="lower left", fontsize=8)
        ax = axs[i, 2]
        t0 = 0.3 * d["t"][-1]
        t1 = t0 + (600 if "pulse" in name else 6000)
        mk = (d["t"] >= t0) & (d["t"] <= t1)
        ax.plot(d["t"][mk] / 60, d["V"][mk], color=COL["Measured"], lw=LW["Measured"], label="Measured")
        for m in cfg.MODELS[::-1]:
            r = st[name].get(m + "_aligned")
            if r and r["traces"] is not None:
                tt = r["traces"]["t"]
                mm = (tt >= t0) & (tt <= t1)
                ax.plot(tt[mm] / 60, r["traces"]["V"][mm], LS[m], color=COL[m], lw=LW[m] * 0.8, label=m)
        ax.set_xlabel("Time [min]")
        ax.set_ylabel("Terminal voltage [V]")
        ax.set_title("Zoom, capacity-aligned (dynamic response)", fontsize=10)
        ax = axs[i, 3]
        ax.plot(d["t"] / 60, d["T_C"], color=COL["Measured"], lw=LW["Measured"], label="Measured (surface)")
        for m in cfg.MODELS[::-1]:
            r = st[name].get(m)
            if r and r["traces"] is not None:
                ax.plot(r["traces"]["t"] / 60, r["traces"]["T_C"], LS[m], color=COL[m], lw=LW[m] * 0.8, label=m)
        ax.set_xlabel("Time [min]")
        ax.set_ylabel("Temperature [°C]")
        ax.set_title("Temperature, measured current: model vs surface sensor", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Validation against measured LG M50T data (Chen2020 parameters, no fitting of dynamic parameters)",
                 fontsize=12)
    fig.tight_layout()
    save(fig, "fig10_validation_m50t.png")


def fig_cooling_sensitivity():
    f50 = cfg.RESULTS / "errors_charge_h50.csv"
    if not f50.exists():
        print("no h=50 results yet")
        return
    e10 = pd.read_csv(cfg.RESULTS / "errors_charge.csv")
    e50 = pd.read_csv(f50)
    r10 = pd.read_csv(cfg.RESULTS / "runs_charge.csv")
    r50 = pd.read_csv(cfg.RESULTS / "runs_charge_h50.csv")
    values, temps = cfg.CHARGE_C_RATES, cfg.AMBIENT_T_C
    cmap = ListedColormap(STATUS)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], 4)
    fig, axs = plt.subplots(1, 4, figsize=(19, 4.9))
    panels = [(e10, "SPMe", "SPMe vs DFN, h = 10 W/m²K (natural convection)"),
              (e50, "SPMe", "SPMe vs DFN, h = 50 W/m²K (forced cooling)"),
              (e50, "SPM", "SPM vs DFN, h = 50 W/m²K")]
    for ax, (e, m, title) in zip(axs[:3], panels):
        Z = _grid(e, m, "class", values, temps)
        A = _grid(e, m, "V_rmse_cc_mV", values, temps)
        ax.imshow(Z, cmap=cmap, norm=norm, origin="lower", aspect="auto")
        for i in range(len(values)):
            for j in range(len(temps)):
                txt = "fail" if Z[i, j] == 3 else (f"{A[i, j]:.0f}" if np.isfinite(A[i, j]) else "")
                ax.text(j, i, txt, ha="center", va="center", fontsize=6.5,
                        color="white" if Z[i, j] in (2, 3) else INK)
        ax.set_xticks(range(len(temps)), [f"{t:g}" for t in temps], fontsize=8)
        ax.set_yticks(range(len(values)), [f"{v:g}" for v in values], fontsize=8)
        ax.set_xlabel("Ambient T [°C]")
        ax.set_title(title, fontsize=10)
        ax.grid(False)
    axs[0].set_ylabel("Charge C-rate")
    ax = axs[3]
    for c, a in zip([1.0, 2.0, 3.0], [0.45, 0.7, 1.0]):
        for r, ls, lab in [(r10, "-", "h = 10"), (r50, "--", "h = 50")]:
            d = r[(r.model == "DFN") & np.isclose(r.value, c)].sort_values("T_amb_C")
            ax.plot(d.T_amb_C, d.Tpeak_C, ls, color=INK, alpha=a, lw=1.6, label=f"{c:g}C, {lab}")
    ax.plot(temps, temps, ":", color=INK2, lw=1)
    ax.set_xlabel("Ambient T [°C]")
    ax.set_ylabel("DFN peak cell temperature [°C]")
    ax.set_title("Self-heating: DFN peak temperature", fontsize=10)
    ax.legend(frameon=False, fontsize=7.5, ncol=2)
    handles = [Patch(color=STATUS[k], label=STATUS_LBL[k]) for k in range(4)]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.4, -0.03))
    fig.suptitle("Cooling sensitivity: a better-cooled cell stays colder, so the SPMe breakdown edge moves to slightly lower C-rates",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0.05, 1, 0.97])
    save(fig, "fig11_cooling_sensitivity.png")


# ============================================================================ bridge to protocol design
def _mask_outline(ax, M, **kw):
    """Draw the outline of the True cells of a boolean grid (imshow coordinates)."""
    n, m = M.shape
    P = np.zeros((n + 2, m + 2), bool)
    P[1:-1, 1:-1] = M
    for i in range(n + 1):
        for k in range(m + 1):
            # interior edges only: the plot frame already closes regions that touch the border
            if k < m and 0 < i < n and P[i + 1, k + 1] != P[i, k + 1]:     # horizontal edge below cell (i, k)
                ax.plot([k - .5, k + .5], [i - .5, i - .5], **kw)
            if i < n and 0 < k < m and P[i + 1, k + 1] != P[i + 1, k]:     # vertical edge left of cell (i, k)
                ax.plot([k - .5, k - .5], [i - .5, i + .5], **kw)


def fig_fast_charge_window(errs, runs):
    """DFN plating-risk indicator with the 15-min, temperature and SPMe-validity limits overlaid."""
    from matplotlib.lines import Line2D
    values, temps = cfg.CHARGE_C_RATES, cfg.AMBIENT_T_C
    d = runs[runs.model == "DFN"]
    def grid(col, scale=1.0):
        Z = np.full((len(values), len(temps)), np.nan)
        for i, v in enumerate(values):
            for k, T in enumerate(temps):
                r = d[np.isclose(d.value, v) & np.isclose(d.T_amb_C, T)]
                if len(r):
                    Z[i, k] = scale * r[col].values[0]
        return Z
    phi, t80, Tp = grid("phi_sep_min_V", 1e3), grid("t80_s", 1 / 60), grid("Tpeak_C")
    cls = _grid(errs, "SPMe", "class", values, temps)
    div = LinearSegmentedColormap.from_list("div", ["#b8302f", "#e66767", "#f6c9c8", "#f0efec", "#cde2fb", "#3987e5", "#1c5cab"])
    lim = np.nanmax(np.abs(phi))
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    im = ax.imshow(phi, cmap=div, vmin=-lim, vmax=lim, origin="lower", aspect="auto")
    for a in range(len(values)):
        for b in range(len(temps)):
            ax.text(b, a, f"{phi[a, b]:.0f}", ha="center", va="center", fontsize=7.5, color=INK)
    _mask_outline(ax, t80 <= 15.0, color=INK, lw=3.0, solid_capstyle="round")
    plt.rcParams["hatch.linewidth"] = 0.7
    for a_, b_ in zip(*np.where(Tp >= 60.0)):
        ax.add_patch(plt.Rectangle((b_ - .5, a_ - .5), 1, 1, facecolor="none", edgecolor="#7a3fbf", hatch="///", lw=0, alpha=0.55))
    _mask_outline(ax, cls == 3, color="#6f6e69", lw=2.0, ls=(0, (6, 2)))
    ax.set_xticks(range(len(temps)), [f"{t:g}" for t in temps])
    ax.set_yticks(range(len(values)), [f"{v:g}" for v in values])
    ax.grid(False)
    ax.set_xlabel("Ambient temperature [°C]")
    ax.set_ylabel("CC-CV charge C-rate (from 10 % SOC)")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cb.set_label("DFN minimum φs − φe at the separator [mV]\n(< 0: lithium plating possible)")
    handles = [Line2D([], [], color=INK, lw=3.0, label="80 % SOC within 15 min"),
               Patch(facecolor="none", edgecolor="#7a3fbf", hatch="///", label="DFN peak temperature ≥ 60 °C"),
               Line2D([], [], color="#6f6e69", lw=2.0, ls=(0, (6, 2)), label="SPMe breaks down")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
    ok = (t80 <= 15.0) & (phi >= 0)
    lst = ", ".join(f"{values[i]:g}C at {temps[k]:g} °C (T_peak {Tp[i, k]:.0f} °C)" for i, k in zip(*np.where(ok)))
    ax.set_title("Plain CC-CV cannot charge to 80 % in 15 min without plating risk\n"
                 f"only {lst or 'none'} meets both, and only by running hot", fontsize=11)
    fig.tight_layout()
    save(fig, "fig12_fast_charge_window.png")


if __name__ == "__main__":
    tr, errs, runs = load("charge")
    fig_cccv_traces(tr)
    fig_adequacy_map(errs)
    fig_error_heatmaps(errs)
    fig_plating(tr, errs, runs)
    fig_profiles()
    fig_thermal_breakdown(tr)
    fig_cost(errs)
    try:
        trd, errd, _ = load("discharge")
        fig_discharge(trd, errd)
        fig_adequacy_map(errd, values=cfg.DISCHARGE_C_RATES, fname="fig02b_adequacy_map_discharge.png",
                         ylabel="Discharge C-rate", annot="V_rmse_mV", title_extra=" (CC discharge)")
    except FileNotFoundError:
        print("no discharge results yet")
    try:
        tru, erru, _ = load("udds")
        fig_udds(tru, erru)
    except FileNotFoundError:
        print("no udds results yet")
    fig_validation()
    fig_cooling_sensitivity()
    fig_fast_charge_window(errs, runs)
