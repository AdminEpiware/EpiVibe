$root = Split-Path -Parent $PSScriptRoot

$backend = Join-Path $root "backend"
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "ERROR: Python virtual environment not found." -ForegroundColor Red
    exit 1
}

Set-Location $backend

Write-Host "Starting EpiVibe Backend..." -ForegroundColor Green

& $python -m uvicorn app.main:app --reload --port 8000