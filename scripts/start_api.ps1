param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectDir
$projectPython = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Missing project .venv; follow README.' }
& $projectPython -m uvicorn api.main:app --host 127.0.0.1 --port $Port
