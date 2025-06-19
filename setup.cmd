@echo off
REM Setup script for Windows/XAMPP

IF NOT EXIST venv (
    python -m venv venv
)

call venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

ECHO.
ECHO Environment ready. To start the collector run:
ECHO    python collector.py
ECHO To start the web server run:
ECHO    flask --app app run

