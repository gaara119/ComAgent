param([switch]$PreserveFailedIpc)
$ErrorActionPreference = 'Stop'
$d4ProjectRoot = Split-Path -Parent $PSScriptRoot
$d4Evidence = Join-Path $d4ProjectRoot 'eval/artifacts/d4/docker-restart-005'
New-Item -ItemType Directory -Path $d4Evidence -Force | Out-Null
$d4Record = [ordered]@{at_utc=[DateTime]::UtcNow.ToString('o'); requested=[bool]$PreserveFailedIpc; database_files_modified=$false; success=$false}
try {
    if (-not $PreserveFailedIpc) { throw 'Explicit PreserveFailedIpc switch required.' }
    $d4Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $d4Principal = [Security.Principal.WindowsPrincipal]::new($d4Identity)
    $d4Record.administrator = $d4Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $d4Source = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'docker-secrets-engine'))
    $d4Expected = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'AppData/Local/docker-secrets-engine'))
    $d4Target = [IO.Path]::GetFullPath($d4Source + '.d4-preserved-20261013')
    if ($d4Source -ne $d4Expected -or (Split-Path -Parent $d4Source) -ne (Split-Path -Parent $d4Target)) { throw 'Unexpected absolute paths.' }
    if (Test-Path -LiteralPath $d4Target) { throw 'Preserved directory exists; nothing overwritten.' }
    $d4Items = @(Get-ChildItem -LiteralPath $d4Source -Force)
    if ($d4Items.Count -ne 1 -or $d4Items[0].Name -ne 'engine.sock' -or $d4Items[0].Length -ne 0) { throw 'Unexpected contents; nothing changed.' }
    $d4Processes = @(Get-Process -Name 'com.docker.backend','Docker Desktop' -ErrorAction SilentlyContinue)
    foreach ($d4Process in $d4Processes) {
        if (-not $d4Process.Path.StartsWith('C:\Program Files\Docker\Docker\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected Docker process path.' }
    }
    foreach ($d4Process in $d4Processes) { Stop-Process -Id $d4Process.Id -Force -ErrorAction SilentlyContinue }
    # Only the already-failed Docker distribution; no other WSL is terminated.
    $d4WslOutput = & wsl --terminate docker-desktop 2>&1
    $d4Record.docker_wsl_terminate_exit_code = $LASTEXITCODE
    Rename-Item -LiteralPath $d4Source -NewName (Split-Path -Leaf $d4Target)
    $d4Record.ipc_preserved = $true
    Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden
    $d4Record.success = $true
} catch {
    $d4Record.error = $_.Exception.Message
} finally {
    $d4Record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $d4Evidence 'ipc-repair-result.json') -Encoding UTF8
}
if (-not $d4Record.success) { exit 1 }
