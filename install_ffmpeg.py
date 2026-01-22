#!/usr/bin/env python
"""
FFmpeg Installation Helper for Dementia Memory Assist System
Checks for FFmpeg and provides installation guidance
"""

import subprocess
import os
import sys
import platform

# Fix for Windows console encoding issues
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def get_ffmpeg_version():
    """Get FFmpeg version if installed"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split('\n')[0]
            return first_line
    except:
        pass
    return None

def print_windows_instructions():
    """Print Windows installation instructions"""
    print("\n" + "=" * 60)
    print("Windows Installation Instructions")
    print("=" * 60)
    print()
    print("Option 1: Using Chocolatey (RECOMMENDED)")
    print("-" * 60)
    print("1. Open PowerShell as Administrator")
    print("2. Run: choco install ffmpeg")
    print("3. Restart your terminal")
    print()
    print("Option 2: Manual Installation")
    print("-" * 60)
    print("1. Download FFmpeg from: https://ffmpeg.org/download.html")
    print("   Recommended: Full build from gyan.dev")
    print("2. Extract to: C:\\ffmpeg")
    print("3. Add C:\\ffmpeg\\bin to System PATH:")
    print("   - Press Win+X → System")
    print("   - Advanced system settings → Environment Variables")
    print("   - Add C:\\ffmpeg\\bin to Path")
    print("4. Restart terminal and verify: ffmpeg -version")
    print()
    print("Option 3: Using Windows Package Managers")
    print("-" * 60)
    print("Scoop:  scoop install ffmpeg")
    print("Winget: winget install ffmpeg")
    print()

def print_mac_instructions():
    """Print macOS installation instructions"""
    print("\n" + "=" * 60)
    print("macOS Installation Instructions")
    print("=" * 60)
    print()
    print("Using Homebrew (RECOMMENDED):")
    print("-" * 60)
    print("1. brew install ffmpeg")
    print("2. Verify: ffmpeg -version")
    print()
    print("Alternative:")
    print("3. Download from: https://ffmpeg.org/download.html")
    print()

def print_linux_instructions():
    """Print Linux installation instructions"""
    print("\n" + "=" * 60)
    print("Linux Installation Instructions")
    print("=" * 60)
    print()
    print("Ubuntu/Debian:")
    print("-" * 60)
    print("sudo apt-get update")
    print("sudo apt-get install ffmpeg")
    print()
    print("Fedora/RHEL:")
    print("-" * 60)
    print("sudo dnf install ffmpeg")
    print()
    print("Arch Linux:")
    print("-" * 60)
    print("sudo pacman -S ffmpeg")
    print()

def print_verification_test():
    """Print how to verify installation"""
    print("\n" + "=" * 60)
    print("Verify Installation")
    print("=" * 60)
    print()
    print("After installation, run:")
    print("  ffmpeg -version")
    print()
    print("Or use our verification script:")
    print("  python verify_installation.py")
    print()
    print("Look for: ✅ FFmpeg installed (audio conversion available)")
    print()

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("FFmpeg Installation Checker")
    print("Dementia Memory Assist System")
    print("=" * 60)
    print()
    
    # Check current status
    if check_ffmpeg():
        version = get_ffmpeg_version()
        print("✅ FFmpeg is installed and accessible!")
        print()
        if version:
            print(f"Version: {version}")
        print()
        print("Your app can now use advanced audio features:")
        print("  ✓ MP3 → WAV conversion")
        print("  ✓ WebM → WAV conversion")
        print("  ✓ M4A → WAV conversion")
        print("  ✓ All standard audio formats")
        return 0
    
    print("❌ FFmpeg is NOT currently installed")
    print()
    print("FFmpeg is needed for audio file format conversion.")
    print("Without it, your app can only use WAV files directly.")
    print()
    
    # Provide OS-specific instructions
    system = platform.system()
    
    if system == "Windows":
        print_windows_instructions()
    elif system == "Darwin":
        print_mac_instructions()
    elif system == "Linux":
        print_linux_instructions()
    else:
        print("Operating System: Unknown")
        print("Visit: https://ffmpeg.org/download.html for instructions")
        print()
    
    print_verification_test()
    
    print("=" * 60)
    print("Need Help?")
    print("=" * 60)
    print("See: FFMPEG_SETUP.md for detailed instructions")
    print("Or visit: https://ffmpeg.org/documentation.html")
    print()
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
