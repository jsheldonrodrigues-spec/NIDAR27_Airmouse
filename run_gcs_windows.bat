@echo off
title TEAM EDITH - AirMouse Ground Control Station (GCS)
echo Starting TEAM EDITH AirMouse Ground Control Station...
python airmouse_gcs.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Trying local Python path...
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" airmouse_gcs.py
)
pause
