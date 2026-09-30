<#
  Windows equivalents of the Makefile targets (make is not installed on the dev machine).
  Usage:  .\scripts\dev.ps1 <target>
  Targets: setup, models, scenario, demo, test, eval, eval-quick, verify, lint, build, check-collectors
#>
param([Parameter(Mandatory = $true)][string]$Target)

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

switch ($Target) {
  "setup" {
    if (-not (Test-Path (Join-Path $Backend ".venv"))) { py -3.11 -m venv (Join-Path $Backend ".venv"); $Py = Join-Path $Backend ".venv\Scripts\python.exe" }
    & $Py -m pip install -e "$Backend[dev]"
    Push-Location (Join-Path $Root "frontend"); npm install; Pop-Location
  }
  "models" { & $Py (Join-Path $Root "scripts\fetch_models.py") }
  "scenario" { Push-Location $Backend; & $Py -m scenario.generate --seed 7; Pop-Location }
  "build" { Push-Location (Join-Path $Root "frontend"); npm run build; Pop-Location }
  "demo" {
    Push-Location (Join-Path $Root "frontend"); npm run build; Pop-Location
    Push-Location $Backend; & $Py -m uvicorn app.main:app --host 127.0.0.1 --port 8000; Pop-Location
  }
  "test" { Push-Location $Backend; & $Py -m pytest tests/ -q; Pop-Location }
  "eval" { Push-Location $Backend; & $Py -m eval.run_all; Pop-Location }
  "eval-quick" { Push-Location $Backend; & $Py -m eval.run_all --quick; Pop-Location }
  "verify" { Push-Location $Backend; & $Py -m app.ledger.verify --db (Join-Path $Root "data\deepastambha.db"); Pop-Location }
  "lint" {
    Push-Location $Backend; & (Join-Path $Backend ".venv\Scripts\ruff.exe") check app/ eval/ scenario/; & (Join-Path $Backend ".venv\Scripts\mypy.exe") app/; Pop-Location
    Push-Location (Join-Path $Root "frontend"); npx tsc --noEmit; Pop-Location
  }
  "check-collectors" { Push-Location $Backend; & $Py (Join-Path $Root "scripts\check_collectors.py") @args; Pop-Location }
  default { Write-Error "Unknown target '$Target'" }
}
