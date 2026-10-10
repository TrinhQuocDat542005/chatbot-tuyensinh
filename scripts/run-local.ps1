param(
    [ValidateSet('actions', 'server', 'train', 'check')]
    [string]$Mode = 'server',
    [string]$Python = '',
    [int]$Port = 0
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:RASA_TELEMETRY_ENABLED = 'false'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not $Python) {
    if (Test-Path .venv-rasa/Scripts/python.exe) { $Python = '.venv-rasa/Scripts/python.exe' }
    elseif (Test-Path .venv/Scripts/python.exe) { $Python = '.venv/Scripts/python.exe' }
    else { $Python = 'python' }
}
switch ($Mode) {
    'actions' {
        if (-not $Port) { $Port = 5055 }
        & $Python -m rasa_sdk --actions actions --port $Port
    }
    'server' {
        if (-not $Port) { $Port = 5005 }
        & $Python -m rasa run --model models/admissions-week4.tar.gz --port $Port --endpoints endpoints.yml
    }
    'train' { & $Python -m rasa train --data data --fixed-model-name admissions-week4 }
    'check' {
        & $Python scripts/validate_data.py
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $Python -m pytest
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $Python -m rasa data validate --fail-on-warnings
    }
}
exit $LASTEXITCODE
