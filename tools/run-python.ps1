param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $repoRoot "apps/api/.venv/Scripts/python.exe"

if (Test-Path $venvPython) {
    & $venvPython @CommandArgs
    exit $LASTEXITCODE
}

$systemPython = Get-Command python -ErrorAction SilentlyContinue
if ($systemPython) {
    & $systemPython.Source @CommandArgs
    exit $LASTEXITCODE
}

throw "No Python interpreter found. Create apps/api/.venv or install Python on PATH."
