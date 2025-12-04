"""Configuration management for the AI Recruitment System."""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from environment
    )
    
    # Hugging Face Configuration
    hf_token: Optional[str] = None
    
    # Zoom Configuration
    zoom_account_id: Optional[str] = None
    zoom_client_id: Optional[str] = None
    zoom_client_secret: Optional[str] = None
    
    # Email Configuration
    email_sender: Optional[str] = None
    email_passkey: Optional[str] = None
    company_name: Optional[str] = "AI Recruiting Team"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["*"]


settings = Settings()
