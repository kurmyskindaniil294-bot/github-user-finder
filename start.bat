@echo off
chcp 65001 >nul
title GitHub User Finder
color 0A
echo ========================================
echo    GitHub User Finder
echo    Author: Mariya Alekseeva
echo ========================================
echo.
echo Installing dependencies...
pip install requests
echo.
echo Running application...
python main.py
pause