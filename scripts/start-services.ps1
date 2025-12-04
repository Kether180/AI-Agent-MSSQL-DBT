# DataMigrate AI - Start All Services
# This script starts all three services:
# 1. Go Backend (port 8080)
# 2. Python AI Service (port 8081)
# 3. Vue Frontend (port 5173)

Write-Host "DataMigrate AI - Starting Services" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Check if PostgreSQL is running and start if needed
Write-Host "`nChecking PostgreSQL..." -ForegroundColor Yellow
$pgRunning = Get-Process -Name "postgres" -ErrorAction SilentlyContinue
if (-not $pgRunning) {
    Write-Host "PostgreSQL is not running. Attempting to start..." -ForegroundColor Yellow

    # Try to start PostgreSQL service
    try {
        # First try the Windows service
        $pgService = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
        if ($pgService) {
            Start-Service -Name "postgresql-x64-16" -ErrorAction Stop
            Write-Host "PostgreSQL service started successfully!" -ForegroundColor Green
        } else {
            # Fallback: Try pg_ctl directly
            $pgCtlPath = "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe"
            $pgDataPath = "C:\Program Files\PostgreSQL\16\data"

            if (Test-Path $pgCtlPath) {
                & $pgCtlPath start -D $pgDataPath -w
                Write-Host "PostgreSQL started using pg_ctl!" -ForegroundColor Green
            } else {
                Write-Host "Warning: Could not find PostgreSQL installation!" -ForegroundColor Red
                Write-Host "Please start PostgreSQL manually on port 5432" -ForegroundColor Red
            }
        }
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "Warning: Could not start PostgreSQL automatically!" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        Write-Host "Please start PostgreSQL manually (may require admin privileges)" -ForegroundColor Yellow
    }
} else {
    Write-Host "PostgreSQL is already running!" -ForegroundColor Green
}

# Set working directory
$projectRoot = Split-Path -Parent $PSScriptRoot

# Start Go Backend
Write-Host "`n1. Starting Go Backend (port 8080)..." -ForegroundColor Cyan
$goProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d $projectRoot\backend && go run cmd\server\main.go" -PassThru -WindowStyle Normal
Write-Host "   Go Backend started (PID: $($goProcess.Id))" -ForegroundColor Green

# Wait for Go backend to start
Start-Sleep -Seconds 3

# Start Python AI Service (full migration + chat API)
Write-Host "`n2. Starting Python AI Service (port 8081)..." -ForegroundColor Cyan
$pythonProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d $projectRoot && python -m uvicorn agents.api:app --host 0.0.0.0 --port 8081 --reload" -PassThru -WindowStyle Normal
Write-Host "   Python AI Service started (PID: $($pythonProcess.Id))" -ForegroundColor Green

# Wait for Python service to start
Start-Sleep -Seconds 3

# Start Vue Frontend
Write-Host "`n3. Starting Vue Frontend (port 5173)..." -ForegroundColor Cyan
$vueProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d $projectRoot\frontend && npm run dev" -PassThru -WindowStyle Normal
Write-Host "   Vue Frontend started (PID: $($vueProcess.Id))" -ForegroundColor Green

# Summary
Write-Host "`n==================================" -ForegroundColor Green
Write-Host "All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "  - Frontend:    http://localhost:5173" -ForegroundColor White
Write-Host "  - Go Backend:  http://localhost:8080" -ForegroundColor White
Write-Host "  - AI Service:  http://localhost:8081" -ForegroundColor White
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor Yellow
Write-Host "  - Go Backend Swagger:  http://localhost:8080/swagger/index.html" -ForegroundColor White
Write-Host "  - AI Service Docs:     http://localhost:8081/docs" -ForegroundColor White
Write-Host ""
Write-Host "To stop services, close the terminal windows or press Ctrl+C in each." -ForegroundColor Gray
