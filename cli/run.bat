@echo off
chcp 65001 >nul
echo ====================================
echo   Цера - AI Транскрибация
echo ====================================
echo.

REM Проверка Python 3.11
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python 3.11 не найден!
    echo.
    echo Установите Python 3.11: https://www.python.org/downloads/release/python-3119/
    echo.
    pause
    exit /b 1
)

echo ✅ Python найден
echo.
echo 🚀 Запуск Цера...
echo.

py main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Ошибка запуска приложения
    pause
)
