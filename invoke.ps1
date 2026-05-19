param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path $scriptDir
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$toolSrc = Join-Path $projectRoot "src"

if (Test-Path $venvPython) {
    $env:PYTHONPATH = "$toolSrc;$env:PYTHONPATH"
    & $venvPython -m day_brief @Arguments
    exit $LASTEXITCODE
}

$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonCmd) {
    $pythonCmd = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $pythonCmd) {
    Write-Error "Python not found. Please install Python 3.10 or later."
    exit 1
}

$env:PYTHONPATH = "$toolSrc;$env:PYTHONPATH"
& $pythonCmd -m day_brief @Arguments
exit $LASTEXITCODE
