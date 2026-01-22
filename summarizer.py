from datetime import date
from typing import Optional
import os
import ssl

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
                try:
                    # Initialize Groq client with API key
                    self.groq_client = Groq(api_key=api_key)
                    self.llm_enabled = True
                    print("[Summarizer] Groq LLM enabled")
                except Exception as e:
                    print(f"[Summarizer] Failed to initialize Groq: {e}. Using fallback method.")
                    self.llm_enabled = False
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
            print(f"[Summarizer] Transcript too short ({len(transcript.split())} words) and last_summary exists, keeping previous summary")
            return last_summary

        print(f"[Summarizer] Summarizing conversation for {name} (visit {visit_count + 1})")
        print(f"[Summarizer] Transcript length: {len(transcript.split())} words, Has previous summary: {bool(last_summary)}")

        # Try LLM-based summarization first
        if self.llm_enabled:
            try:
                print(f"[Summarizer] Using LLM for summarization")
                result = self._summarize_with_llm(
                    name, relationship, transcript, last_visit
                )
                print(f"[Summarizer] LLM summary generated successfully: {result[:80]}...")
                return result
            except Exception as e:
                print(f"[Summarizer] LLM error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                print(f"[Summarizer] Falling back to simple method.")
        else:
            print(f"[Summarizer] LLM not enabled (self.llm_enabled={self.llm_enabled}), using fallback method")
        
        # Fallback to simple extraction
        print(f"[Summarizer] Creating fallback summary...")
        return self._simple_summarize(transcript)

    def _summarize_with_llm(self, name: str, relationship: str, transcript: str, last_visit: Optional[str]) -> str:
        """
        Use Groq LLM to generate an emotional, important summary.
        Automatically handles model selection and deprecation.
        """
        rel_info = f" ({relationship})" if relationship else ""
        time_info = f" They last visited on {last_visit}." if last_visit else ""
        
        prompt = f"""You are creating a SHORT memory for someone with memory loss about a meaningful conversation.

Person: {name}{rel_info}{time_info}

Conversation transcript:
{transcript}

CRITICAL RULES:
✓ MUST be 3-4 lines MAXIMUM
✓ MUST contain important words from the conversation
✓ MUST capture WHY this matters, not WHAT was literally said
✓ MUST be in YOUR OWN WORDS, not copying from transcript
✓ NEVER include verbatim phrases or sentences from above

FORBIDDEN:
✗ Do NOT copy any sentence or phrase directly from the transcript
✗ Do NOT just repeat what was said word-for-word
✗ Do NOT include speaker names or quotes
✗ Do NOT exceed 4 lines

WHAT TO INCLUDE:
- Main topic/theme (use your words)
- Why it mattered (emotions, decisions, concerns)
- Actions or outcomes mentioned
- The feeling or tone of interaction

EXAMPLES:

BAD (verbatim copying): "He said he was going to the doctor tomorrow and was worried about the test results."
GOOD (abstract, meaningful): "Planning to address health concerns with upcoming medical visit—showed caring and focus on wellness."

BAD (too long/detailed): "They discussed the kids, the weather, and plans for next week. It was a nice conversation about many things."
GOOD (concise, meaningful): "Caught up on family updates and upcoming plans together—warm and connected."

BAD (missing meaning): "Talked about the presentation."
GOOD (captures meaning): "Discussed important work presentation with encouragement and support offered."

Now create a 3-4 line summary with important keywords that captures the essence and meaning:"""

        try:
            # Try to get available models, fallback to common models
            available_models = [
                "llama-3.3-70b-versatile",  # Most capable, latest
                "llama-3.1-8b-instant",     # Fast, lightweight
                "whisper-large-v3",         # For audio transcription
                "whisper-large-v3-turbo",   # Fast audio transcription
            ]
            
            # Try each model in order
            for model in available_models:
                try:
                    message = self.groq_client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        model=model,
                    )
                    print(f"[Summarizer] Using model: {model}")
                    summary = message.choices[0].message.content.strip()
                    break
                except Exception as model_error:
                    if "decommissioned" in str(model_error) or "not found" in str(model_error) or "does not exist" in str(model_error):
                        print(f"[Summarizer] Model {model} not available, trying next...")
                        continue
                    else:
                        # Some other error, raise it
                        raise
            else:
                # No models available
                raise Exception("No available Groq models found. Please check your API key and account.")
        
        except Exception as e:
            print(f"[Summarizer] LLM error: {type(e).__name__}: {e}")
            raise
        
        # Post-check: validate that summary is not just truncation
        if self._is_truncation_or_verbatim(summary, transcript):
            print(f"[Summarizer] LLM output appears to be truncation/verbatim. Using fallback instead.")
            return self._simple_summarize(transcript)
        
        # Check line count - enforce 3-4 lines maximum
        lines = [l.strip() for l in summary.split('\n') if l.strip()]
        if len(lines) > 4:
            print(f"[Summarizer] Summary exceeds 4 lines ({len(lines)} lines). Truncating...")
            summary = '\n'.join(lines[:4])
        
        return summary
        
        return summary

    def _is_truncation_or_verbatim(self, summary: str, transcript: str) -> bool:
        """
        Check if summary is just truncation or verbatim copying from transcript.
        Returns True if summary appears to be a bad summary (truncation/verbatim).
        
        Uses multiple detection methods:
        1. Truncation indicators (ellipsis)
        2. Consecutive word matching (70%+ means verbatim)
        3. Substring matching (looks for long extracted phrases)
        """
        # Check for truncation indicators
        if "..." in summary or summary.endswith("…"):
            print(f"[Summarizer] Detected truncation (ellipsis) in summary")
            return True
        
        # Check if more than 60% of summary appears as consecutive substring in transcript
        # This catches direct extraction
        summary_lower = summary.lower()
        transcript_lower = transcript.lower()
        
        # Try to find the summary as a substring (with some fuzzing for punctuation)
        if len(summary) > 20:
            # For longer summaries, check if they appear directly
            if summary_lower in transcript_lower:
                print(f"[Summarizer] Summary is direct substring of transcript")
                return True
        
        # Split summary into words and check consecutive matching
        summary_words = summary.lower().split()
        
        if len(summary_words) < 3:
            return False  # Too short to judge, allow it
        
        # Find consecutive word runs in transcript
        max_consecutive = 0
        current_consecutive = 0
        search_pos = 0
        
        for i, word in enumerate(summary_words):
            pos = transcript_lower.find(word, search_pos)
            if pos != -1:
                current_consecutive += 1
                search_pos = pos + len(word)
            else:
                if current_consecutive > max_consecutive:
                    max_consecutive = current_consecutive
                current_consecutive = 0
                search_pos = 0
        
        if current_consecutive > max_consecutive:
            max_consecutive = current_consecutive
        
        # If 5+ consecutive words appear in transcript, likely verbatim
        if max_consecutive >= 5:
            print(f"[Summarizer] Found {max_consecutive} consecutive words from transcript in summary—likely verbatim")
            return True
        
        # Check verbatim ratio (percentage of summary words in transcript consecutively)
        consecutive_count = 0
        search_pos = 0
        for word in summary_words:
            pos = transcript_lower.find(word, search_pos)
            if pos != -1:
                consecutive_count += 1
                search_pos = pos + len(word)
            else:
                search_pos = 0
        
        verbatim_ratio = consecutive_count / len(summary_words)
        if verbatim_ratio > 0.65:
            print(f"[Summarizer] High verbatim ratio {verbatim_ratio:.1%} ({consecutive_count}/{len(summary_words)} words)")
            return True
        
        return False

    def _simple_summarize(self, transcript: str) -> str:
        """
        Fallback summarization - creates abstract summary from key concepts.
        Extracts important sentences and rewrites them in abstract form.
        """
        if not transcript or len(transcript.strip()) == 0:
            return "Had a conversation together."
        
        # Split into sentences
        import re
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        if not sentences:
            # Fallback to first 30 words if no sentences
            words = transcript.split()
            summary = " ".join(words[:min(30, len(words))])
            if summary and not summary.endswith(('.', '!', '?')):
                summary += "."
            return summary
        
        # Create a summary by abstracting key concepts
        if len(sentences) <= 2:
            # Short conversation - abstract both sentences
            abstract = self._abstract_sentence(sentences[0])
            if len(sentences) == 2:
                abstract += " " + self._abstract_sentence(sentences[1])
            summary = abstract
        elif len(sentences) == 3:
            # Take first and last, and middle
            first = self._abstract_sentence(sentences[0])
            last = self._abstract_sentence(sentences[-1])
            summary = f"{first} {last}"
        else:
            # Take first, middle, and last sentence - create abstract form
            first = self._abstract_sentence(sentences[0])
            middle_idx = len(sentences) // 2
            middle = self._abstract_sentence(sentences[middle_idx])
            last = self._abstract_sentence(sentences[-1])
            
            # Combine into 3-4 lines with meaning
            summary = f"{first} {middle} {last}"
        
        # Ensure proper ending and format
        if summary and not summary.endswith(('.', '!', '?')):
            summary += "."
        
        # Enforce 3-4 lines max
        lines = summary.split('\n')
        if len(lines) > 4:
            summary = '\n'.join(lines[:4])
        
        print(f"[Summarizer] Fallback summary created from {len(sentences)} sentences")
        return summary
    
    def _abstract_sentence(self, sentence: str) -> str:
        """
        Convert a literal sentence to an abstract meaning-focused form.
        Captures the essence without copying the exact phrasing.
        """
        if not sentence or len(sentence.strip()) < 3:
            return ""
        
        sentence = sentence.strip()
        
        # Simple pattern-based abstraction for common conversation types
        lower = sentence.lower()
        
        # Detect common patterns and abstract them
        if any(word in lower for word in ["told", "said", "mentioned", "shared", "talked about"]):
            if "worried" in lower or "concerned" in lower or "anxious" in lower:
                return "Expressed concerns and worries—showed caring attention to challenges."
            elif "happy" in lower or "excited" in lower or "great" in lower or "wonderful" in lower:
                return "Shared positive news and enthusiasm—connection through joy."
            elif "plan" in lower or "going to" in lower or "will" in lower:
                return "Discussed future plans and upcoming activities."
            else:
                # Extract key nouns/verbs
                import re
                words = re.findall(r'\b[a-z]{4,}\b', lower)
                if words:
                    main_topic = words[0] if len(words) > 0 else "something"
                    return f"Shared thoughts and connected through conversation about {main_topic}."
        
        if any(word in lower for word in ["asking", "asked", "question", "need", "help"]):
            return "Sought advice or assistance—showed trust and openness."
        
        if any(word in lower for word in ["agree", "decided", "planned", "arranged"]):
            return "Made decisions and concrete plans together."
        
        if any(word in lower for word in ["laughed", "joked", "fun", "enjoyed"]):
            return "Shared laughter and lighthearted moments together."
        
        # Default: extract meaning from the sentence
        # Take first 15 words and reframe
        words = sentence.split()[:15]
        main_phrase = " ".join(words)
        
        # Remove common filler words at start
        for filler in ["they said", "he said", "she said", "i said", "he told", "she told"]:
            if main_phrase.lower().startswith(filler):
                main_phrase = main_phrase[len(filler):].strip()
                break
        
        if len(main_phrase) > 50:
            main_phrase = main_phrase[:50].rsplit(' ', 1)[0]
        
        return main_phrase + ("." if not main_phrase.endswith(('.', '!', '?')) else "")


