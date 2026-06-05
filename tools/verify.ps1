param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

if (-not $SkipInstall) {
    Write-Host "Install dependencies with npm install and the Python requirements before running this script in CI."
}

Write-Host "Checking TypeScript contracts"
npm --prefix packages/contracts run typecheck
npm --prefix packages/contracts run test

Write-Host "Checking web workspace"
npm --prefix apps/web run typecheck
npm --prefix apps/web run test

Write-Host "Checking API workspace"
powershell -ExecutionPolicy Bypass -File tools/run-python.ps1 -m pytest apps/api/tests
powershell -ExecutionPolicy Bypass -File tools/run-python.ps1 -m ruff check apps/api
powershell -ExecutionPolicy Bypass -File tools/run-python.ps1 -m ruff format --check apps/api
