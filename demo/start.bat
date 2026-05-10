@echo off
REM start.bat - Windows one-click launcher for sprinkler-tools
REM Sets up a Python venv, installs deps, runs the FastAPI backend.

setlocal

cd /d "%~dp0backend"

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Could not create the virtual environment.
        echo Make sure Python 3.10 or newer is installed and on your PATH.
        echo Download from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo ============================================================
echo  sprinkler-tools API starting on http://localhost:8000
echo  Open frontend\index.html in your browser to use the demo.
echo  Press Ctrl+C to stop the server.
echo ============================================================
echo.

uvicorn app:app --host 0.0.0.0 --port 8000 --reload

endlocal
