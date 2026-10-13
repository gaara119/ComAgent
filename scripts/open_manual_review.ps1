param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$reviewProjectRoot = Split-Path -Parent $PSScriptRoot
$reviewPage = Join-Path $reviewProjectRoot 'eval\reports\oct12\manual-review\全部待人工审核统一入口.html'
if (-not (Test-Path -LiteralPath $reviewPage -PathType Leaf)) {
    throw ('Review HTML was not found: ' + $reviewPage)
}
if ($CheckOnly) {
    Write-Output $reviewPage
    exit 0
}
Start-Process -FilePath $reviewPage
