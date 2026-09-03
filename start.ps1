#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Samanvaya — One-Command Full-Stack Launcher (Windows)
  Starts all 3 microservices in parallel and opens the browser.

.USAGE
  .\start.ps1
#>

Write-Host ""
Write-Host "  🌙 Samanvaya (समान्वय) — Full-Stack Launcher" -ForegroundColor Cyan
Write-Host "  ═══════════════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host "  🧠  ML FastAPI        → http://localhost:8001" -ForegroundColor Yellow
Write-Host "  🛡️   Node.js Gateway  → http://localhost:3000" -ForegroundColor Magenta
Write-Host "  🚀  React Dashboard  → http://localhost:5173" -ForegroundColor Green
Write-Host ""

$root = $PSScriptRoot

# 1. Python ML Service
Write-Host "[1/3] Launching ML Microservice (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "Set-Location '$root\ml_service'; if (Test-Path venv\Scripts\Activate.ps1) { .\venv\Scripts\Activate.ps1 }; python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

Start-Sleep -Seconds 2

# 2. Node.js Gateway
Write-Host "[2/3] Launching Node.js Zero-Trust Gateway..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "Set-Location '$root\backend'; npx tsx src/index.ts"

Start-Sleep -Seconds 2

# 3. React Vite Frontend
Write-Host "[3/3] Launching React Dashboard (Vite)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "Set-Location '$root\frontend'; npm run dev"

# Open browser after compile time
Write-Host ""
Write-Host "  Waiting for Vite to compile (5s)..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "  ✅ All services running! Close the 3 terminal windows to stop." -ForegroundColor Green
Write-Host ""
Write-Host "  Quick test:" -ForegroundColor White
Write-Host "  curl http://localhost:8001/" -ForegroundColor DarkGray
Write-Host "  curl http://localhost:3000/" -ForegroundColor DarkGray
