#!/usr/bin/env python3
"""Check available Groq models"""
from dotenv import load_dotenv
import os

load_dotenv()

from groq import Groq

api_key = os.getenv('GROQ_API_KEY')
print(f'API Key present: {bool(api_key)}')

try:
    client = Groq(api_key=api_key)
    print("✅ Groq client initialized successfully!")
    
    # Try to list models
    try:
        models = client.models.list()
        print("\n📋 Available Models:")
        for model in models.data:
            print(f"  - {model.id}")
    except Exception as e:
        print(f"\n⚠️ Could not list models: {e}")
        print("\nTrying common models...")
        
        test_models = [
            "llama-3.1-70b-versatile",
            "llama-3.2-90b-text-preview", 
            "mixtral-8x7b-32768",
            "gemma-7b-it",
            "gemma2-9b-it",
            "llama2-70b-4096",
            "whisper-large-v3-turbo"
        ]
        
        for model in test_models:
            try:
                message = client.chat.completions.create(
                    messages=[{"role": "user", "content": "test"}],
                    model=model,
                    max_tokens=1,
                )
                print(f"  ✅ {model}")
            except Exception as e:
                error_type = type(e).__name__
                print(f"  ❌ {model} ({error_type})")
                
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
