@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%PROJECT_DIR%portable_python\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=F:\Conda\python.exe"
)

if not exist "%PYTHON_EXE%" (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
    )
)

if "%PYTHON_EXE%"=="py" goto run_app

if not exist "%PYTHON_EXE%" (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="python" goto run_app

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
)

if not exist "%PYTHON_EXE%" (
    echo Python was not found in Anaconda locations.
    echo Install Python 3.11+, add portable Python at portable_python\python.exe, or update PYTHON_EXE in this file.
    pause
    exit /b 1
)

:run_app
cd /d "%PROJECT_DIR%"
"%PYTHON_EXE%" -m image_dataset_manager.main

if errorlevel 1 (
    echo.
    echo App failed to start. If PySide6 is missing, run:
    echo "%PYTHON_EXE%" -m pip install -r requirements.txt
    pause
)
