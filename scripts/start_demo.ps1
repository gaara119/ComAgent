param([int]$ApiPort = 8000, [int]$UiPort = 8501)
$ErrorActionPreference = 'Stop'
if ($ApiPort -lt 1 -or $ApiPort -gt 65535 -or $UiPort -lt 1 -or $UiPort -gt 65535 -or $ApiPort -eq $UiPort) {
    throw 'API and UI ports must be distinct numbers from 1 to 65535.'
}
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectDir
$projectPython = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Missing project .venv; follow README.' }
$runtimeDir = Join-Path $projectDir '.runtime'
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$apiUrl = "http://127.0.0.1:$ApiPort"

function Test-ProjectApi {
    try {
        $health = Invoke-RestMethod -Uri "$apiUrl/health" -TimeoutSec 3
        return ($health.status -eq 'ok' -and $health.stage -in @('D1', 'D2', 'D3', 'D4'))
    } catch { return $false }
}

foreach ($listener in @(Get-NetTCPConnection -LocalPort $ApiPort -State Listen -ErrorAction SilentlyContinue)) {
    $owner = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $listener.OwningProcess)
    $ownerParent = if ($owner) { Get-CimInstance Win32_Process -Filter ('ProcessId=' + $owner.ParentProcessId) }
    $ownerCommand = [string]$owner.CommandLine
    if (-not $ownerCommand.Contains('api.main:app') -or
        -not ($ownerCommand.Contains($projectPython) -or ([string]$ownerParent.CommandLine).Contains($projectPython))) {
        throw "Port $ApiPort belongs to another application or workspace. No process was stopped."
    }
}

if (-not (Test-ProjectApi)) {
    $existingListener = Get-NetTCPConnection -LocalPort $ApiPort -State Listen -ErrorAction SilentlyContinue
    if ($existingListener) { throw "Port $ApiPort is occupied by another service. Select another ApiPort; no process was stopped." }
    $apiProcess = Start-Process -FilePath $projectPython -ArgumentList @('-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', "$ApiPort") `
        -WorkingDirectory $projectDir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $runtimeDir 'api.stdout.log') -RedirectStandardError (Join-Path $runtimeDir 'api.stderr.log')
    $apiProcess.Id | Set-Content -LiteralPath (Join-Path $runtimeDir 'api.pid')
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if (Test-ProjectApi) { $ready = $true; break }
        if ($apiProcess.HasExited) { break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'API did not become ready. See .runtime/api.stderr.log.' }
}

$existingUiListener = Get-NetTCPConnection -LocalPort $UiPort -State Listen -ErrorAction SilentlyContinue
if ($existingUiListener) { throw "Port $UiPort is already occupied. Open http://127.0.0.1:$UiPort if the demo is running, or select another UiPort; no process was stopped." }
Write-Host "API: $apiUrl/docs"
Write-Host "Workbench: http://127.0.0.1:$UiPort"
Write-Host 'Press Ctrl+C to stop the workbench. The API remains available.'
& $projectPython frontend-workbench/run_ui.py --api-url $apiUrl --port $UiPort
if ($LASTEXITCODE -ne 0) { throw "Workbench exited with code $LASTEXITCODE." }
