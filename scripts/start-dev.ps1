# EpiVibe - Start Frontend and Backend

$root = Split-Path -Parent $PSScriptRoot

$backendScript = Join-Path $PSScriptRoot "run-backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "run-frontend.ps1"

Write-Host "Starting EpiVibe Development Environment..." -ForegroundColor Cyan

Start-Process powershell.exe -WorkingDirectory $root -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$backendScript`""
)

Start-Process powershell.exe -WorkingDirectory $root -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$frontendScript`""
)

Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Green