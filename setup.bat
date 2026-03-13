@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo CCAgent Annotator Setup Script (Windows)
echo ==========================================

:: Get the directory where this script lives
set "SCRIPT_DIR=%~dp0"

:: ==========================================
:: 1. Ensure Miniconda is available
:: ==========================================

:: Find conda.exe (not conda.bat - .bat breaks batch parser state)
set "CONDA_EXE="
where conda.exe >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('where conda.exe') do (
        if not defined CONDA_EXE set "CONDA_EXE=%%i"
    )
)

:: Check common install locations
if not defined CONDA_EXE (
    if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" set "CONDA_EXE=%USERPROFILE%\miniconda3\Scripts\conda.exe"
)
if not defined CONDA_EXE (
    if exist "%USERPROFILE%\Miniconda3\Scripts\conda.exe" set "CONDA_EXE=%USERPROFILE%\Miniconda3\Scripts\conda.exe"
)
if not defined CONDA_EXE (
    if exist "C:\Miniconda3\Scripts\conda.exe" set "CONDA_EXE=C:\Miniconda3\Scripts\conda.exe"
)

if defined CONDA_EXE (
    echo [OK] Found conda at !CONDA_EXE!
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

echo Installing Miniconda - this may take a few minutes...
start /wait "" "!MINICONDA_INSTALLER!" /InstallationType=JustMe /AddToPath=1 /RegisterPython=0 /S /D=%USERPROFILE%\miniconda3
del "!MINICONDA_INSTALLER!" >nul 2>&1

set "CONDA_EXE=%USERPROFILE%\miniconda3\Scripts\conda.exe"
if not exist "!CONDA_EXE!" (
    echo [ERROR] Miniconda installation failed.
    pause
    exit /b 1
)

:: Add to PATH for this session
set "PATH=%USERPROFILE%\miniconda3;%USERPROFILE%\miniconda3\Scripts;%USERPROFILE%\miniconda3\Library\bin;!PATH!"
echo [OK] Miniconda installed.

:conda_ready
:: Show version using conda.exe directly (never call conda.bat - it breaks batch state)
for /f "tokens=*" %%v in ('"!CONDA_EXE!" --version 2^>^&1') do echo [OK] %%v
echo:

:: ==========================================
:: 2. Ensure Node.js 18+ is available
:: ==========================================

set "NODE_OK=0"
where node >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=1 delims=." %%a in ('node --version') do set "NODE_VER_RAW=%%a"
    set "NODE_MAJOR=!NODE_VER_RAW:v=!"
    if !NODE_MAJOR! GEQ 18 (
        echo [OK] Node.js detected:
        node --version
        set "NODE_OK=1"
    ) else (
        echo [WARNING] Node.js found but version too old - need 18+.
    )
)

if "!NODE_OK!"=="0" (
    echo [INFO] Downloading Node.js 18 LTS...
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
)

echo:

:: ==========================================
:: 3. Accept conda Terms of Service
:: ==========================================

echo Accepting conda channel Terms of Service...
"!CONDA_EXE!" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main >nul 2>&1
"!CONDA_EXE!" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r >nul 2>&1
"!CONDA_EXE!" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2 >nul 2>&1

:: ==========================================
:: 4. Create / reuse conda environment
:: ==========================================

"!CONDA_EXE!" env list > "%TEMP%\conda_envs.txt" 2>&1
findstr /B "agentnet " "%TEMP%\conda_envs.txt" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Conda environment 'agentnet' already exists.
) else (
    echo Creating conda environment 'agentnet' with Python 3.11...
    "!CONDA_EXE!" create -n agentnet python=3.11 -y
    if errorlevel 1 (
        echo [ERROR] Failed to create conda environment.
        pause
        exit /b 1
    )
    echo [OK] Conda environment created.
)
del "%TEMP%\conda_envs.txt" >nul 2>&1

:: Activate the environment
echo Activating conda environment 'agentnet'...

:: Ensure conda shell hooks are initialized first
set "CONDA_ROOT=!CONDA_EXE:\Scripts\conda.exe=!"
if exist "!CONDA_ROOT!\Scripts\activate.bat" (
    call "!CONDA_ROOT!\Scripts\activate.bat"
)
call conda activate agentnet

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment.
    pause
    exit /b 1
)
:: Restore Node.js in PATH (conda activate resets PATH)
if exist "C:\Program Files\nodejs\npm.cmd" (
    set "PATH=C:\Program Files\nodejs;!PATH!"
)
echo [OK] Environment activated. Python:
python --version

:: ==========================================
:: 5. Install Python dependencies
:: ==========================================

echo:
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
:: 6. Install Node.js dependencies
:: ==========================================

echo:
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
:: 7. Check/create libs directory for DLLs
:: ==========================================

echo:
if not exist "%SCRIPT_DIR%agentnet-annotator\api\libs" (
    echo Creating libs directory for DLLs...
    mkdir "%SCRIPT_DIR%agentnet-annotator\api\libs"
    echo [OK] Created agentnet-annotator\api\libs directory.
) else (
    echo [OK] libs directory already exists.
)

:: ==========================================
:: 8. Create .env from .env.example if needed
:: ==========================================

echo:
if not exist "%SCRIPT_DIR%.env" (
    if exist "%SCRIPT_DIR%.env.example" (
        copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
        echo [OK] Created .env from .env.example
        echo [INFO] Edit .env with your Aliyun OSS credentials if you need cloud upload.
    ) else (
        echo [WARNING] .env.example not found. Cloud upload will not work without .env configuration.
    )
) else (
    echo [OK] .env already exists.
)

:: ==========================================
:: Done
:: ==========================================

echo:
echo ==========================================
echo Setup completed successfully!
echo ==========================================
echo:
echo Next steps:
echo:
echo 1. Install OBS Studio - required for screen recording:
echo    Download from https://obsproject.com/
echo:
echo 2. Run the application:
echo    start.bat
echo:

pause
endlocal
