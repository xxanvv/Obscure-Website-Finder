@echo off
echo Checking for virtual environment...

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    
    echo Installing dependencies...
    call venv\Scripts\activate
    pip install requests pillow urllib3 tk ipaddress playwright nest_asyncio
    playwright install chromium
) else (
    echo Virtual environment already exists.
    call venv\Scripts\activate
)

echo Starting OWF...
python OWF.py
