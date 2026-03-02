@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo AgentNet Annotator Setup Script (Windows)
echo ==========================================

:: Get the directory where this script lives
set "SCRIPT_DIR=%~dp0"

:: ==========================================
:: 1. Ensure Miniconda is available
:: ==========================================

where conda >nul 2>&1
if not errorlevel 1 (
    echo [OK] Conda already available.
    goto :conda_ready
)

:: Check common install locations
set "CONDA_PATH="
if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" set "CONDA_PATH=%USERPROFILE%\miniconda3"
if exist "%USERPROFILE%\Miniconda3\Scripts\conda.exe" set "CONDA_PATH=%USERPROFILE%\Miniconda3"
if exist "C:\Miniconda3\Scripts\conda.exe" set "CONDA_PATH=C:\Miniconda3"

if defined CONDA_PATH (
    echo [OK] Found Conda at !CONDA_PATH!
    call "!CONDA_PATH!\Scripts\activate.bat"
    goto :conda_ready
)

:: Download and install Miniconda
echo [INFO] Conda not found. Downloading Miniconda...
set "MINICONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
set "MINICONDA_INSTALLER=%TEMP%\Miniconda3-latest-Windows-x86_64.exe"

where curl >nul 2>&1
if not errorlevel 1 (
    curl -L -o "!MINICONDA_INSTALLER!" "!MINICONDA_URL!"
) else (
    powershell -Command "Invoke-WebRequest -Uri '!MINICONDA_URL!' -OutFile '!MINICONDA_INSTALLER!'"
)

if not exist "!MINICONDA_INSTALLER!" (
    echo [ERROR] Failed to download Miniconda.
    pause
    exit /b 1
)

echo Installing Miniconda (this may take a few minutes)...
start /wait "" "!MINICONDA_INSTALLER!" /InstallationType=JustMe /AddToPath=1 /RegisterPython=0 /S /D=%USERPROFILE%\miniconda3
del "!MINICONDA_INSTALLER!" >nul 2>&1

set "CONDA_PATH=%USERPROFILE%\miniconda3"
if not exist "!CONDA_PATH!\Scripts\conda.exe" (
    echo [ERROR] Miniconda installation failed.
    pause
    exit /b 1
)

:: Add to PATH for this session
set "PATH=!CONDA_PATH!;!CONDA_PATH!\Scripts;!CONDA_PATH!\Library\bin;!PATH!"
call "!CONDA_PATH!\Scripts\activate.bat"
echo [OK] Miniconda installed at !CONDA_PATH!

:conda_ready
echo [OK] Conda version:
call conda --version
echo.

:: ==========================================
:: 2. Ensure Node.js 18+ is available
:: ==========================================

where node >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=1 delims=." %%a in ('node --version') do set "NODE_VER_RAW=%%a"
    set "NODE_MAJOR=!NODE_VER_RAW:v=!"
    if !NODE_MAJOR! GEQ 18 (
        echo [OK] Node.js detected:
        node --version
        goto :node_ready
    )
    echo [WARNING] Node.js found but version too old (need 18+).
)

echo [INFO] Node.js not found. Downloading Node.js 18 LTS...
set "NODE_URL=https://nodejs.org/dist/v18.20.8/node-v18.20.8-x64.msi"
set "NODE_INSTALLER=%TEMP%\node-v18.20.8-x64.msi"

where curl >nul 2>&1
if not errorlevel 1 (
    curl -L -o "!NODE_INSTALLER!" "!NODE_URL!"
) else (
    powershell -Command "Invoke-WebRequest -Uri '!NODE_URL!' -OutFile '!NODE_INSTALLER!'"
)

if not exist "!NODE_INSTALLER!" (
    echo [ERROR] Failed to download Node.js.
    pause
    exit /b 1
)

echo Installing Node.js 18 LTS...
msiexec /i "!NODE_INSTALLER!" /qn /norestart
del "!NODE_INSTALLER!" >nul 2>&1

:: Refresh PATH to pick up newly installed Node.js
set "PATH=C:\Program Files\nodejs;!PATH!"

where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js installation failed. You may need to restart your terminal.
    echo Download manually from https://nodejs.org/ if this persists.
    pause
    exit /b 1
)
echo [OK] Node.js installed:
node --version

:node_ready
echo.

:: ==========================================
:: 3. Create / reuse conda environment
:: ==========================================

call conda env list | findstr /B "agentnet " >nul 2>&1
if not errorlevel 1 (
    echo [OK] Conda environment 'agentnet' already exists. Using it.
) else (
    echo Creating conda environment 'agentnet' with Python 3.11...
    call conda create -n agentnet python=3.11 -y
    if errorlevel 1 (
        echo [ERROR] Failed to create conda environment.
        pause
        exit /b 1
    )
    echo [OK] Conda environment created.
)

:: Activate the environment
echo Activating conda environment 'agentnet'...
call conda activate agentnet
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment.
    pause
    exit /b 1
)
echo [OK] Environment activated. Python:
python --version

:: ==========================================
:: 4. Install Python dependencies
:: ==========================================

echo.
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

echo Installing Python dependencies...
pip install -r "%SCRIPT_DIR%requirements_windows.txt"
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
cd "%SCRIPT_DIR%agentnet-annotator"
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies.
    cd "%SCRIPT_DIR%"
    pause
    exit /b 1
)
cd "%SCRIPT_DIR%"
echo [OK] Node.js dependencies installed.

:: ==========================================
:: 6. Check/create libs directory for DLLs
:: ==========================================

echo.
if not exist "%SCRIPT_DIR%agentnet-annotator\api\libs" (
    echo Creating libs directory for DLLs...
    mkdir "%SCRIPT_DIR%agentnet-annotator\api\libs"
    echo [OK] Created agentnet-annotator\api\libs directory.
) else (
    echo [OK] libs directory already exists.
)

:: ==========================================
:: 7. Create .env from .env.example if needed
:: ==========================================

echo.
if not exist "%SCRIPT_DIR%.env" (
    if exist "%SCRIPT_DIR%.env.example" (
        copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
        echo [OK] Created .env from .env.example
        echo [INFO] Edit .env with your Aliyun OSS credentials if you need cloud upload.
        echo        notepad .env
    ) else (
        echo [WARNING] .env.example not found. Cloud upload will not work without .env configuration.
    )
) else (
    echo [OK] .env already exists.
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
echo 1. (Optional) Edit .env with your Aliyun OSS credentials for cloud upload:
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
