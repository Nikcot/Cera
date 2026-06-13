@echo off
chcp 65001 >nul
title Cera Desktop

echo.
echo   🚀 Запуск Цера Десктоп...
echo.

set PYTHON_CMD=py -3.11

REM Проверяем зависимости (грубо)
%PYTHON_CMD% -c "import webview; import pyaudiowpatch; import faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo   📦 Устанавливаю зависимости...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Ошибка установки
        pause
        exit /b
    )
)

%PYTHON_CMD% main.py
if errorlevel 1 pause
