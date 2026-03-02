@echo off
setlocal enabledelayedexpansion

echo Starting AgentNet Annotator...

:: ==========================================
:: 1. Load .env file if it exists
:: ==========================================

if exist ".env" (
    echo Loading environment variables from .env...
    for /f "usebackq tokens=* delims=" %%a in (".env") do (
        set "LINE=%%a"
        if not "!LINE!"=="" (
            :: Skip lines starting with #
            set "FIRST_CHAR=!LINE:~0,1!"
            if not "!FIRST_CHAR!"=="#" (
                set "%%a"
            )
        )
    )
) else (
    echo [WARNING] .env file not found.
    echo Cloud upload features may not work without OSS credentials.
    echo Copy .env.example to .env and configure your credentials.
    echo.
)

:: ==========================================
:: 2. Kill existing process on port 5328
:: ==========================================

echo Checking for existing processes on port 5328...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :5328 ^| findstr LISTENING 2^>nul') do (
    if not "%%p"=="0" (
        echo Killing existing process on port 5328 (PID: %%p)...
        taskkill /F /PID %%p >nul 2>&1
    )
)

:: ==========================================
:: 3. Activate virtual environment
:: ==========================================

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    exit /b 1
)

call venv\Scripts\activate.bat
echo [OK] Virtual environment activated.
echo Python:
python --version

:: ==========================================
:: 4. Check npm is available
:: ==========================================

npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found. Please install Node.js and run setup.bat first.
    exit /b 1
)
echo [OK] npm is available.
echo Node:
node --version

echo.

:: ==========================================
:: 5. Start the application
:: ==========================================

echo Starting AgentNet Annotator application...
cd agentnet-annotator
npm start

endlocal
