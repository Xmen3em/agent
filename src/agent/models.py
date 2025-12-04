"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional


class ConfigUpdate(BaseModel):
    """Model for updating configuration."""
    hf_token: Optional[str] = None
    zoom_account_id: Optional[str] = None
    zoom_client_id: Optional[str] = None
    zoom_client_secret: Optional[str] = None
    email_sender: Optional[EmailStr] = None
    email_passkey: Optional[str] = None
    company_name: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Model for resume analysis request."""
    candidate_email: EmailStr
    role: Literal["ai_ml_engineer", "frontend_engineer", "backend_engineer"]


class AnalysisResponse(BaseModel):
    """Model for resume analysis response."""
    is_selected: bool
    feedback: str
    matching_skills: Optional[list[str]] = None
    missing_skills: Optional[list[str]] = None
    experience_level: Optional[str] = None


class EmailRequest(BaseModel):
    """Model for email sending request."""
    candidate_email: EmailStr
    role: str
    email_type: Literal["selection", "rejection"]
    feedback: Optional[str] = None


class InterviewScheduleRequest(BaseModel):
    """Model for interview scheduling request."""
    candidate_email: EmailStr
    role: str


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Model for success responses."""
    message: str
    data: Optional[dict] = None
