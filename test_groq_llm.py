#!/usr/bin/env python
"""
Test script to demonstrate Groq LLM integration
Tests the AI summarization capability with sample conversations
"""

import sys
import os

# Fix for Windows console encoding issues
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

from datetime import date
from dotenv import load_dotenv
from summarizer import ConversationSummarizer

def test_groq_summarization():
    """Test Groq LLM with sample conversations"""
    
    print("\n" + "="*70)
    print("Groq LLM Integration Test")
    print("="*70)
    print()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize summarizer
    print("[TEST] Initializing ConversationSummarizer...")
    summarizer = ConversationSummarizer()
    print()
    
    if not summarizer.llm_enabled:
        print("ERROR: Groq LLM is not enabled!")
        print("Please check your GROQ_API_KEY in .env file")
        return False
    
    # Test conversations
    test_cases = [
        {
            "name": "Sarah",
            "relationship": "Daughter",
            "last_summary": "Recently retired and enjoying gardening",
            "transcript": "Hi Mom! I wanted to tell you about the flowers I planted in my garden. I used the yellow tulips you gave me last spring, and they looked beautiful. The kids loved helping me plant them. We also found a robin's nest in the tree. It reminded me of when we used to watch birds together.",
            "visit_count": 5,
            "last_visit": "2026-01-15",
        },
        {
            "name": "James",
            "relationship": "Son",
            "last_summary": "Works in technology, married with two kids",
            "transcript": "Dad, I wanted to thank you for all the advice you gave me about my job. I finally got that promotion I was hoping for! The team is really supportive, and I'm excited about the new projects. Emma and Luke are doing great in school. Luke made the soccer team this year.",
            "visit_count": 3,
            "last_visit": "2026-01-10",
        },
        {
            "name": "Michael",
            "relationship": "Grandson",
            "last_summary": "College student studying engineering",
            "transcript": "Hey Grandpa! I wanted to tell you about my engineering project. We're building a solar panel system for the university. Remember how you always taught me to think practically about solving problems? That's really helping me now. My team thinks the project could save the university a lot of money on energy costs.",
            "visit_count": 2,
            "last_visit": "2026-01-08",
        },
    ]
    
    print("[TEST] Testing AI Summarization with 3 sample conversations")
    print()
    
    for i, test in enumerate(test_cases, 1):
        print("-" * 70)
        print(f"TEST CASE {i}: {test['name']} ({test['relationship']})")
        print("-" * 70)
        print()
        
        print(f"Transcript ({len(test['transcript'].split())} words):")
        print(f"  \"{test['transcript'][:100]}...\"")
        print()
        
        try:
            print("[GENERATING] AI Summary...")
            summary = summarizer.summarize(
                name=test['name'],
                relationship=test['relationship'],
                last_summary=test['last_summary'],
                transcript=test['transcript'],
                visit_count=test['visit_count'],
                last_visit=test['last_visit'],
                now=date.today(),
            )
            
            print()
            print("✅ AI SUMMARY GENERATED:")
            print("-" * 70)
            for line in summary.split('\n'):
                if line.strip():
                    print(f"  {line}")
            print("-" * 70)
            print()
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("="*70)
    print("✅ All tests passed! Groq LLM is working correctly.")
    print("="*70)
    print()
    
    return True

if __name__ == "__main__":
    success = test_groq_summarization()
    sys.exit(0 if success else 1)
