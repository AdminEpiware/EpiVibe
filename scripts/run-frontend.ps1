$root = Split-Path -Parent $PSScriptRoot

$frontend = Join-Path $root "frontend"

if (-not (Test-Path (Join-Path $frontend "package.json"))) {
    Write-Host "ERROR: Frontend package.json not found." -ForegroundColor Red
    exit 1
}

Set-Location $frontend

Write-Host "Starting EpiVibe Frontend..." -ForegroundColor Green

npm run dev