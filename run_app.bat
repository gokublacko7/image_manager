@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=F:\Conda\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
)

if not exist "%PYTHON_EXE%" (
    echo Python was not found in Anaconda locations.
    echo Update PYTHON_EXE in this file or install Python 3.11+.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"
"%PYTHON_EXE%" -m image_dataset_manager.main

if errorlevel 1 (
    echo.
    echo App failed to start. If PySide6 is missing, run:
    echo "%PYTHON_EXE%" -m pip install -r requirements.txt
    pause
)
