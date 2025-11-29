"""Whisper service for audio transcription."""
import whisper
import tempfile
import os
from fastapi import UploadFile
from app.config import settings


class WhisperService:
    """Service for transcribing audio using Whisper."""
    
    def __init__(self):
        """Initialize Whisper model."""
        self.model = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of Whisper model."""
        if not self._initialized:
            try:
                self.model = whisper.load_model(settings.whisper_model_size)
                self._initialized = True
            except Exception as e:
                raise Exception(f"Failed to load Whisper model: {str(e)}")
    
    def transcribe_audio(self, audio_file: UploadFile) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: FastAPI UploadFile containing audio data
            
        Returns:
            Transcribed text string
            
        Raises:
            Exception: If transcription fails
        """
        # Ensure model is loaded
        self._ensure_initialized()
        
        # Validate file
        if not audio_file.filename:
            raise ValueError("Audio file must have a filename")
        
        # Create temporary file to save audio
        # Use appropriate extension based on file type
        file_ext = os.path.splitext(audio_file.filename)[1] or ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            try:
                # Read audio file content
                content = audio_file.file.read()
                if not content:
                    raise ValueError("Audio file is empty")
                
                tmp_file.write(content)
                tmp_file.flush()
                
                # Transcribe using Whisper
                result = self.model.transcribe(tmp_file.name)
                transcribed_text = result.get("text", "").strip()
                
                if not transcribed_text:
                    raise ValueError("No text was transcribed from audio")
                
                return transcribed_text
            except Exception as e:
                raise Exception(f"Failed to transcribe audio: {str(e)}")
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file.name):
                    try:
                        os.unlink(tmp_file.name)
                    except OSError:
                        pass  # Ignore cleanup errors


# Global instance
whisper_service = WhisperService()

