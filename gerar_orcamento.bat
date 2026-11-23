@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" -m pip install -q -r requirements.txt
"%PY%" orcamento.py
echo.
pause
