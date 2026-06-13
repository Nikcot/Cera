@echo off
chcp 65001 >nul
echo Starting Cera with full error output...
echo.

py main.py 2>&1

echo.
echo.
echo Press any key to close...
pause >nul
