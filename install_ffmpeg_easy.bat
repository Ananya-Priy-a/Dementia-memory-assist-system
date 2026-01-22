@echo off
REM Simple FFmpeg Installation Script for Windows
REM This script downloads and extracts FFmpeg without requiring admin rights

echo.
echo =========================================
echo  FFmpeg Installation for Dementia System
echo =========================================
echo.

REM Check if FFmpeg already exists in PATH
where ffmpeg >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo FFmpeg is already installed!
    ffmpeg -version | findstr /R "ffmpeg version"
    exit /b 0
)

echo FFmpeg not found. Creating portable installation...
echo.

REM Create ffmpeg folder in user directory
set FFMPEG_DIR=%USERPROFILE%\ffmpeg
if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"

cd /d "%FFMPEG_DIR%"
echo Downloading FFmpeg (this may take a minute)...

REM Download FFmpeg using PowerShell (no admin needed)
powershell -Command "try { Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z' -OutFile 'ffmpeg.7z' -UseBasicParsing; Write-Host 'Download complete!'; exit 0 } catch { Write-Host 'Download failed. Please visit: https://www.gyan.dev/ffmpeg/builds/' ; exit 1 }"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Download failed. Manual installation needed:
    echo 1. Download from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z
    echo 2. Extract to: %FFMPEG_DIR%
    echo 3. Add to PATH (see instructions below)
    echo.
    pause
    exit /b 1
)

echo.
echo NOTE: This downloaded the .7z archive which requires 7-Zip to extract.
echo.
echo Next Steps:
echo 1. Install 7-Zip if you don't have it (from https://www.7-zip.org/)
echo 2. Right-click on ffmpeg.7z and select "Extract Here"
echo 3. Then follow the PATH setup instructions below
echo.
echo.
echo =========== Add to Windows PATH (No Admin Needed) ===========
echo.
echo Method 1 (Easiest - Temporary for current session):
echo   Run this in PowerShell:
echo   $env:Path += ';%FFMPEG_DIR%\ffmpeg-full\bin'
echo.
echo Method 2 (Permanent - User Variables):
echo   1. Press WIN+X and search "Edit the system environment variables"
echo   2. Click "Environment Variables" button
echo   3. Under "User variables for [YourUsername]", click "New"
echo   4. Variable name: Path
echo   5. Variable value: %FFMPEG_DIR%\ffmpeg-full\bin
echo   6. Click OK, OK, OK
echo   7. Restart PowerShell
echo.
echo Method 3 (Via PowerShell - Permanent):
echo   Run as Administrator:
echo   [Environment]::SetEnvironmentVariable('Path', $env:Path + ';%FFMPEG_DIR%\ffmpeg-full\bin', 'User')
echo.
echo ============================================================
echo.
pause
