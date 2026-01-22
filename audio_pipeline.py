import os
import tempfile
import subprocess
import shutil
from datetime import datetime
from typing import Tuple, List, Dict, Optional
import sys

import whisper

# Check if FFmpeg is available
FFMPEG_PATH = shutil.which("ffmpeg")

# If not in PATH, check common installation locations
if not FFMPEG_PATH:
    # Try winget installation location
    potential_paths = [
        r"C:\Users\ABHIRAJ ARYA\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",
        # Add more potential paths if needed
    ]
    for path in potential_paths:
        if os.path.exists(path):
            FFMPEG_PATH = path
            break

FFMPEG_AVAILABLE = FFMPEG_PATH is not None
if FFMPEG_AVAILABLE:
    print(f"[AudioProcessor] FFmpeg found at: {FFMPEG_PATH}")
else:
    print(f"[AudioProcessor] Warning: FFmpeg not found in PATH")

# Don't import pyannote at module level due to import issues
# It will be lazily imported only if needed
DIARIZATION_AVAILABLE = False

from memory_store import MemoryStore
from summarizer import ConversationSummarizer
from session_manager import SessionManager


class ConversationAudioProcessor:
    """
    Handles audio -> text -> speaker diarization -> summary -> memory update.
    Supports multi-speaker conversations with speaker attribution.
    
    Implements session-based transcription:
    - Audio chunks are accumulated in sessions while mic is ON
    - Only when mic turns OFF (session ends) is full transcript summarized
    - No repeated processing or premature summarization
    """

    def __init__(self, memory_store: MemoryStore, whisper_model: str = "tiny"):
        self.memory_store = memory_store
        self.model_name = whisper_model
        self._model = whisper.load_model(self.model_name)
        self.summarizer = ConversationSummarizer()
        self.session_manager = SessionManager()
        
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

    def _convert_to_wav_ffmpeg(self, input_path: str) -> str:
        """
        Convert audio file to WAV using FFmpeg.
        
        Args:
            input_path: Path to input audio file
        
        Returns:
            Path to converted WAV file
        
        Raises:
            RuntimeError: If FFmpeg is not available or conversion fails
        """
        if not FFMPEG_AVAILABLE:
            raise RuntimeError(
                "FFmpeg not found in PATH. Install FFmpeg to convert audio formats.\n"
                "Windows: choco install ffmpeg\n"
                "macOS: brew install ffmpeg\n"
                "Linux: sudo apt-get install ffmpeg"
            )
        
        output_path = None
        try:
            # Create temp WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                output_path = tmp.name
            
            # Convert using FFmpeg
            print(f"[AudioProcessor] Converting {os.path.basename(input_path)} to WAV with FFmpeg...")
            result = subprocess.run(
                [
                    FFMPEG_PATH,
                    "-i", input_path,
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",  # Overwrite output file
                    output_path
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")
            
            print(f"[AudioProcessor] Converted to {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError("FFmpeg conversion timed out")
        except Exception as e:
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise RuntimeError(f"FFmpeg conversion failed: {e}")

    def _convert_audio_to_wav(self, audio_path: str) -> str:
        """
        Convert audio to WAV format, trying multiple methods.
        
        Returns:
            Path to WAV file (either original if already WAV, or converted)
        """
        if audio_path.lower().endswith('.wav'):
            return audio_path
        
        # Try FFmpeg first (if available)
        if FFMPEG_AVAILABLE:
            try:
                return self._convert_to_wav_ffmpeg(audio_path)
            except Exception as e:
                print(f"[AudioProcessor] FFmpeg conversion failed: {e}")
                print(f"[AudioProcessor] Attempting direct Whisper processing...")
        
        # Fallback: return original file, let Whisper handle it
        print(f"[AudioProcessor] FFmpeg not available, using Whisper directly on {os.path.basename(audio_path)}")
        return audio_path

    def process_conversation(self, person_id: str, audio_path: str) -> Tuple[str, str]:
        """
        Returns (transcript, summary)
        Accepts any audio format (webm, mp3, wav) and converts to wav for Whisper.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(audio_path)

        print(f"[AudioProcessor] Processing conversation for person: {person_id}")

        # Convert to WAV if needed (Whisper works best with WAV)
        wav_path = self._convert_audio_to_wav(audio_path)
        temp_wav_created = (wav_path != audio_path)

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
        if temp_wav_created and os.path.exists(wav_path):
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
        wav_path = self._convert_audio_to_wav(audio_path)
        temp_wav_created = (wav_path != audio_path)

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
        if temp_wav_created and os.path.exists(wav_path):
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
    # ============================================================================
    # SESSION-BASED TRANSCRIPTION API
    # ============================================================================
    # These methods implement the session-based transcription pipeline where:
    # 1. Microphone ON -> start_session()
    # 2. Audio chunks received -> add_audio_chunk() [accumulates, no summarization]
    # 3. Microphone OFF -> end_session_and_summarize() [only then summarize]
    # ============================================================================

    def start_session(self, person_id: str) -> str:
        """
        Start a new conversation session for a person.
        Call this when the microphone turns ON.
        
        Args:
            person_id: ID of the person
        
        Returns:
            Session ID for reference
        
        Raises:
            RuntimeError: If a session is already active for this person
        """
        try:
            session = self.session_manager.start_session(person_id)
            print(f"[AudioProcessor] Session started for {person_id}: {session.session_id[:16]}")
            return session.session_id
        except RuntimeError as e:
            print(f"[AudioProcessor] ERROR: {e}")
            raise

    def add_audio_chunk(self, person_id: str, audio_path: str) -> Dict:
        """
        Process and add an audio chunk to the active session.
        Call this for each audio chunk while the microphone is ON.
        
        IMPORTANT: This method does NOT summarize.
        It only transcribes and accumulates the chunk.
        
        Args:
            person_id: ID of the person
            audio_path: Path to the audio chunk file
        
        Returns:
            Dict with status, chunk transcript, and session status
        
        Raises:
            RuntimeError: If no active session for this person
        """
        if not self.session_manager.has_active_session(person_id):
            raise RuntimeError(f"No active session for person: {person_id}")
        
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(audio_path)
        
        print(f"[AudioProcessor] Processing audio chunk for {person_id}")
        
        # Convert to WAV if needed
        wav_path = self._convert_audio_to_wav(audio_path)
        temp_wav_created = (wav_path != audio_path)
        
        # Transcribe the chunk
        try:
            print(f"[AudioProcessor] Transcribing chunk...")
            result = self._model.transcribe(wav_path, language="en")
            chunk_transcript = (result.get("text") or "").strip()
            
            if not chunk_transcript:
                print(f"[AudioProcessor] WARNING: Empty transcription from chunk")
                return {
                    "status": "empty_chunk",
                    "person_id": person_id,
                    "chunk_transcript": "",
                    "session_status": self.session_manager.get_active_session(person_id).get_status()
                }
            
            # Add to session (this appends, doesn't overwrite)
            self.session_manager.add_chunk_to_session(person_id, chunk_transcript)
            
            session = self.session_manager.get_active_session(person_id)
            print(f"[AudioProcessor] Chunk added. Session now has {session.chunk_count} chunks")
            
            return {
                "status": "chunk_added",
                "person_id": person_id,
                "chunk_transcript": chunk_transcript,
                "session_status": session.get_status(),
            }
        finally:
            # Clean up temp WAV if created
            if temp_wav_created and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass

    def end_session_and_summarize(self, person_id: str) -> Dict:
        """
        End the active session and summarize the ENTIRE conversation.
        Call this when the microphone turns OFF.
        
        This is the ONLY place where summarization happens.
        The full accumulated transcript is passed to the summarizer.
        
        Args:
            person_id: ID of the person
        
        Returns:
            Dict with status, full_transcript, summary, and updated memory
        
        Raises:
            RuntimeError: If no active session for this person
        """
        if not self.session_manager.has_active_session(person_id):
            raise RuntimeError(f"No active session for person: {person_id}")
        
        # End the session and get full transcript
        full_transcript, session = self.session_manager.end_session(person_id)
        
        print(f"[AudioProcessor] Session ended. Full transcript length: {len(full_transcript)} chars")
        
        if not full_transcript or not full_transcript.strip():
            print(f"[AudioProcessor] WARNING: Empty transcript for session {session.session_id}")
            return {
                "status": "empty_session",
                "session_id": session.session_id,
                "person_id": person_id,
                "full_transcript": "",
                "summary": "",
                "memory": self.memory_store.get_person(person_id),
            }
        
        # Get person info for summarization
        person = self.memory_store.get_person(person_id)
        last_summary = person.get("last_summary", "")
        person_name = person.get("name", person_id)
        person_relationship = person.get("relationship", "")
        
        print(f"[AudioProcessor] Summarizing full conversation for {person_name}...")
        
        # SINGLE SUMMARIZATION of full transcript (only happens here)
        summary = self.summarizer.summarize(
            name=person_name,
            relationship=person_relationship,
            last_summary=last_summary,
            transcript=full_transcript,  # FULL accumulated transcript
            visit_count=person.get("visit_count", 0),
            last_visit=person.get("last_visit"),
            now=datetime.utcnow().date(),
        )
        
        print(f"[AudioProcessor] Summary generated: {len(summary)} chars")
        
        # Update memory with the summary
        updated_memory = self.memory_store.update_after_visit(person_id, summary)
        
        return {
            "status": "success",
            "session_id": session.session_id,
            "person_id": person_id,
            "full_transcript": full_transcript,
            "summary": summary,
            "memory": updated_memory,
            "session_metadata": {
                "chunks_processed": session.chunk_count,
                "audio_duration_seconds": session.audio_duration_seconds,
                "duration_seconds": (session.ended_at - session.created_at).total_seconds(),
            }
        }

    def get_session_status(self, person_id: str) -> Optional[Dict]:
        """
        Get the status of the active session for a person.
        Returns None if no active session.
        """
        session = self.session_manager.get_active_session(person_id)
        return session.get_status() if session else None

    def get_all_active_sessions_status(self) -> Dict:
        """Get status of all active sessions across all people."""
        return self.session_manager.get_status()