"""
Session-based audio transcription system for Dementia Memory Assist.

This module manages conversation sessions that accumulate audio chunks
while the microphone is ON and finalize transcription/summarization only
when the microphone turns OFF.

Key Features:
- Per-person session management
- Incremental transcript accumulation
- Single summarization on session end
- Efficient memory usage
- Real-time suitable
"""

from datetime import datetime
from typing import Dict, Optional, List, Tuple
import uuid


class ConversationSession:
    """
    Represents a single conversation session for a person.
    Accumulates transcription chunks until the session is ended.
    """
    
    def __init__(self, person_id: str, session_id: Optional[str] = None):
        """
        Initialize a new conversation session.
        
        Args:
            person_id: ID of the person for this session
            session_id: Optional session identifier (generated if not provided)
        """
        self.person_id = person_id
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.ended_at: Optional[datetime] = None
        
        # Transcript accumulation
        self.transcript_chunks: List[str] = []
        self.full_transcript = ""
        
        # Metadata
        self.chunk_count = 0
        self.is_active = True
        self.audio_duration_seconds = 0.0
    
    def add_chunk(self, transcript_chunk: str, duration: float = 0.0) -> None:
        """
        Add a transcribed chunk to the session.
        
        Args:
            transcript_chunk: Text transcribed from an audio chunk
            duration: Duration of the audio chunk in seconds
        """
        if not self.is_active:
            raise RuntimeError(f"Session {self.session_id} is not active")
        
        if transcript_chunk and transcript_chunk.strip():
            self.transcript_chunks.append(transcript_chunk.strip())
            self.chunk_count += 1
            self.audio_duration_seconds += duration
            # Update full transcript (without reprocessing)
            self.full_transcript = " ".join(self.transcript_chunks)
            
            print(f"[Session {self.session_id[:8]}] Chunk {self.chunk_count} added "
                  f"({len(transcript_chunk)} chars, {len(self.transcript_chunks)} total chunks)")
    
    def end_session(self) -> str:
        """
        End the session and return the finalized transcript.
        
        Returns:
            Complete accumulated transcript for the entire session
        """
        if not self.is_active:
            raise RuntimeError(f"Session {self.session_id} is already ended")
        
        self.is_active = False
        self.ended_at = datetime.utcnow()
        
        print(f"[Session {self.session_id[:8]}] ENDED - "
              f"Chunks: {self.chunk_count}, Total length: {len(self.full_transcript)} chars, "
              f"Duration: {self.audio_duration_seconds:.1f}s")
        
        return self.full_transcript
    
    def get_status(self) -> Dict:
        """Get current session status."""
        return {
            "session_id": self.session_id,
            "person_id": self.person_id,
            "is_active": self.is_active,
            "chunk_count": self.chunk_count,
            "transcript_length": len(self.full_transcript),
            "audio_duration": self.audio_duration_seconds,
            "created_at": self.created_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


class SessionManager:
    """
    Manages multiple concurrent conversation sessions.
    Ensures one active session per person at a time.
    """
    
    def __init__(self):
        """Initialize session manager."""
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.session_history: Dict[str, List[ConversationSession]] = {}
    
    def start_session(self, person_id: str) -> ConversationSession:
        """
        Start a new conversation session for a person.
        
        Raises error if a session is already active for this person.
        
        Args:
            person_id: ID of the person
        
        Returns:
            New ConversationSession instance
        """
        if person_id in self.active_sessions:
            active_session = self.active_sessions[person_id]
            if active_session.is_active:
                raise RuntimeError(
                    f"Session already active for {person_id}: {active_session.session_id}"
                )
        
        session = ConversationSession(person_id)
        self.active_sessions[person_id] = session
        
        if person_id not in self.session_history:
            self.session_history[person_id] = []
        
        print(f"[SessionManager] New session started for {person_id}: {session.session_id[:8]}")
        return session
    
    def add_chunk_to_session(self, person_id: str, transcript_chunk: str, 
                            duration: float = 0.0) -> None:
        """
        Add a transcribed chunk to the active session for a person.
        
        Args:
            person_id: ID of the person
            transcript_chunk: Transcribed text from audio chunk
            duration: Duration of audio chunk in seconds
        
        Raises:
            RuntimeError: If no active session exists for this person
        """
        if person_id not in self.active_sessions:
            raise RuntimeError(f"No active session for person: {person_id}")
        
        session = self.active_sessions[person_id]
        if not session.is_active:
            raise RuntimeError(f"Session is not active for person: {person_id}")
        
        session.add_chunk(transcript_chunk, duration)
    
    def end_session(self, person_id: str) -> Tuple[str, ConversationSession]:
        """
        End the active session for a person.
        
        Returns:
            Tuple of (full_transcript, session_object)
        
        Raises:
            RuntimeError: If no active session exists for this person
        """
        if person_id not in self.active_sessions:
            raise RuntimeError(f"No active session for person: {person_id}")
        
        session = self.active_sessions[person_id]
        if not session.is_active:
            raise RuntimeError(f"Session already ended for person: {person_id}")
        
        full_transcript = session.end_session()
        self.session_history[person_id].append(session)
        del self.active_sessions[person_id]
        
        print(f"[SessionManager] Session ended for {person_id}")
        return full_transcript, session
    
    def get_active_session(self, person_id: str) -> Optional[ConversationSession]:
        """Get the active session for a person, or None if no active session."""
        session = self.active_sessions.get(person_id)
        return session if session and session.is_active else None
    
    def has_active_session(self, person_id: str) -> bool:
        """Check if there's an active session for a person."""
        return person_id in self.active_sessions and self.active_sessions[person_id].is_active
    
    def get_session_history(self, person_id: str) -> List[ConversationSession]:
        """Get all completed sessions for a person."""
        return self.session_history.get(person_id, [])
    
    def get_all_active_sessions(self) -> Dict[str, ConversationSession]:
        """Get all currently active sessions."""
        return {
            person_id: session 
            for person_id, session in self.active_sessions.items()
            if session.is_active
        }
    
    def get_status(self) -> Dict:
        """Get overall session manager status."""
        return {
            "active_sessions": {
                person_id: session.get_status()
                for person_id, session in self.active_sessions.items()
                if session.is_active
            },
            "total_history": sum(len(sessions) for sessions in self.session_history.values()),
            "timestamp": datetime.utcnow().isoformat(),
        }
