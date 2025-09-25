@echo off
echo Starting CodePecker Server with UI...
echo.
echo Opening browser in 3 seconds...
echo.

REM Start the server in the background
start /B python server.py

REM Wait a moment for the server to start
timeout /t 3 /nobreak >nul

REM Open the browser
start http://localhost:8000

echo.
echo CodePecker is running!
echo UI: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop the server...
pause >nul

REM Kill the server process
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *server.py*" 2>nul
echo Server stopped.
