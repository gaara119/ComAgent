param([switch]$SkipUi, [switch]$Capture, [string]$ArtifactDirectory = 'eval/artifacts/d2-final/runtime', [string]$CaptureDirectory = 'eval/artifacts/d2-final/ui/api')
$ErrorActionPreference = 'Stop'
$d2ProjectDir = Split-Path -Parent $PSScriptRoot
$d2Python = Join-Path $d2ProjectDir '.venv\Scripts\python.exe'
$d2Runtime = Join-Path $d2ProjectDir '.runtime'
$d2Logs = Join-Path $d2ProjectDir $ArtifactDirectory
New-Item -ItemType Directory -Path $d2Logs -Force | Out-Null
$d2Stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')

function Stop-OwnedService([string]$PidFile, [string[]]$Markers) {
    if (Test-Path -LiteralPath $PidFile) {
        $d2ServicePid = [int](Get-Content -LiteralPath $PidFile -Raw)
        $d2ProcessInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$d2ServicePid"
        if ($d2ProcessInfo) {
            $d2IsProjectPython = $d2ProcessInfo.CommandLine.Contains($d2Python) -or ($d2ProcessInfo.ExecutablePath -eq $d2Python)
            $d2HasMarker = @($Markers | Where-Object { $d2ProcessInfo.CommandLine.Contains($_) }).Count -gt 0
            if (-not $d2IsProjectPython -or -not $d2HasMarker) {
                throw 'Saved PID belongs to a different process; no process was stopped.'
            }
            # The Windows venv launcher owns a child running the base Python
            # executable. Verify ancestry AND the service marker before stopping
            # it, otherwise terminating only the launcher leaves the port busy.
            $d2Children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$d2ServicePid"
            foreach ($d2Child in $d2Children) {
                $d2ChildHasMarker = @($Markers | Where-Object { $d2Child.CommandLine.Contains($_) }).Count -gt 0
                if ($d2Child.Name -eq 'python.exe' -and $d2ChildHasMarker) {
                    Stop-Process -Id $d2Child.ProcessId -Force
                    Wait-Process -Id $d2Child.ProcessId -Timeout 5 -ErrorAction SilentlyContinue
                    Write-Output "Stopped owned worker PID=$($d2Child.ProcessId)"
                } elseif ($d2Child.Name -in @('conhost.exe', 'OpenConsole.exe')) {
                    # Windows console hosts close with the launcher; they do
                    # not run an independent application or serve either port.
                    continue
                } else { throw 'Unexpected child process; inspect it before restarting.' }
            }
            Stop-Process -Id $d2ServicePid -Force -ErrorAction SilentlyContinue
            Wait-Process -Id $d2ServicePid -Timeout 5 -ErrorAction SilentlyContinue
            Write-Output "Stopped owned service PID=$d2ServicePid"
        }
    }
}

Stop-OwnedService (Join-Path $d2Runtime 'd2-api.pid') @('api.main:app', 'scripts.d2_capture_api:app')
if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 8000 is occupied by an unrecognized process; no other process was stopped.'
}
$d2ApiApp = 'api.main:app'
if ($Capture) {
    $d2ApiApp = 'scripts.d2_capture_api:app'
    $env:D2_CAPTURE_DIR = Join-Path $d2ProjectDir $CaptureDirectory
} else {
    Remove-Item Env:D2_CAPTURE_DIR -ErrorAction SilentlyContinue
}
$d2ApiProcess = Start-Process -FilePath $d2Python -ArgumentList @('-m','uvicorn',$d2ApiApp,'--host','127.0.0.1','--port','8000') `
    -WorkingDirectory $d2ProjectDir -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $d2Logs "$d2Stamp-api.stdout.txt") -RedirectStandardError (Join-Path $d2Logs "$d2Stamp-api.stderr.txt")
$d2ApiProcess.Id | Set-Content -LiteralPath (Join-Path $d2Runtime 'd2-api.pid')
Write-Output "Started API PID=$($d2ApiProcess.Id) http://127.0.0.1:8000/docs"
if (-not $SkipUi) {
    Stop-OwnedService (Join-Path $d2Runtime 'd2-ui.pid') 'streamlit'
    if (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue) { throw 'Port 8501 is occupied; no other process was stopped.' }
    $d2UiProcess = Start-Process -FilePath $d2Python -ArgumentList @('-m','streamlit','run','ui/app.py','--server.address','127.0.0.1','--server.port','8501','--server.headless','true','--browser.gatherUsageStats','false') `
        -WorkingDirectory $d2ProjectDir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $d2Logs "$d2Stamp-ui.stdout.txt") -RedirectStandardError (Join-Path $d2Logs "$d2Stamp-ui.stderr.txt")
    $d2UiProcess.Id | Set-Content -LiteralPath (Join-Path $d2Runtime 'd2-ui.pid')
    Write-Output "Started UI PID=$($d2UiProcess.Id) http://127.0.0.1:8501"
}
