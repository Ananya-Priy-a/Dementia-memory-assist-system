# FFmpeg Installation Script for Windows
# This script will install FFmpeg using Chocolatey (recommended) or direct download

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FFmpeg Installation for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if FFmpeg is already installed
$ffmpegCheck = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpegCheck) {
    Write-Host "✅ FFmpeg is already installed at: $($ffmpegCheck.Source)" -ForegroundColor Green
    ffmpeg -version | Select-Object -First 1
    exit 0
}

Write-Host "FFmpeg not found. Attempting installation..." -ForegroundColor Yellow
Write-Host ""

# Method 1: Check if Chocolatey is available
$chocoCheck = Get-Command choco -ErrorAction SilentlyContinue
if ($chocoCheck) {
    Write-Host "📦 Chocolatey found. Installing FFmpeg..." -ForegroundColor Cyan
    choco install ffmpeg -y
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Verify installation
    $ffmpegCheck = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpegCheck) {
        Write-Host "✅ FFmpeg installed successfully!" -ForegroundColor Green
        ffmpeg -version | Select-Object -First 1
        exit 0
    }
}

# Method 2: Install via Windows Package Manager (if available)
$wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
if ($wingetCheck) {
    Write-Host "📦 Windows Package Manager found. Installing FFmpeg..." -ForegroundColor Cyan
    winget install --id Gyan.FFmpeg --source winget
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Verify installation
    $ffmpegCheck = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpegCheck) {
        Write-Host "✅ FFmpeg installed successfully!" -ForegroundColor Green
        ffmpeg -version | Select-Object -First 1
        exit 0
    }
}

# Method 3: Manual download instructions
Write-Host "❌ Could not find package manager (Chocolatey or Windows Package Manager)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Manual Installation Options:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Install Chocolatey (Recommended)" -ForegroundColor Yellow
Write-Host "1. Open PowerShell as Administrator" -ForegroundColor White
Write-Host "2. Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
Write-Host "3. Run: iex ((New-Object System.Net.ServicePointManager).SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" -ForegroundColor White
Write-Host "4. Run: choco install ffmpeg -y" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Direct Download" -ForegroundColor Yellow
Write-Host "1. Visit: https://ffmpeg.org/download.html" -ForegroundColor White
Write-Host "2. Download FFmpeg for Windows" -ForegroundColor White
Write-Host "3. Extract to a folder (e.g., C:\ffmpeg)" -ForegroundColor White
Write-Host "4. Add to PATH environment variable" -ForegroundColor White
Write-Host ""
Write-Host "Option 3: Automatic Download (requires .NET)" -ForegroundColor Yellow
Write-Host "Run: python -m pip install ffmpeg-python" -ForegroundColor White
Write-Host ""
