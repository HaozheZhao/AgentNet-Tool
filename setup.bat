@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo AgentNet Annotator Setup Script (Windows)
echo ==========================================

:: ==========================================
:: 1. Find Python 3.11+
:: ==========================================

:: Try 'py' launcher first (standard on Windows 11), then 'python'
set PYTHON_CMD=
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
    )
)

if "!PYTHON_CMD!"=="" (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11 or later from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('!PYTHON_CMD! --version 2^>^&1') do set PYTHON_VERSION=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if !PYTHON_MAJOR! LSS 3 (
    echo [ERROR] Python 3.11+ is required. Found Python !PYTHON_VERSION!
    pause
    exit /b 1
)
if !PYTHON_MAJOR! EQU 3 if !PYTHON_MINOR! LSS 11 (
    echo [ERROR] Python 3.11+ is required. Found Python !PYTHON_VERSION!
    pause
    exit /b 1
)
echo [OK] Python !PYTHON_VERSION! detected (using "!PYTHON_CMD!").

:: ==========================================
:: 2. Check Node.js 18+ is installed
:: ==========================================

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js 18 or later from https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=1 delims=." %%a in ('node --version') do set NODE_VER_RAW=%%a
set NODE_MAJOR=!NODE_VER_RAW:v=!

if !NODE_MAJOR! LSS 18 (
    echo [ERROR] Node.js 18+ is required. Found Node.js v!NODE_MAJOR!
    pause
    exit /b 1
)
echo [OK] Node.js detected:
node --version

echo.

:: ==========================================
:: 3. Create Python virtual environment
:: ==========================================

if not exist "venv" (
    echo Creating Python virtual environment...
    !PYTHON_CMD! -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

:: ==========================================
:: 4. Activate venv and install pip dependencies
:: ==========================================

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

echo Installing Python dependencies...
pip install -r requirements_windows.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed.

:: ==========================================
:: 5. Install Node.js dependencies
:: ==========================================

echo.
echo Installing Node.js dependencies...
cd agentnet-annotator
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies.
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] Node.js dependencies installed.

:: ==========================================
:: 6. Check/create libs directory for DLLs
:: ==========================================

echo.
if not exist "agentnet-annotator\api\libs" (
    echo Creating libs directory for DLLs...
    mkdir "agentnet-annotator\api\libs"
    echo [OK] Created agentnet-annotator\api\libs directory.
) else (
    echo [OK] libs directory already exists.
)

:: ==========================================
:: Done
:: ==========================================

echo.
echo ==========================================
echo Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo.
echo 1. Copy .env.example to .env and fill in your OSS credentials:
echo    copy .env.example .env
echo    notepad .env
echo.
echo 2. Install OBS Studio (required for screen recording):
echo    Download from https://obsproject.com/
echo.
echo 3. Run the application:
echo    start.bat
echo.

pause
endlocal
