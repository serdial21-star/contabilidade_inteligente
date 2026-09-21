@echo off
setlocal
cd /d "%~dp0"
title Serdial21 - Ambiente local

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version >nul 2>&1
    if not errorlevel 1 (
        ".venv\Scripts\python.exe" "scripts\start_local.py" %*
        goto finished
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3 "scripts\start_local.py" %*
    goto finished
)

where python >nul 2>&1
if not errorlevel 1 (
    python "scripts\start_local.py" %*
    goto finished
)

echo.
echo Nao foi encontrado Python 3.12 ou superior neste computador.
echo Instale o Python e tente novamente.
set "S21_EXIT_CODE=1"
goto pause_on_error

:finished
set "S21_EXIT_CODE=%ERRORLEVEL%"

:pause_on_error
if not "%S21_EXIT_CODE%"=="0" (
    echo.
    pause
)
exit /b %S21_EXIT_CODE%
