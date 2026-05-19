param()

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $root
try {
    $env:PYTHONPATH = "src;$env:PYTHONPATH"
    python -m ruff check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    python -m pytest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    .\invoke.ps1 brief --output json --mail-limit 0 --task-limit 0 | Out-Null
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
