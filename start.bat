@echo off
setlocal enabledelayedexpansion

echo Starting AgentNet Annotator...

:: ==========================================
:: 1. Load .env file if it exists
:: ==========================================

if exist ".env" (
    echo Loading environment variables from .env...
    for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%b"=="" (
            set "%%a=%%b"
        )
    )
) else (
    echo [WARNING] .env file not found.
    echo Cloud upload features may not work without OSS credentials.
    echo Copy .env.example to .env and configure your credentials.
    echo:
)

:: ==========================================
:: 2. Kill existing process on port 5328
:: ==========================================

echo Checking for existing processes on port 5328...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :5328 ^| findstr LISTENING 2^>nul') do (
    if not "%%p"=="0" (
        echo Killing existing process on port 5328, PID: %%p
        taskkill /F /PID %%p >nul 2>&1
    )
)

:: ==========================================
:: 3. Find conda and activate environment
:: ==========================================

:: Find conda root directory
set "CONDA_ROOT="
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" set "CONDA_ROOT=%USERPROFILE%\miniconda3"
if exist "%USERPROFILE%\Miniconda3\Scripts\activate.bat" set "CONDA_ROOT=%USERPROFILE%\Miniconda3"
if exist "C:\Miniconda3\Scripts\activate.bat" set "CONDA_ROOT=C:\Miniconda3"

:: Also try to find via where
if not defined CONDA_ROOT (
    where conda.exe >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%i in ('where conda.exe') do (
            if not defined CONDA_ROOT (
                set "_CPATH=%%i"
                set "CONDA_ROOT=!_CPATH:\Scripts\conda.exe=!"
            )
        )
    )
)

if not defined CONDA_ROOT (
    echo [ERROR] Conda not found. Please run setup.bat first.
    pause
    exit /b 1
)

call "!CONDA_ROOT!\Scripts\activate.bat"
call conda activate agentnet
if errorlevel 1 (
    echo [ERROR] Conda environment 'agentnet' not found. Please run setup.bat first.
    pause
    exit /b 1
)
echo [OK] Conda environment 'agentnet' activated.

:: ==========================================
:: 4. Start the application
:: ==========================================

echo:
echo Starting AgentNet Annotator application...
echo Close this window or press Ctrl+C to stop
echo:
cd agentnet-annotator
call npm start

pause
endlocal
