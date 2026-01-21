import os
import tempfile
from datetime import datetime
from typing import Tuple, List, Dict
import sys

import whisper
from pydub import AudioSegment

# Don't import pyannote at module level due to import issues
# It will be lazily imported only if needed
DIARIZATION_AVAILABLE = False

from memory_store import MemoryStore
from summarizer import ConversationSummarizer


class ConversationAudioProcessor:
    """
    Handles audio -> text -> speaker diarization -> summary -> memory update.
    Supports multi-speaker conversations with speaker attribution.
    """

    def __init__(self, memory_store: MemoryStore, whisper_model: str = "tiny"):
        self.memory_store = memory_store
        self.model_name = whisper_model
        self._model = whisper.load_model(self.model_name)
        self.summarizer = ConversationSummarizer()
        
        # Initialize speaker diarization pipeline if available
        self.diarization_pipeline = None
        if DIARIZATION_AVAILABLE:
            try:
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.0"
                )
                print("[AudioProcessor] Speaker diarization pipeline loaded")
            except Exception as e:
                print(f"[AudioProcessor] Failed to load diarization pipeline: {e}")

    def process_conversation(self, person_id: str, audio_path: str) -> Tuple[str, str]:
        """
        Returns (transcript, summary)
        Accepts any audio format (webm, mp3, wav) and converts to wav for Whisper.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(audio_path)

        print(f"[AudioProcessor] Processing conversation for person: {person_id}")

        # Convert to WAV if needed (Whisper works best with WAV)
        wav_path = audio_path
        if not audio_path.lower().endswith('.wav'):
            print(f"[AudioProcessor] Converting {audio_path} to WAV...")
            try:
                # Try to convert using pydub (requires ffmpeg)
                audio = AudioSegment.from_file(audio_path)
                # Export as WAV
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    wav_path = tmp.name
                    audio.export(wav_path, format="wav")
                    print(f"[AudioProcessor] Converted to {wav_path}")
            except Exception as e:
                print(f"[AudioProcessor] Conversion failed (ffmpeg may not be installed): {e}")
                print(f"[AudioProcessor] Trying Whisper with original file (may work for some formats)...")
                # Fallback: try direct (Whisper might handle webm/mp3 directly in some cases)
                wav_path = audio_path

        print(f"[AudioProcessor] Transcribing {wav_path}...")
        result = self._model.transcribe(wav_path, language="en")
        transcript = (result.get("text") or "").strip()
        print(f"[AudioProcessor] Transcript: {transcript[:100]}...")

        person = self.memory_store.get_person(person_id)
        last_summary = person.get("last_summary", "")
        person_name = person.get("name", person_id)
        person_relationship = person.get("relationship", "")
        
        print(f"[AudioProcessor] Person info - Name: {person_name}, Relationship: {person_relationship}, Last Summary: {bool(last_summary)}")

        summary = self.summarizer.summarize(
            name=person_name,
            relationship=person_relationship,
            last_summary=last_summary,
            transcript=transcript,
            visit_count=person.get("visit_count", 0),
            last_visit=person.get("last_visit"),
            now=datetime.utcnow().date(),
        )
        
        print(f"[AudioProcessor] Generated summary: {summary[:100]}...")
        print(f"[AudioProcessor] DEBUG: Full summary from summarizer: {repr(summary)}")
        print(f"[AudioProcessor] DEBUG: Summary length: {len(summary)} chars, lines: {len(summary.split(chr(10)))}")

        # Clean up temp WAV file if we created one
        if wav_path != audio_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except:
                pass

        return transcript, summary

    def process_multi_speaker_conversation(
        self, person_ids: List[str], audio_path: str
    ) -> Dict[str, Tuple[str, str]]:
        """
        Process conversation with multiple speakers.
        Creates a unified group conversation summary instead of trying to attribute speakers.
        Returns dict mapping person_id -> (transcript, group_summary)
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(audio_path)

        # Convert to WAV if needed
        wav_path = audio_path
        if not audio_path.lower().endswith('.wav'):
            print(f"[AudioProcessor] Converting {audio_path} to WAV...")
            try:
                audio = AudioSegment.from_file(audio_path)
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    wav_path = tmp.name
                    audio.export(wav_path, format="wav")
            except Exception as e:
                print(f"[AudioProcessor] Conversion failed: {e}")
                wav_path = audio_path

        print(f"[AudioProcessor] Transcribing multi-speaker conversation {wav_path}...")
        result = self._model.transcribe(wav_path, language="en")
        full_transcript = (result.get("text") or "").strip()
        print(f"[AudioProcessor] Full conversation transcript: {full_transcript[:100]}...")

        # Get names of all participants for context
        people_names = []
        for person_id in person_ids:
            person = self.memory_store.get_person(person_id)
            people_names.append(person.get("name", person_id))

        results = {}
        
        # Create ONE unified group conversation summary for all participants
        # This avoids incorrectly attributing words to wrong speakers
        print(f"[AudioProcessor] Generating unified group conversation summary...")
        
        # Generate summary with awareness of multiple participants
        group_summary_prompt = (
            f"This is a group conversation between {', '.join(people_names)}. "
            f"Summarize the main points, emotions, and topics discussed in 2-3 lines. "
            f"Focus on what was discussed as a group, not individual speakers. "
            f"Make it warm and personal.\n\n"
            f"Transcript: {full_transcript}"
        )
        
        # Use the first person as the reference for the summary
        primary_person_id = person_ids[0]
        primary_person = self.memory_store.get_person(primary_person_id)
        
        try:
            # Use LLM if available to generate better group summary
            if self.summarizer.llm_enabled:
                print("[AudioProcessor] Using LLM for group conversation summary...")
                group_summary = self.summarizer.summarizer.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": group_summary_prompt}],
                    model="mixtral-8x7b-32768",
                    max_tokens=150,
                ).choices[0].message.content.strip()
            else:
                # Fallback: simple summary from last words
                group_summary = self._generate_simple_group_summary(full_transcript, people_names)
        except Exception as e:
            print(f"[AudioProcessor] LLM summary failed: {e}, using fallback...")
            group_summary = self._generate_simple_group_summary(full_transcript, people_names)
        
        # Apply the SAME group summary to all participants
        # This ensures consistency and avoids attribution errors
        for person_id in person_ids:
            results[person_id] = (full_transcript, group_summary)
        
        print(f"[AudioProcessor] Group conversation summary: {group_summary[:100]}...")

        # Clean up temp WAV file if we created one
        if wav_path != audio_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except:
                pass

        return results

    def _generate_simple_group_summary(self, transcript: str, people_names: list) -> str:
        """
        Generate a simple group conversation summary without LLM.
        """
        words = transcript.split()
        if len(words) < 10:
            return f"Had a conversation with {' and '.join(people_names)}."
        
        # Get last ~30 words which usually contain key points
        focus = " ".join(words[-30:])
        summary = f"Had a conversation with {' and '.join(people_names)} about: {focus.rstrip('.') + '.'}"
        return summary
