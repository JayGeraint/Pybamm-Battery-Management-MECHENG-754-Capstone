"""Plot exported measured-data checks, including residuals and coverage."""
import argparse
import os
import json
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / "work/mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("folder",type=Path)
    a=parser.parse_args()
    summary=pd.read_csv(a.folder/"validation_metrics.csv")
    config_path=a.folder/"config.json"
    variant=json.loads(config_path.read_text()).get("parameter_variant","Chen2020") if config_path.exists() else "Chen2020"
    dest=a.folder/"figures"
    dest.mkdir(exist_ok=True)
    for (cell,step), group in summary[summary.status=="ok"].groupby(["cell","step"]):
        fig,axes=plt.subplots(2,1,figsize=(8,6),sharex=True,constrained_layout=True)
        for i,(_,row) in enumerate(group.iterrows()):
            d=pd.read_csv(a.folder/(row["case"]+".csv"))
            axes[0].plot(d.time_s/60,d.model_voltage_v,label=row.model)
            axes[1].plot(d.time_s/60,1000*(d.model_voltage_v-d.measured_voltage_v),
                         label=f"{row.model}: {row.voltage_rmse_mv:.1f} mV, {row.coverage_pct:.1f}% coverage")
            if i==0:
                axes[0].plot(d.time_s/60,d.measured_voltage_v,"k--",label="Measured (shared interval)",linewidth=1)
        axes[0].set_ylabel("Voltage (V)")
        axes[1].set(xlabel="Time (min)",ylabel="Model minus measured (mV)")
        for ax in axes:
            ax.grid(alpha=.2)
            ax.legend(fontsize=8)
        axes[1].axhline(0,color="black",linewidth=.7)
        fig.suptitle(f"{cell}, discharge step {int(step)} | {variant}\nNo parameter fitting; rested-voltage initialization",fontsize=10)
        fig.savefig(dest/f"{cell}_step{int(step)}.png",dpi=180)
        plt.close(fig)
    print(dest)


if __name__=="__main__":
    main()
