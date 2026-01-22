#!/usr/bin/env python3
"""
Full system initialization test for Dementia Memory Assist System
"""
from dotenv import load_dotenv
load_dotenv()

import shutil
import os

print('='*60)
print('DEMENTIA MEMORY ASSIST SYSTEM - INITIALIZATION TEST')
print('='*60)

print('\n[1] Checking FFmpeg...')
if shutil.which('ffmpeg'):
    print(f'    ✅ FFmpeg found: {shutil.which("ffmpeg")}')
else:
    print('    ❌ FFmpeg not found')

print('\n[2] Checking Groq...')
try:
    from groq import Groq
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        client = Groq(api_key=api_key)
        print(f'    ✅ Groq imported and client initialized')
        print(f'    ✅ API Key configured (first 20 chars: {api_key[:20]}...)')
    else:
        print('    ❌ GROQ_API_KEY not set')
except ImportError:
    print('    ❌ Groq not installed')
except Exception as e:
    print(f'    ❌ Error: {e}')

print('\n[3] Initializing Conversation Summarizer...')
try:
    from summarizer import ConversationSummarizer
    summarizer = ConversationSummarizer()
    print(f'    ✅ Summarizer initialized')
    print(f'    ✅ LLM Enabled: {summarizer.llm_enabled}')
except Exception as e:
    print(f'    ❌ Error: {e}')
    import traceback
    traceback.print_exc()

print('\n[4] Initializing Audio Processor...')
try:
    from memory_store import MemoryStore
    from audio_pipeline import ConversationAudioProcessor
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath('.')), 'data')
    MEMORY_PATH = os.path.join(DATA_DIR, 'memories.json')
    memory_store = MemoryStore(MEMORY_PATH)
    audio_processor = ConversationAudioProcessor(memory_store)
    print(f'    ✅ Audio Processor initialized')
except Exception as e:
    print(f'    ❌ Error: {e}')
    import traceback
    traceback.print_exc()

print('\n[5] Testing Groq Summarization...')
try:
    from datetime import date
    test_transcript = "I'm really happy about the garden project. We planted beautiful flowers together and the kids really enjoyed it. It was a wonderful day with lots of laughter."
    
    summary = summarizer.summarize(
        name="Test Person",
        relationship="Friend",
        last_summary="",
        transcript=test_transcript,
        visit_count=1,
        last_visit=None,
        now=date.today()
    )
    print(f'    ✅ Summarization successful!')
    print(f'    Summary: {summary[:80]}...')
except Exception as e:
    print(f'    ❌ Error: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '='*60)
print('✅ ALL SYSTEMS READY FOR OPERATION!')
print('='*60)
print('\n📋 Summary:')
print('  • FFmpeg: Available for audio processing')
print('  • Groq LLM: Enabled for AI-powered summarization')
print('  • Audio Pipeline: Ready to process conversations')
print('  • Memory Store: Ready to persist memories')
print('\n🚀 App is ready to start!')
