#!/usr/bin/env python
"""
Verification script for Dementia Memory Assist System
Checks all dependencies and components are working correctly
"""

import sys
import subprocess
import io

# Fix for Windows console encoding issues
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

def check_python_version():
    """Verify Python 3.10+ is installed"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python Version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python Version: {version.major}.{version.minor}.{version.micro} (Need 3.10+)")
        return False

def check_imports():
    """Verify all required modules can be imported"""
    modules = {
        'flask': 'Flask web framework',
        'flask_cors': 'CORS support',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'PIL': 'Pillow',
        'torch': 'PyTorch',
        'whisper': 'OpenAI Whisper',
        'groq': 'Groq API',
        'sqlalchemy': 'SQLAlchemy',
        'dotenv': 'python-dotenv',
    }
    
    all_ok = True
    for module_name, description in modules.items():
        try:
            __import__(module_name)
            print(f"✅ {description}: {module_name}")
        except ImportError as e:
            print(f"❌ {description}: {module_name} - {e}")
            all_ok = False
    
    return all_ok

def check_app_modules():
    """Verify app-specific modules"""
    app_modules = [
        'app',
        'audio_pipeline',
        'face_module',
        'memory_store',
        'summarizer',
    ]
    
    print("\n--- Checking App Modules ---")
    all_ok = True
    for mod in app_modules:
        try:
            __import__(mod)
            print(f"✅ {mod}.py")
        except Exception as e:
            print(f"❌ {mod}.py - {e}")
            all_ok = False
    
    return all_ok

def check_data_files():
    """Verify data files exist"""
    import os
    
    print("\n--- Checking Data Files ---")
    files_to_check = [
        ('data/memories.json', 'Memory storage'),
        ('data/known_faces', 'Known faces directory'),
        ('.env', 'Configuration file'),
        ('requirements.txt', 'Dependencies list'),
    ]
    
    all_ok = True
    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            print(f"✅ {description}: {filepath}")
        else:
            print(f"⚠️  {description}: {filepath} (not found)")
    
    return all_ok

def check_ffmpeg():
    """Check if FFmpeg is available"""
    print("\n--- Optional Dependencies ---")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg installed (audio conversion available)")
            return True
        else:
            print("⚠️  FFmpeg not available (audio conversion limited)")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  FFmpeg not installed (optional, but recommended)")
        return False

def check_groq_key():
    """Check if Groq API key is configured"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        print(f"✅ Groq API Key configured")
        return True
    else:
        print("⚠️  Groq API Key not set (LLM features disabled)")
        return False

def main():
    """Run all checks"""
    print("=" * 50)
    print("Dementia Memory Assist System - Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Imports", check_imports),
        ("App Modules", check_app_modules),
        ("Data Files", check_data_files),
        ("FFmpeg", check_ffmpeg),
        ("Groq Config", check_groq_key),
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error during check: {e}")
            results[name] = False
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    critical = all([
        results.get("Python Version", False),
        results.get("Required Imports", False),
        results.get("App Modules", False),
    ])
    
    if critical:
        print("✅ All critical systems operational")
        print("🟢 Application is ready to run!")
    else:
        print("❌ Some critical systems failed")
        print("🔴 Fix errors above before running the app")
    
    print("\nOptional:")
    if results.get("FFmpeg", False):
        print("  ✅ Audio file conversion available")
    else:
        print("  ⚠️  Install FFmpeg for full audio support")
    
    if results.get("Groq Config", False):
        print("  ✅ AI-powered summaries enabled")
    else:
        print("  ⚠️  Get Groq API key for AI summaries")
    
    return 0 if critical else 1

if __name__ == "__main__":
    sys.exit(main())
