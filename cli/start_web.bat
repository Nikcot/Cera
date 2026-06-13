@echo off
chcp 65001 >nul
title Cera Web - AI Транскрибация

echo ====================================
echo   Cera Web - Запуск сервера
echo ====================================
echo.
echo Сервер запустится на http://localhost:5000
echo Браузер откроется автоматически...
echo.

py -3.11 cera_web.py

pause
