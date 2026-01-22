# FFmpeg Installation Guide

FFmpeg is required for audio processing in the Dementia Memory Assist System. Without it, audio file format conversion will be limited.

## What is FFmpeg?

FFmpeg is a free, open-source multimedia framework that handles audio, video, and image processing. Our app uses it to convert audio files to formats that Whisper (speech-to-text) can process.

---

## ✅ Windows Installation (Recommended)

### Option 1: Using Chocolatey (Easiest)

If you have Chocolatey installed:

```powershell
choco install ffmpeg
```

Then restart your terminal and verify:
```powershell
ffmpeg -version
```

---

### Option 2: Manual Installation

#### Step 1: Download FFmpeg
1. Visit: https://ffmpeg.org/download.html
2. Click on **Windows** section
3. Choose a build (recommended: **Full** build from gyan.dev or BtbN)
4. Download the ZIP file

#### Step 2: Extract FFmpeg
1. Extract the downloaded ZIP to a location (e.g., `C:\ffmpeg`)
2. You should have folders like `bin`, `doc`, `presets` inside

#### Step 3: Add to System PATH

##### Via GUI (Recommended):
1. Press `Win + X` and select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables** button
4. Under "System variables", click **New**
5. Variable name: `Path`
6. Variable value: `C:\ffmpeg\bin` (adjust path if different)
7. Click **OK** three times
8. Restart your terminal

##### Via PowerShell (Admin):
```powershell
# Run as Administrator
$ffmpegPath = "C:\ffmpeg\bin"
$env:Path += ";$ffmpegPath"
[Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::User)
```

#### Step 4: Verify Installation
Close and reopen PowerShell, then run:
```powershell
ffmpeg -version
```

You should see version information if installed correctly.

---

## ✅ macOS Installation

### Using Homebrew:
```bash
brew install ffmpeg
```

### Verify:
```bash
ffmpeg -version
```

---

## ✅ Linux Installation

### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Fedora/RHEL:
```bash
sudo dnf install ffmpeg
```

### Arch:
```bash
sudo pacman -S ffmpeg
```

### Verify:
```bash
ffmpeg -version
```

---

## 🧪 Quick Test

After installation, test with the app:

```powershell
cd 'c:\Users\ABHIRAJ ARYA\Desktop\SO IMP\New folder (2)\Dementia-memory-assist-system'
& "C:/Users/ABHIRAJ ARYA/Desktop/SO IMP/New folder (2)/.venv/Scripts/python.exe" verify_installation.py
```

Look for: `✅ FFmpeg installed (audio conversion available)`

---

## ❓ Troubleshooting

### "ffmpeg is not recognized as an internal or external command"
**Solution**: 
- FFmpeg not in PATH
- Restart your terminal after adding to PATH
- Verify path exists: `dir C:\ffmpeg\bin` (adjust path)

### "Cannot open shared object file: No such file or directory"
**Solution** (Linux):
- Install missing libraries
```bash
sudo apt-get install libavcodec-extra libavformat-dev libavutil-dev
```

### App still says "FFmpeg is not installed"
**Solution**:
- Restart the application completely
- Check PATH is correct: `echo $env:Path` (PowerShell)
- Verify: `which ffmpeg` (macOS/Linux) or `where ffmpeg` (Windows)

---

## 📋 What FFmpeg Enables

✅ **With FFmpeg**:
- Convert MP3 → WAV
- Convert WebM → WAV
- Convert M4A → WAV
- Process any audio format

❌ **Without FFmpeg**:
- Can only use WAV files directly
- Audio conversion will fail
- Whisper will still work if file is already in compatible format

---

## 📊 Current Status

Run this to check if FFmpeg is properly installed:

```powershell
& "C:/Users/ABHIRAJ ARYA/Desktop/SO IMP/New folder (2)/.venv/Scripts/python.exe" -c "import shutil; print('FFmpeg found!' if shutil.which('ffmpeg') else 'FFmpeg not found')"
```

---

## 🔗 Resources

- **FFmpeg Official**: https://ffmpeg.org/download.html
- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html
- **Chocolatey**: https://chocolatey.org/packages/ffmpeg
- **gyan.dev builds**: https://www.gyan.dev/ffmpeg/builds/

---

**Last Updated**: January 21, 2026
