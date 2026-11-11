# Startet den Spot-Kurs und öffnet ihn im Browser.
#
# Der Kurs braucht ein Python, in dem spotlab installiert ist. Gesucht wird in
# dieser Reihenfolge: die .venv der Schülerausgabe von spotlab daneben, dann
# jedes "python" im PATH, das spotlab importieren kann.

# "Continue": ein Python ohne spotlab schreibt nach stderr, das soll die Suche nicht abbrechen
$ErrorActionPreference = "Continue"
$wurzel = $PSScriptRoot

$kandidaten = @(
    (Join-Path $wurzel "..\spotlab\.venv\Scripts\python.exe"),
    (Join-Path $env:USERPROFILE "miniconda3\python.exe")
) + @(Get-Command python -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source })

$python = $null
foreach ($k in $kandidaten) {
    if ($k -and (Test-Path $k)) {
        & $k -c "import spotlab" 2>$null
        if ($LASTEXITCODE -eq 0) { $python = $k; break }
    }
}
if (-not $python) {
    Write-Host "Kein Python mit spotlab gefunden. Zuerst spotlab einrichten (einrichten.cmd)." -ForegroundColor Red
    exit 1
}

Start-Process "http://127.0.0.1:5200"
& $python (Join-Path $wurzel "server.py")
