#!/usr/bin/env bash
# Runs the complete study (Linux/macOS).  On Windows use run_all.bat.
set -e
cd "$(dirname "$0")/src"
python run_sweep.py --only charge
python run_sweep.py --only discharge
python run_sweep.py --only udds
python run_sweep.py --only charge --h 50   # cooling sensitivity
python run_benchmark.py        # serial timing benchmark
python run_mesh_check.py
python run_validation.py
python make_figures.py
python export_matlab.py
