# FFmpeg Setup for Non-Admin Users
# This script sets up FFmpeg without requiring administrator privileges

Write-Host @"
============================================================
     FFmpeg Setup for Dementia Memory Assist System
============================================================

This script will help you set up FFmpeg without admin rights.
"@

# Check if FFmpeg already exists
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    Write-Host "✓ FFmpeg is already installed at: $($ffmpeg.Source)" -ForegroundColor Green
    & ffmpeg -version | Select-Object -First 1
    exit 0
}

Write-Host ""
Write-Host "FFmpeg not found in PATH. Here are your options:" -ForegroundColor Yellow
Write-Host ""

# Option 1: Temporary PATH for current session
Write-Host "OPTION 1: Add FFmpeg to PATH temporarily (this session only)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host @"
If you have FFmpeg already downloaded/installed somewhere, run:

`$env:Path += ';C:\path\to\ffmpeg\bin'

Then test it:
ffmpeg -version

Then you can use the app normally for this session.
"@
Write-Host ""

# Option 2: Download portable FFmpeg
Write-Host "OPTION 2: Download portable FFmpeg (Recommended)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host @"
Method A - Using Windows Package Manager (easiest):
   - Requires Windows 10/11 with App Installer
   - Run in PowerShell:
     winget install --id Gyan.FFmpeg --source winget
   - Then restart PowerShell

Method B - Manual download:
   1. Download from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z
   2. Extract to: C:\ffmpeg
   3. Add to PATH (see Option 3 below)
   4. Restart PowerShell
   5. Verify: ffmpeg -version

Method C - Using Python package:
   python -m pip install ffmpeg-python
"@
Write-Host ""

# Option 3: Permanent PATH setup (no admin needed)
Write-Host "OPTION 3: Add FFmpeg to permanent PATH (User Variables)" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host @"
This method sets PATH for your user account permanently (no admin needed):

Method A - Via GUI (easiest):
   1. Press WIN+R
   2. Type: rundll32 sysdm.cpl,EditEnvironmentVariables
   3. Under "User variables for [YourName]"
   4. Click "New..." button
   5. Variable name: Path
   6. Variable value: C:\path\to\ffmpeg\bin
   7. Click OK, OK, OK
   8. Restart PowerShell

Method B - Via PowerShell (no admin):
   [Environment]::SetEnvironmentVariable(
       'Path',
       [Environment]::GetEnvironmentVariable('Path','User') + ';C:\ffmpeg\bin',
       'User'
   )
   
   Then restart PowerShell and verify:
   ffmpeg -version
"@
Write-Host ""

# Option 4: Check existing installations
Write-Host "OPTION 4: Check if FFmpeg is already installed somewhere" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host @"
Run these commands to find existing FFmpeg:

# Check common locations
Test-Path "C:\Program Files\ffmpeg\bin\ffmpeg.exe"
Test-Path "C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe"
Test-Path "$env:USERPROFILE\ffmpeg\bin\ffmpeg.exe"
Test-Path "$env:USERPROFILE\Downloads\ffmpeg\bin\ffmpeg.exe"

If you find it, use Option 3 to add its location to PATH.
"@
Write-Host ""

Write-Host "For detailed help, see: PYDUB_FFMPEG_RESOLUTION.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "TIP: The app works WITHOUT FFmpeg, but performs better WITH it!" -ForegroundColor Yellow
Write-Host ""
