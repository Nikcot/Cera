@echo off
chcp 65001 >nul
title Установка сервера Цера (Python 3.11)

echo.
echo   [1/2] Поиск Python 3.11...

set PYTHON_CMD=py -3.11

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Python 3.11 не найден!
    echo Установите его с https://www.python.org/downloads/
    pause
    exit /b
)

echo   ✅ Используем Python 3.11
%PYTHON_CMD% --version

echo.
echo   [2/2] Установка зависимостей для 3.11...
cd server
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей.
    pause
    exit /b
)

echo.
echo   ✅ Готово!
echo   Теперь запустите start_server.bat
pause
