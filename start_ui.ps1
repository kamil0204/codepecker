#!/usr/bin/env pwsh

Write-Host "🚀 Starting CodePecker Server with UI..." -ForegroundColor Green
Write-Host ""

# Start the server
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
$serverProcess = Start-Process python -ArgumentList "server.py" -PassThru -WindowStyle Hidden

# Wait for server to start
Write-Host "Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Server is running!" -ForegroundColor Green
        
        # Open browser
        Write-Host "🌐 Opening browser..." -ForegroundColor Cyan
        Start-Process "http://localhost:8000"
        
        Write-Host ""
        Write-Host "CodePecker is running!" -ForegroundColor Green
        Write-Host "🎨 UI: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Press Ctrl+C to stop the server..." -ForegroundColor Yellow
        
        # Wait for user to stop
        try {
            while ($true) {
                Start-Sleep -Seconds 1
            }
        }
        catch {
            Write-Host ""
            Write-Host "Stopping server..." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "❌ Server failed to start properly" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Could not connect to server. Please check if it started correctly." -ForegroundColor Red
}
finally {
    # Clean up
    if ($serverProcess -and !$serverProcess.HasExited) {
        Write-Host "🛑 Stopping server..." -ForegroundColor Yellow
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Server stopped." -ForegroundColor Green
    }
}
