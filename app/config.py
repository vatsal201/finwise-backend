"""Application configuration settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra variables in .env file
    )
    
    # Database configuration (JSON file storage)
    # Data is stored in data/users.json and data/transactions.json
    
    # Gemini configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    
    # Ollama configuration (fallback)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    
    # Whisper configuration
    whisper_model_size: str = "medium"


settings = Settings()

