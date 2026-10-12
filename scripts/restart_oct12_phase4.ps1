$ErrorActionPreference = 'Stop'
$oct12Root = Split-Path -Parent $PSScriptRoot
$oct12Evidence = Join-Path $oct12Root 'eval/artifacts/oct12/commands'
$oct12Record = Join-Path $oct12Evidence 'oct12-runtime-phase4.json'
if (Test-Path -LiteralPath $oct12Record) { throw 'Preserve prior runtime evidence.' }
$oct12Started = [DateTime]::UtcNow.ToString('o')
$oct12EnvPath = Join-Path $oct12Root '.env'
$oct12EnvText = [IO.File]::ReadAllText($oct12EnvPath)
$oct12CaptureLine = 'LLM_CAPTURE_DIR=eval/artifacts/oct12/provider-captures/live-004'
if ($oct12EnvText -match '(?m)^LLM_CAPTURE_DIR=.*$') {
    $oct12EnvText = [regex]::Replace($oct12EnvText, '(?m)^LLM_CAPTURE_DIR=.*$', $oct12CaptureLine)
} else { $oct12EnvText += "`n$oct12CaptureLine`n" }
[IO.File]::WriteAllText($oct12EnvPath, $oct12EnvText, [Text.UTF8Encoding]::new($false))
$oct12Output = & (Join-Path $PSScriptRoot 'restart_services.ps1') -Capture -ArtifactDirectory 'eval/artifacts/oct12/runtime-phase4' -CaptureDirectory 'eval/artifacts/oct12/api-records/live-004' 2>&1 | Out-String
[IO.File]::WriteAllText((Join-Path $oct12Evidence 'oct12-runtime-phase4.txt'), $oct12Output)
$oct12Health = $null
for ($oct12Attempt=0; $oct12Attempt -lt 20; $oct12Attempt++) {
    try { $oct12Health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2; break }
    catch { Start-Sleep -Milliseconds 500 }
}
if (-not $oct12Health) { throw 'API health check did not complete.' }
$oct12UiStatus = (Invoke-WebRequest -Uri 'http://127.0.0.1:8501/_stcore/health' -TimeoutSec 5).StatusCode
$oct12Result = [ordered]@{
    started_at_utc=$oct12Started; completed_at_utc=[DateTime]::UtcNow.ToString('o')
    command='pwsh -NoProfile -File scripts/restart_oct12_phase4.ps1'
    script_completed=$true; credentials_printed=$false
    only_env_change='LLM_CAPTURE_DIR (nonsecret capture path)'; provider_capture='eval/artifacts/oct12/provider-captures/live-004'
    api_capture='eval/artifacts/oct12/api-records/live-004'; api_health=$oct12Health; ui_health_status=$oct12UiStatus
    api_launcher_pid=[int](Get-Content -LiteralPath (Join-Path $oct12Root '.runtime/d2-api.pid'))
    ui_launcher_pid=[int](Get-Content -LiteralPath (Join-Path $oct12Root '.runtime/d2-ui.pid'))
}
$oct12Result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $oct12Record -Encoding utf8
Write-Output $oct12Output
Write-Output ('API/UI healthy; phase4 capture provenance saved, no credentials printed.')
