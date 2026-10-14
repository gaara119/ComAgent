param([switch]$NoBrowser, [switch]$SkipDatabaseStart)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$projectRuntime = Join-Path $projectRoot '.runtime'
$projectLogs = Join-Path $projectRuntime 'project-start'
$projectApiUrl = 'http://127.0.0.1:8000'
$projectUiUrl = 'http://127.0.0.1:8501/'
$projectStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
if (-not (Test-Path -LiteralPath $projectPython -PathType Leaf)) { throw 'Project Python environment is missing.' }
New-Item -ItemType Directory -Path $projectLogs -Force | Out-Null

function Test-DockerReady {
    try {
        $dockerVersion = & docker info --format '{{.ServerVersion}}' 2>$null
        return ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($dockerVersion))
    } catch { return $false }
}

function Start-ExistingDatabases {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI is not installed.' }
    if (-not (Test-DockerReady)) {
        $dockerDesktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (-not (Test-Path -LiteralPath $dockerDesktop)) { throw 'Docker Desktop is not installed.' }
        Write-Host 'Starting Docker Desktop...'
        try {
            $dockerStartOutput = & docker desktop start --detach 2>$null
            if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop CLI start is unavailable.' }
        } catch {
            Start-Process -FilePath $dockerDesktop -WorkingDirectory (Split-Path -Parent $dockerDesktop) -WindowStyle Hidden
        }
        $dockerReady = $false
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            if (Test-DockerReady) { $dockerReady = $true; break }
            Start-Sleep -Seconds 2
        }
        if (-not $dockerReady) { throw 'Docker did not become ready. Start Docker Desktop and retry.' }
    }
    foreach ($definition in @(
        @{Project='comagent-d1';Service='chinook-pg'},
        @{Project='comagent-d3-aw';Service='aw-pg'}
    )) {
        $containerIds = @(& docker ps -aq --filter ('label=com.docker.compose.project=' + $definition.Project) --filter ('label=com.docker.compose.service=' + $definition.Service))
        if ($LASTEXITCODE -eq 0 -and $containerIds.Count -eq 0) {
            $containerIds = @(& docker ps -aq --filter 'label=com.docker.compose.project=comagent-d4-recovery' --filter ('label=com.docker.compose.service=' + $definition.Service) --filter 'label=comagent.data-purpose=d4-recovery-copy')
        }
        if ($LASTEXITCODE -ne 0 -or $containerIds.Count -ne 1) {
            throw ('Expected one existing database container for ' + $definition.Project + '; nothing was created or imported.')
        }
        $containerId = [string]$containerIds[0]
        $labelsText = & docker inspect --format '{{json .Config.Labels}}' $containerId
        if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect existing database ownership.' }
        $labels = $labelsText | ConvertFrom-Json
        $databaseOwner = [string]$labels.'com.docker.compose.project.working_dir'
        if ($databaseOwner.Replace('/', '\').TrimEnd('\') -ne $projectRoot.Replace('/', '\').TrimEnd('\')) {
            throw 'Database container belongs to a different workspace; it was not started.'
        }
        $containerState = & docker inspect --format '{{.State.Running}}' $containerId
        if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect database state.' }
        if ($containerState -ne 'true') {
            $startedContainer = & docker start $containerId
            if ($LASTEXITCODE -ne 0) { throw 'Existing database container could not be started.' }
            Write-Host ('Started existing database: ' + $definition.Service)
        } else { Write-Host ('Reusing existing database: ' + $definition.Service) }
    }
}

function Assert-ProjectListener([int]$Port, [string[]]$Markers) {
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    foreach ($listener in $listeners) {
        $listenerInfo = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $listener.OwningProcess)
        $listenerParent = if ($listenerInfo) { Get-CimInstance Win32_Process -Filter ('ProcessId=' + $listenerInfo.ParentProcessId) }
        $command = [string]$listenerInfo.CommandLine
        $parentCommand = [string]$listenerParent.CommandLine
        $marked = @($Markers | Where-Object { $command.Contains($_) }).Count -gt 0
        $owned = $command.Contains($projectPython) -or $parentCommand.Contains($projectPython)
        if (-not $marked -or -not $owned) { throw ('Port ' + $Port + ' belongs to an unrecognized process. No process was stopped.') }
    }
    return ($listeners.Count -gt 0)
}

function Get-ProjectHealth {
    try {
        $health = Invoke-RestMethod -Uri ($projectApiUrl + '/health') -TimeoutSec 6
        if ($health.status -eq 'ok' -and $health.stage -in @('D3','D4') -and $health.sql_prompt_sha256) { return $health }
    } catch { }
    return $null
}

$databaseStartError = $null
if (-not $SkipDatabaseStart) {
    try { Start-ExistingDatabases }
    catch {
        $databaseStartError = $_.Exception.Message
        Write-Warning ($databaseStartError + ' The interface will open with the actual database readiness status.')
    }
}
$apiListening = Assert-ProjectListener 8000 @('api.main:app', 'scripts.d2_capture_api:app')
if (-not $apiListening) {
    $api = Start-Process -FilePath $projectPython -ArgumentList @('-m','uvicorn','api.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectLogs ($projectStamp + '-api.stdout.log')) -RedirectStandardError (Join-Path $projectLogs ($projectStamp + '-api.stderr.log'))
    $api.Id | Set-Content -LiteralPath (Join-Path $projectRuntime 'd2-api.pid')
    Write-Host 'Started project API.'
} else { Write-Host 'Reusing project API.' }
$health = $null
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    $health = Get-ProjectHealth
    if ($health -and ($SkipDatabaseStart -or $databaseStartError -or ($health.database_ready -and (-not $health.aw_configured -or $health.aw_database_ready)))) { break }
    Start-Sleep -Milliseconds 500
}
if (-not $health) { throw 'API did not become healthy. See .runtime/project-start logs.' }
if (-not $SkipDatabaseStart -and (-not $health.database_ready -or ($health.aw_configured -and -not $health.aw_database_ready))) {
    Write-Warning 'The interface is available, but SQL databases are not ready. Existing data has not been recreated or imported.'
}
$uiListening = Assert-ProjectListener 8501 @('streamlit run ui/app.py')
if (-not $uiListening) {
    $previousApiBase = $env:QA_API_BASE_URL
    $env:QA_API_BASE_URL = $projectApiUrl
    try {
        $ui = Start-Process -FilePath $projectPython -ArgumentList @('-m','streamlit','run','ui/app.py','--server.address','127.0.0.1','--server.port','8501','--server.headless','true','--browser.gatherUsageStats','false') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectLogs ($projectStamp + '-ui.stdout.log')) -RedirectStandardError (Join-Path $projectLogs ($projectStamp + '-ui.stderr.log'))
        $ui.Id | Set-Content -LiteralPath (Join-Path $projectRuntime 'd2-ui.pid')
    } finally { $env:QA_API_BASE_URL = $previousApiBase }
    Write-Host 'Started project interface.'
} else { Write-Host 'Reusing project interface.' }
$uiReady = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $uiStatus = Invoke-RestMethod -Uri ($projectUiUrl + '_stcore/health') -TimeoutSec 3
        if ($uiStatus -eq 'ok') { $uiReady = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 500
}
if (-not $uiReady) { throw 'Interface did not become healthy. See .runtime/project-start logs.' }
$result = [ordered]@{started_at_utc=$projectStamp;ui_url=$projectUiUrl;api_url=$projectApiUrl;api_reused=$apiListening;ui_reused=$uiListening;api_ready=$true;ui_ready=$uiReady;database_ready=$health.database_ready;aw_database_ready=$health.aw_database_ready;database_start_error=$databaseStartError;browser_requested=(-not $NoBrowser)}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectLogs ($projectStamp + '-result.json')) -Encoding utf8
if (-not $NoBrowser) { Start-Process -FilePath $projectUiUrl }
Write-Host ('Project interface available: ' + $projectUiUrl)
