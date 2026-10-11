param(
    [string]$OutputDirectory = 'eval/artifacts/d2/source/docx-render'
)
$ErrorActionPreference = 'Stop'
$ProjectDirectory = Split-Path -Parent $PSScriptRoot
$ResolvedOutput = [System.IO.Path]::GetFullPath((Join-Path $ProjectDirectory $OutputDirectory))
if (-not $ResolvedOutput.StartsWith($ProjectDirectory + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Renderer output must remain inside the project.'
}
New-Item -ItemType Directory -Path $ResolvedOutput -Force | Out-Null
$InputNames = @('Chinook业务指标口径手册.docx', 'metallica-introduction.docx')
$NativeWord = New-Object -ComObject Word.Application
$NativeWord.Visible = $false
$NativeWord.DisplayAlerts = 0
$NativeWord.AutomationSecurity = 3
$NativeWord.ScreenUpdating = $false
$Results = @()
try {
    foreach ($InputName in $InputNames) {
        $DocumentPath = Join-Path $ProjectDirectory ('data/docs/raw/d2/' + $InputName)
        $PdfPath = Join-Path $ResolvedOutput ([System.IO.Path]::GetFileNameWithoutExtension($InputName) + '.pdf')
        $Document = $NativeWord.Documents.Open($DocumentPath, $false, $true)
        try {
            $Document.Repaginate()
            $PageCount = $Document.ComputeStatistics(2)
            $Document.ExportAsFixedFormat($PdfPath, 17)
            $Results += [pscustomobject]@{
                input = 'data/docs/raw/d2/' + $InputName
                output_pdf = $OutputDirectory.TrimEnd('/') + '/' + [System.IO.Path]::GetFileName($PdfPath)
                actual_page_count = $PageCount
                renderer = 'Microsoft Word native COM ExportAsFixedFormat'
                read_only = $true
                status = 'rendered'
            }
        }
        finally {
            $Document.Close(0)
            [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Document)
        }
    }
}
finally {
    $NativeWord.Quit(0)
    [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($NativeWord)
}
$Results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $ResolvedOutput 'word-render-audit.json') -Encoding utf8
$Results | ConvertTo-Json -Depth 4
