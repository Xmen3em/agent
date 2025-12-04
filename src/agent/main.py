"""FastAPI application for AI Recruitment System."""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from typing import Optional
import logging

from .config import settings
from .models import (
    ConfigUpdate, AnalysisResponse, EmailRequest, 
    InterviewScheduleRequest, ErrorResponse, SuccessResponse
)
from .utils import extract_text_from_pdf, ROLE_REQUIREMENTS
from .agents import (
    create_resume_analyzer, create_email_agent, create_scheduler_agent,
    analyze_resume, send_selection_email, send_rejection_email, schedule_interview
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Recruitment System",
    description="Automated recruitment system with AI-powered resume analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Store uploaded resumes temporarily
resume_storage = {}


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse(content="<h1>AI Recruitment System</h1><p>Frontend not found. Please check static files.</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Recruitment System"}


@app.get("/api/config")
async def get_config():
    """Get current configuration (without sensitive data)."""
    return {
        "company_name": settings.company_name,
        "has_hf_token": bool(settings.hf_token),
        "has_zoom_config": all([
            settings.zoom_account_id, 
            settings.zoom_client_id, 
            settings.zoom_client_secret
        ]),
        "has_email_config": all([
            settings.email_sender, 
            settings.email_passkey
        ])
    }


@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update configuration."""
    try:
        if config.hf_token:
            settings.hf_token = config.hf_token
        if config.zoom_account_id:
            settings.zoom_account_id = config.zoom_account_id
        if config.zoom_client_id:
            settings.zoom_client_id = config.zoom_client_id
        if config.zoom_client_secret:
            settings.zoom_client_secret = config.zoom_client_secret
        if config.email_sender:
            settings.email_sender = config.email_sender
        if config.email_passkey:
            settings.email_passkey = config.email_passkey
        if config.company_name:
            settings.company_name = config.company_name
            
        return SuccessResponse(message="Configuration updated successfully")
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/roles")
async def get_roles():
    """Get available roles and their requirements."""
    return {
        "roles": list(ROLE_REQUIREMENTS.keys()),
        "requirements": ROLE_REQUIREMENTS
    }


@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    candidate_email: str = Form(...),
    role: str = Form(...)
):
    """Upload and process a resume."""
    try:
        # Validate role
        if role not in ROLE_REQUIREMENTS:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # Read file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        content = await file.read()
        
        # Extract text
        try:
            resume_text = extract_text_from_pdf(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
        
        # Store resume
        resume_id = f"{candidate_email}_{role}"
        resume_storage[resume_id] = {
            "text": resume_text,
            "email": candidate_email,
            "role": role,
            "filename": file.filename
        }
        
        return SuccessResponse(
            message="Resume uploaded successfully",
            data={
                "resume_id": resume_id,
                "filename": file.filename,
                "text_length": len(resume_text)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-resume", response_model=AnalysisResponse)
async def analyze_resume_endpoint(
    candidate_email: str = Form(...),
    role: str = Form(...)
):
    """Analyze a resume."""
    try:
        # Check configuration
        if not settings.hf_token:
            raise HTTPException(status_code=400, detail="Hugging Face token not configured")
        
        # Get resume
        resume_id = f"{candidate_email}_{role}"
        if resume_id not in resume_storage:
            raise HTTPException(status_code=404, detail="Resume not found. Please upload first.")
        
        resume_data = resume_storage[resume_id]
        
        # Create analyzer
        analyzer = create_resume_analyzer(settings.hf_token)
        
        # Analyze
        is_selected, feedback, details = analyze_resume(
            resume_data["text"],
            role,
            analyzer
        )
        
        # Store result
        resume_storage[resume_id]["analysis"] = {
            "is_selected": is_selected,
            "feedback": feedback,
            "details": details
        }
        
        return AnalysisResponse(
            is_selected=is_selected,
            feedback=feedback,
            matching_skills=details.get("matching_skills"),
            missing_skills=details.get("missing_skills"),
            experience_level=details.get("experience_level")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-email")
async def send_email(request: EmailRequest):
    """Send an email to the candidate."""
    try:
        # Check configuration
        if not all([
            settings.hf_token,
            settings.email_sender,
            settings.email_passkey
        ]):
            raise HTTPException(
                status_code=400, 
                detail="Email configuration incomplete"
            )
        
        # Create email agent
        email_agent = create_email_agent(
            hf_token=settings.hf_token,
            candidate_email=request.candidate_email,
            sender_email=settings.email_sender,
            sender_passkey=settings.email_passkey,
            company_name=settings.company_name
        )
        
        # Send appropriate email
        if request.email_type == "selection":
            send_selection_email(email_agent, request.candidate_email, request.role)
        else:
            if not request.feedback:
                raise HTTPException(
                    status_code=400, 
                    detail="Feedback required for rejection emails"
                )
            send_rejection_email(
                email_agent, 
                request.candidate_email, 
                request.role, 
                request.feedback
            )
        
        return SuccessResponse(message=f"{request.email_type.capitalize()} email sent successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/schedule-interview")
async def schedule_interview_endpoint(request: InterviewScheduleRequest):
    """Schedule an interview."""
    try:
        # Check configuration
        if not all([
            settings.hf_token,
            settings.zoom_account_id,
            settings.zoom_client_id,
            settings.zoom_client_secret,
            settings.email_sender,
            settings.email_passkey
        ]):
            raise HTTPException(
                status_code=400, 
                detail="Configuration incomplete. Please check Zoom and email settings."
            )
        
        # Create agents
        scheduler_agent = create_scheduler_agent(
            hf_token=settings.hf_token,
            zoom_account_id=settings.zoom_account_id,
            zoom_client_id=settings.zoom_client_id,
            zoom_client_secret=settings.zoom_client_secret
        )
        
        email_agent = create_email_agent(
            hf_token=settings.hf_token,
            candidate_email=request.candidate_email,
            sender_email=settings.email_sender,
            sender_passkey=settings.email_passkey,
            company_name=settings.company_name
        )
        
        # Schedule interview
        meeting_details = schedule_interview(
            scheduler_agent,
            request.candidate_email,
            email_agent,
            request.role
        )
        
        return SuccessResponse(
            message="Interview scheduled successfully",
            data={"meeting_details": meeting_details}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-application")
async def process_application(
    candidate_email: str = Form(...),
    role: str = Form(...)
):
    """Process complete application: send selection email and schedule interview."""
    try:
        # Check if candidate was selected
        resume_id = f"{candidate_email}_{role}"
        if resume_id not in resume_storage:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        analysis = resume_storage[resume_id].get("analysis")
        if not analysis or not analysis.get("is_selected"):
            raise HTTPException(
                status_code=400, 
                detail="Candidate not selected or analysis not completed"
            )
        
        # Send selection email
        await send_email(EmailRequest(
            candidate_email=candidate_email,
            role=role,
            email_type="selection"
        ))
        
        # Schedule interview
        await schedule_interview_endpoint(InterviewScheduleRequest(
            candidate_email=candidate_email,
            role=role
        ))
        
        return SuccessResponse(
            message="Application processed successfully. Email sent and interview scheduled."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing application: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
