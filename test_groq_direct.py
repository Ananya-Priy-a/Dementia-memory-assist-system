#!/usr/bin/env python3
"""
Direct test of Groq client initialization and basic functionality
"""
from dotenv import load_dotenv
import os

load_dotenv()

from groq import Groq

api_key = os.getenv('GROQ_API_KEY')
print(f'API Key present: {bool(api_key)}')
if api_key:
    print(f'API Key (first 20 chars): {api_key[:20]}...')

print("\n" + "="*60)
print("Testing Groq Client Initialization")
print("="*60)

try:
    print("Creating Groq client...")
    client = Groq(api_key=api_key)
    print("✅ Groq client initialized successfully!")
    
    print("\n" + "="*60)
    print("Testing Basic LLM Call")
    print("="*60)
    
    print("\nSending test message to Groq API...")
    message = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Hello! Summarize this in one sentence: The patient had a good day today. They ate well, took their medications, and had a nice conversation with family.",
            }
        ],
        model="llama-3.3-70b-versatile",
        max_tokens=100,
    )
    
    summary = message.choices[0].message.content
    print(f"\n✅ API Call Successful!")
    print(f"Response: {summary}")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
