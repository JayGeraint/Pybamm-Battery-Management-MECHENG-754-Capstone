$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment' }
& .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
Write-Host 'Ready. Run: .\.venv\Scripts\python.exe run_study.py --config configs/baseline.json --out results/my_baseline'
