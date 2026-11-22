"""Plot previously exported simulation results without rerunning models."""
import argparse
import os
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / "work/mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder", type=Path)
    a = p.parse_args()
    out = a.folder / "figures"
    out.mkdir(exist_ok=True)
    s = pd.read_csv(a.folder / "summary.csv")
    c = pd.read_csv(a.folder / "comparisons.csv")
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    for (rate, temp), group in s[s.status == "ok"].groupby(["rate_c", "ambient_c"]):
        fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
        for _, row in group.iterrows():
            name = row.model
            f = pd.read_csv(a.folder / "traces" / f"{name}_{rate:g}C_{temp:g}degC.csv")
            for ax, col, label in zip(axes.flat,
                ["voltage_v", "current_a", "temperature_c", "soc_nominal", "anode_mean_v", "anode_separator_v"],
                ["Terminal voltage (V)", "Current (A), charging < 0", "Lumped temperature (deg C)",
                 "Coulomb-counted nominal SOC", "Mean anode potential difference (V)", "Separator anode potential difference (V)"]):
                ax.plot(f.time_s / 60, f[col], label=name, linewidth=1.6)
                ax.set(xlabel="Time (min)", ylabel=label)
                ax.grid(alpha=.2)
        for ax in axes[1, 1:]:
            ax.axhline(0, color="black", linestyle=":", linewidth=.7)
        axes[0, 0].legend()
        fig.suptitle(f"Chen2020 model comparison | {rate:g}C charge | ambient {temp:g} deg C\n"
                     "Numerical simulation; reduced-model separator values have reduced spatial fidelity", fontsize=12)
        fig.savefig(out / f"comparison_{rate:g}C_{temp:g}degC.png", dpi=180)
        plt.close(fig)
    if c.ambient_c.nunique() > 1:
        fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
        for i, name in enumerate(["SPM", "SPMe"]):
            for j, (metric, label) in enumerate([("voltage_cc_mv_rmse", "Common CC voltage RMSE (mV)"),
                                                ("warm_wall_speedup", "DFN / model warm wall time")]):
                ax = axes[i,j]
                pivot = c[c.model == name].pivot(index="ambient_c", columns="rate_c", values=metric)
                pivot = pivot.reindex(index=sorted(s.ambient_c.unique()), columns=sorted(s.rate_c.unique()))
                im = ax.imshow(pivot, aspect="auto", origin="lower", cmap="viridis")
                ax.set(xticks=range(len(pivot.columns)), xticklabels=pivot.columns,
                       yticks=range(len(pivot.index)), yticklabels=pivot.index,
                       xlabel="Charge C-rate", ylabel="Ambient temperature (deg C)", title=f"{name}: {label}")
                for (r, k), value in np.ndenumerate(pivot.to_numpy()):
                    label_value = f"{value:.1f}" if np.isfinite(value) else "failed"
                    ax.text(k,r,label_value,ha="center",va="center",color="white" if value < np.nanmean(pivot) else "black")
                fig.colorbar(im, ax=ax)
        fig.suptitle("Model fidelity and measured compute cost | Simulation benchmark")
        fig.savefig(out / "accuracy_cost_map.png", dpi=200)
        plt.close(fig)
    print("Figures:", out)


if __name__ == "__main__":
    main()
