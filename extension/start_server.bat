@echo off
chcp 65001 >nul
title СЕРВЕР ЦЕРА (Python 3.11)

echo.
echo   🚀 Запуск сервера на Python 3.11...
echo.

set PYTHON_CMD=py -3.11

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Python 3.11 не найден!
    echo Установите его с сайта Python.org
    pause
    exit /b
)

cd server
%PYTHON_CMD% cera_server.py
if errorlevel 1 (
    echo.
    echo ❌ Сервер упал.
    pause
)

pause
