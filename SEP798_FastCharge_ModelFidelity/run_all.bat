@echo off
REM Runs the complete study on Windows (needs Python 3.10+ with: pip install -r requirements.txt)
cd /d "%~dp0src"
python run_sweep.py --only charge   || goto :err
python run_sweep.py --only discharge || goto :err
python run_sweep.py --only udds     || goto :err
python run_sweep.py --only charge --h 50 || goto :err
python run_benchmark.py             || goto :err
python run_mesh_check.py            || goto :err
python run_validation.py            || goto :err
python make_figures.py              || goto :err
python export_matlab.py             || goto :err
echo Done. Figures in ..\figures, tables in ..\results
goto :eof
:err
echo A step failed - see the message above.
