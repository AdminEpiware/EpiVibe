# EpiVibe - Start Backend with Environment Configuration

$root = Split-Path -Parent $PSScriptRoot

$backend = Join-Path $root "backend"
$python = Join-Path $root ".venv\Scripts\python.exe"
$envFile = Join-Path $backend ".env"

if (-not (Test-Path $python)) {
    Write-Host "ERROR: Python virtual environment not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: backend/.env file not found." -ForegroundColor Red
    exit 1
}

# Load environment variables from backend/.env
foreach ($line in Get-Content $envFile) {

    $line = $line.Trim()

    if (-not $line -or $line.StartsWith("#")) {
        continue
    }

    if ($line -match '^([^=]+)=(.*)$') {

        $name = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")

        [Environment]::SetEnvironmentVariable(
            $name,
            $value,
            "Process"
        )
    }
}

# Verify configuration without exposing API keys
Write-Host ""
Write-Host "EpiVibe Environment Verification" -ForegroundColor Cyan

Write-Host "Qloo API Key: " -NoNewline
Write-Host $(if ($env:QLOO_API_KEY) { "Configured" } else { "Missing" })

Write-Host "Gemini API Key: " -NoNewline
Write-Host $(if ($env:GEMINI_API_KEY) { "Configured" } else { "Missing" })

if (-not $env:QLOO_API_KEY -or -not $env:GEMINI_API_KEY) {
    Write-Host "ERROR: Required API keys are missing." -ForegroundColor Red
    exit 1
}

Set-Location $backend

Write-Host ""
Write-Host "Starting EpiVibe Backend..." -ForegroundColor Green

& $python -m uvicorn app.main:app --reload --port 8000