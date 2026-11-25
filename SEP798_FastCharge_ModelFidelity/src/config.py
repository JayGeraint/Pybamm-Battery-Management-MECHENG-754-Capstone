"""
Study configuration: everything you might want to change lives here.

SEP798 Final Project (Plan A)
"Model fidelity vs. computational cost in fast-charge simulation of a 21700 cell"
Models : SPM, SPMe, DFN (PyBaMM), each coupled to a lumped (0-D) thermal model
Cell   : LG M50 / M50T 21700 (NMC811 | graphite-SiOx), PyBaMM parameter set Chen2020
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)

UDDS_CSV = DATA / "UDDS_course.csv"                       # course UDDS current profile (Assignment 2)
M50T_C10 = DATA / "m50t" / "cellD_RPT0_C10_discharge.csv"
M50T_PULSE = DATA / "m50t" / "cellD_RPT1_hybrid_pulse_0p5C_discharge.csv"

# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
MODELS = ["SPM", "SPMe", "DFN"]          # DFN is the reference ("truth") model
REFERENCE = "DFN"
THERMAL = "lumped"                       # lumped (0-D) thermal model for all three

# Spatial discretisation (PyBaMM default = 20 points per domain / particle).
# A DFN mesh-refinement check is done in run_mesh_check.py.
VAR_PTS = {"x_n": 20, "x_s": 20, "x_p": 20, "r_n": 20, "r_p": 20}
VAR_PTS_FINE = {"x_n": 40, "x_s": 40, "x_p": 40, "r_n": 40, "r_p": 40}

# Same solver tolerances for every model so that the solve-time comparison is fair
RTOL = 1e-6
ATOL = 1e-8

# ----------------------------------------------------------------------------
# Operating conditions
# ----------------------------------------------------------------------------
NOMINAL_CAPACITY_AH = 5.0                # Chen2020 nominal capacity
V_MAX = 4.2
V_MIN = 2.5

# (1) CC-CV fast charge  (main study)
CHARGE_C_RATES = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
AMBIENT_T_C = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
CHARGE_SOC0 = 0.10                       # start of a typical fast-charge window
CV_CUTOFF = "C/20"                       # CV phase ends when |I| < C/20
CHARGE_PERIOD_S = 5                      # output resolution [s]

# (2) CC discharge
DISCHARGE_C_RATES = [0.5, 1.0, 2.0, 3.0]
DISCHARGE_SOC0 = 1.0
DISCHARGE_PERIOD_S = 5

# (3) UDDS drive cycle (course profile, 1370 s, originally for a 5.4 Ah cell)
#     current is rescaled by 5.0/5.4 to keep the same C-rate on the 5 Ah cell,
#     then multiplied by UDDS_SCALES to emulate a gentle (x1) and an aggressive (x2) pack load.
UDDS_SCALES = [1.0, 2.0]
UDDS_T_C = [0.0, 10.0, 25.0, 40.0]       # fewer temperatures: DFN drive-cycle runs are slow
UDDS_REPEATS = 4                         # 4 x 1370 s ~ 91 min of driving
UDDS_SOC0 = 0.80                         # start below 100 % so regen pulses do not hit 4.2 V
UDDS_V_MAX_EVENT = 4.4                   # regen spikes may briefly exceed 4.2 V; don't stop the run
UDDS_DT_S = 1.0                          # resample 0.1 s data to 1 s

# ----------------------------------------------------------------------------
# "Is the reduced model adequate?" thresholds (vs DFN).  Two levels:
#   value <= first  -> adequate,  first < value <= second -> marginal,  > second -> inadequate
# Chosen to match typical BMS needs: ~1 % voltage accuracy (≈ 37 mV at 3.7 V),
# ±2 K thermal accuracy, and charge-time prediction within 5 %.
# ----------------------------------------------------------------------------
THRESHOLDS_CHARGE = {
    "V_rmse_cc_mV": (20.0, 40.0),     # voltage RMSE during DFN's CC phase
    "t80_err_pct": (5.0, 10.0),       # |time-to-80 % SOC error| / DFN time
    "Tpeak_err_K": (2.0, 4.0),        # |peak temperature error|
}
THRESHOLDS_DISCHARGE = {
    "V_rmse_mV": (20.0, 40.0),
    "Q_err_pct": (2.0, 5.0),          # |discharge capacity to 2.5 V error|
    "Tpeak_err_K": (2.0, 4.0),
}
THRESHOLDS_UDDS = {
    "V_rmse_mV": (20.0, 40.0),
    "Tpeak_err_K": (2.0, 4.0),
}

# Lithium-plating risk indicator: negative-electrode potential vs Li/Li+ at the
# separator interface, phi_s - phi_e.  Below 0 V, Li plating is thermodynamically possible.
PLATING_THRESHOLD_V = 0.0

# Timing benchmark
BENCH_REPEATS = 5
BENCH_CASES = [  # (protocol, c_rate or scale, ambient T [degC]) - all inside SPMe's valid region,
    ("charge", 1.0, 25.0),       # so that no timing comes from a truncated (failed) run
    ("charge", 2.0, 25.0),
    ("charge", 3.0, 40.0),
    ("charge", 1.0, 0.0),
    ("discharge", 1.0, 25.0),
    ("udds", 1.0, 25.0),
]

N_WORKERS = 3     # parallel processes for the accuracy sweep (timing benchmark runs serially)
