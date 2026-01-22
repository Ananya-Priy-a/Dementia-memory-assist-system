#!/usr/bin/env python
"""
Complete verification script for the Dementia Memory Assist System.
Tests all modules and confirms pydub/FFmpeg refactoring is complete.
"""

import sys
import os
import shutil
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"[PASS] {text}")

def print_warning(text):
    print(f"[WARN] {text}")

def print_error(text):
    print(f"[FAIL] {text}")

def print_info(text):
    print(f"[INFO] {text}")

def test_imports():
    """Test that all critical modules import successfully"""
    print_header("Testing Module Imports")
    
    modules = {
        "memory_store": "Memory database",
        "audio_pipeline": "Audio processing (pydub refactored)",
        "session_manager": "Session-based transcription",
        "summarizer": "Conversation summarizer",
        "app": "Flask application",
    }
    
    all_pass = True
    for module_name, description in modules.items():
        try:
            __import__(module_name)
            print_success(f"{module_name:20} - {description}")
        except ImportError as e:
            print_error(f"{module_name:20} - {str(e)}")
            all_pass = False
    
    return all_pass

def check_ffmpeg():
    """Check if FFmpeg is installed and available"""
    print_header("Checking FFmpeg Installation")
    
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print_success(f"FFmpeg found at: {ffmpeg_path}")
        
        # Try to get version
        import subprocess
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_line = result.stdout.split('\n')[0]
            print_success(f"Version: {version_line}")
            return True
        except Exception as e:
            print_warning(f"Could not get FFmpeg version: {e}")
            return False
    else:
        print_warning("FFmpeg not found in PATH")
        print_info("To install FFmpeg on Windows with Chocolatey:")
        print_info("  choco install ffmpeg -y")
        print_info("Or visit: https://ffmpeg.org/download.html")
        return False

def check_pydub():
    """Verify pydub is no longer imported by audio_pipeline"""
    print_header("Verifying pydub Removal")
    
    try:
        import audio_pipeline
        
        # Check if pydub is in the module's attributes
        has_pydub = hasattr(audio_pipeline, 'AudioSegment')
        if has_pydub:
            print_warning("AudioSegment from pydub still found in audio_pipeline")
            return False
        else:
            print_success("pydub completely removed from audio_pipeline")
            return True
    except Exception as e:
        print_error(f"Could not check audio_pipeline: {e}")
        return False

def check_groq_config():
    """Verify Groq API configuration"""
    print_header("Checking Groq API Configuration")
    
    # Check for .env file
    env_path = Path(".env")
    if env_path.exists():
        print_success(".env file found")
        
        # Check if GROQ_API_KEY is set
        with open(env_path, 'r') as f:
            content = f.read()
            if 'GROQ_API_KEY' in content:
                # Get the key (masked for security)
                for line in content.split('\n'):
                    if 'GROQ_API_KEY' in line:
                        key_part = line.split('=')[1] if '=' in line else ''
                        masked = key_part[:8] + '...' + key_part[-4:] if len(key_part) > 12 else '***'
                        print_success(f"GROQ_API_KEY configured: {masked}")
                return True
            else:
                print_warning("GROQ_API_KEY not found in .env")
                return False
    else:
        print_warning(".env file not found")
        return False

def check_session_manager():
    """Test SessionManager functionality"""
    print_header("Testing SessionManager")
    
    try:
        from session_manager import SessionManager
        
        manager = SessionManager()
        print_success("SessionManager initialized")
        
        # Test creating a session
        session = manager.start_session("test_person")
        print_success(f"Session created: {session.session_id}")
        
        # Test adding chunks
        session.add_chunk("Hello world")
        session.add_chunk(" This is a test")
        print_success("Transcript chunks added successfully")
        
        # Test getting status
        status = session.get_status()
        print_success(f"Session status: {status['chunk_count']} chunks")
        
        # Test ending session
        full_transcript, ended_session = manager.end_session("test_person")
        expected = "Hello world This is a test"
        if full_transcript == expected:
            print_success(f"Session ended: transcript verified")
            return True
        else:
            print_error(f"Transcript mismatch. Got: {full_transcript}")
            return False
    except Exception as e:
        print_error(f"SessionManager test failed: {e}")
        return False

def check_audio_pipeline():
    """Test audio pipeline initialization"""
    print_header("Testing Audio Pipeline")
    
    try:
        from audio_pipeline import ConversationAudioProcessor, FFMPEG_AVAILABLE
        from memory_store import MemoryStore
        
        memory_store = MemoryStore("data/memories.json")
        processor = ConversationAudioProcessor(memory_store)
        print_success("ConversationAudioProcessor initialized")
        
        if FFMPEG_AVAILABLE:
            print_success("FFmpeg support: ENABLED")
        else:
            print_warning("FFmpeg support: DISABLED (will use Whisper fallback)")
        
        # Test session methods exist
        methods = ['start_session', 'add_audio_chunk', 'end_session_and_summarize']
        for method in methods:
            if hasattr(processor, method):
                print_success(f"Session method available: {method}")
            else:
                print_error(f"Session method missing: {method}")
                return False
        
        return True
    except Exception as e:
        print_error(f"Audio pipeline test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print_header("Dementia Memory Assist System - Complete Verification")
    
    results = []
    
    # Run all tests
    results.append(("Module Imports", test_imports()))
    results.append(("FFmpeg Installation", check_ffmpeg()))
    results.append(("pydub Removal", check_pydub()))
    results.append(("Groq Configuration", check_groq_config()))
    results.append(("SessionManager", check_session_manager()))
    results.append(("Audio Pipeline", check_audio_pipeline()))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "[✓]" if result else "[✗]"
        print(f"{symbol} {test_name:30} {status}")
    
    print(f"\n{'='*60}")
    print(f"Overall: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print_success("ALL TESTS PASSED! System is ready for use.")
        print_info("To start the app: python app.py")
        print_info("Then visit: http://127.0.0.1:8080")
        return 0
    else:
        print_warning(f"{total - passed} test(s) failed. See details above.")
        if not check_ffmpeg():
            print_info("\n💡 HINT: FFmpeg is optional but recommended for better audio performance.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
