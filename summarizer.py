from datetime import date
from typing import Optional
import os

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class ConversationSummarizer:
    """
    LLM-powered summarizer using Groq API (free tier).
    
    Generates 2-3 line emotional and important summaries
    focusing on the key aspects of the conversation.
    Falls back to simple text extraction if LLM fails.
    """

    def __init__(self):
        self.groq_client = None
        self.llm_enabled = False
        
        if GROQ_AVAILABLE:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self.groq_client = Groq(api_key=api_key)
                self.llm_enabled = True
                print("[Summarizer] Groq LLM enabled")
            else:
                print("[Summarizer] GROQ_API_KEY not found. Set it to enable LLM. Using fallback method.")
        else:
            print("[Summarizer] Groq not installed. Using fallback summarization method.")

    def summarize(
        self,
        name: str,
        relationship: str,
        last_summary: str,
        transcript: str,
        visit_count: int,
        last_visit: Optional[str],
        now: date,
    ) -> str:
        transcript = (transcript or "").strip()

        # If there's very little speech, keep the previous memory.
        if len(transcript.split()) < 6 and last_summary:
            return last_summary

        # Try LLM-based summarization first
        if self.llm_enabled:
            try:
                return self._summarize_with_llm(
                    name, relationship, transcript, last_visit
                )
            except Exception as e:
                print(f"[Summarizer] LLM error: {e}. Falling back to simple method.")
        
        # Fallback to simple extraction
        return self._simple_summarize(transcript)

    def _summarize_with_llm(self, name: str, relationship: str, transcript: str, last_visit: Optional[str]) -> str:
        """
        Use Groq LLM to generate an emotional, important summary.
        """
        rel_info = f" ({relationship})" if relationship else ""
        time_info = f" They last visited on {last_visit}." if last_visit else ""
        
        prompt = f"""You are helping create a brief memory for someone with memory loss about a conversation.

Person: {name}{rel_info}{time_info}

Conversation transcript:
{transcript}

Create a 2-3 line memory summary focusing on:
1. The emotional tone and feelings expressed
2. The most important topics discussed
3. Any meaningful moments or connections

Keep it warm, personal, and concise. Maximum 3 lines."""

        message = self.groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="mixtral-8x7b-32768",  # Free Groq model with high rate limits
        )
        
        summary = message.choices[0].message.content.strip()
        return summary

    def _simple_summarize(self, transcript: str) -> str:
        """
        Simple fallback summarization - extract key content.
        """
        words = transcript.split()
        
        if words:
            # Get the most recent 25 words (emotional/important parts usually at end)
            focus = " ".join(words[-25:])
            # Clean up and ensure proper punctuation
            summary = focus.strip().rstrip(".")
            if summary and not summary.endswith("."):
                summary += "."
        else:
            summary = "You shared a warm moment together."

        return summary

