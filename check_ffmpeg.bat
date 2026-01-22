@echo off
REM FFmpeg Installation Checker and Setup Guide for Windows
REM This script checks if FFmpeg is installed and provides installation instructions

echo ========================================
echo FFmpeg Installation Checker
echo ========================================
echo.

REM Check if ffmpeg is available
where ffmpeg >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ FFmpeg is already installed!
    echo.
    ffmpeg -version | findstr /R "ffmpeg version"
    echo.
    echo Your app can now use advanced audio features.
    goto :end
)

echo ✗ FFmpeg is NOT currently installed
echo.
echo FFmpeg is required for audio file format conversion.
echo Without it, only WAV files will work directly.
echo.
echo ========================================
echo Installation Options:
echo ========================================
echo.
echo Option 1: Using Chocolatey (RECOMMENDED - Automatic)
echo ----------------------------------------
echo 1. Open PowerShell as Administrator
echo 2. Run: choco install ffmpeg
echo 3. Restart your terminal
echo.
echo Option 2: Manual Installation
echo ----------------------------------------
echo 1. Download from: https://ffmpeg.org/download.html
echo 2. Extract to: C:\ffmpeg
echo 3. Add C:\ffmpeg\bin to System PATH
echo 4. Restart terminal
echo.
echo Option 3: Using Package Managers
echo ----------------------------------------
echo Scoop:  scoop install ffmpeg
echo.
echo ========================================
echo After Installation:
echo ========================================
echo 1. Close this terminal
echo 2. Open a NEW terminal
echo 3. Run this script again to verify
echo 4. Or run: ffmpeg -version
echo.

:end
echo ========================================
pause
