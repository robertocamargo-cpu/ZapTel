@echo off
setlocal
cd /d "%~dp0"
echo --- ABRINDO DASHBOARD ---
python visualizar_dashboard.py
pause
