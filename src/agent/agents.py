"""Agent creation and management for the AI Recruitment System."""
import json
import os
from typing import Tuple, Literal
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.email import EmailTools
from phi.utils.log import logger
from datetime import datetime, timedelta
import pytz

from .utils import CustomZoomTool, ROLE_REQUIREMENTS


def create_resume_analyzer(hf_token: str) -> Agent:
    """Creates and returns a resume analysis agent using Hugging Face model."""
    return Agent(
        model=OpenAIChat(
            id="openai/gpt-oss-120b:nscale",
            api_key=hf_token,
            base_url="https://router.huggingface.co/v1"
        ),
        description="You are an expert technical recruiter who analyzes resumes.",
        instructions=[
            "Analyze the resume against the provided job requirements",
            "Be lenient with AI/ML candidates who show strong potential",
            "Consider project experience as valid experience",
            "Value hands-on experience with key technologies",
            "Return a JSON response with selection decision and feedback"
        ],
        markdown=True
    )


def create_email_agent(
    hf_token: str,
    candidate_email: str,
    sender_email: str,
    sender_passkey: str,
    company_name: str
) -> Agent:
    """Creates and returns an email agent using Hugging Face model."""
    return Agent(
        model=OpenAIChat(
            id="openai/gpt-oss-120b:nscale",
            api_key=hf_token,
            base_url="https://router.huggingface.co/v1"
        ),
        tools=[EmailTools(
            receiver_email=candidate_email,
            sender_email=sender_email,
            sender_name=company_name,
            sender_passkey=sender_passkey
        )],
        description="You are a professional recruitment coordinator handling email communications.",
        instructions=[
            "Draft and send professional recruitment emails",
            "Act like a human writing an email and use all lowercase letters",
            "Maintain a friendly yet professional tone",
            "Always end emails with exactly: 'best,\\nthe ai recruiting team'",
            "Never include the sender's or receiver's name in the signature",
            f"The name of the company is '{company_name}'"
        ],
        markdown=True,
        show_tool_calls=True
    )


def create_scheduler_agent(
    hf_token: str,
    zoom_account_id: str,
    zoom_client_id: str,
    zoom_client_secret: str
) -> Agent:
    """Creates and returns a scheduler agent using Hugging Face model."""
    zoom_tools = CustomZoomTool(
        account_id=zoom_account_id,
        client_id=zoom_client_id,
        client_secret=zoom_client_secret
    )

    return Agent(
        name="Interview Scheduler",
        model=OpenAIChat(
            id="openai/gpt-oss-120b:nscale",
            api_key=hf_token,
            base_url="https://router.huggingface.co/v1"
        ),
        tools=[zoom_tools],
        description="You are an interview scheduling coordinator.",
        instructions=[
            "You are an expert at scheduling technical interviews using Zoom.",
            "Schedule interviews during business hours (9 AM - 5 PM EST)",
            "Create meetings with proper titles and descriptions",
            "Ensure all meeting details are included in responses",
            "Use ISO 8601 format for dates",
            "Handle scheduling errors gracefully"
        ],
        markdown=True,
        show_tool_calls=True
    )


def analyze_resume(
    resume_text: str,
    role: Literal["ai_ml_engineer", "frontend_engineer", "backend_engineer"],
    analyzer: Agent
) -> Tuple[bool, str, dict]:
    """
    Analyze a resume against role requirements.
    
    Returns:
        Tuple of (is_selected, feedback, details_dict)
    """
    try:
        response = analyzer.run(
            f"""Please analyze this resume against the following requirements and provide your response in valid JSON format:
            
            Role Requirements:
            {ROLE_REQUIREMENTS[role]}
            
            Resume Text:
            {resume_text}
            
            Your response must be a valid JSON object like this:
            {{
                "selected": true/false,
                "feedback": "Detailed feedback explaining the decision",
                "matching_skills": ["skill1", "skill2"],
                "missing_skills": ["skill3", "skill4"],
                "experience_level": "junior/mid/senior"
            }}
            
            Evaluation criteria:
            1. Match at least 70% of required skills
            2. Consider both theoretical knowledge and practical experience
            3. Value project experience and real-world applications
            4. Consider transferable skills from similar technologies
            5. Look for evidence of continuous learning and adaptability
            
            Important: Return ONLY the JSON object without any markdown formatting or backticks.
            """
        )

        assistant_message = next(
            (msg.content for msg in response.messages if msg.role == 'assistant'), 
            None
        )
        
        if not assistant_message:
            raise ValueError("No assistant message found in response.")

        result = json.loads(assistant_message.strip())
        
        if not isinstance(result, dict) or not all(k in result for k in ["selected", "feedback"]):
            raise ValueError("Invalid response format")

        return result["selected"], result["feedback"], result

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error processing response: {str(e)}")
        raise ValueError(f"Error analyzing resume: {str(e)}")


def send_selection_email(email_agent: Agent, to_email: str, role: str) -> None:
    """Send a selection confirmation email."""
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their selection for the {role} position.
        The email should:
        1. Congratulate them on being selected
        2. Explain the next steps in the process
        3. Mention that they will receive interview details shortly
        """
    )


def send_rejection_email(
    email_agent: Agent, 
    to_email: str, 
    role: str, 
    feedback: str
) -> None:
    """Send a rejection email with constructive feedback."""
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their application for the {role} position.
        Use this specific style:
        1. use all lowercase letters
        2. be empathetic and human
        3. mention specific feedback from: {feedback}
        4. encourage them to upskill and try again
        5. suggest some learning resources based on missing skills
        6. end the email with exactly:
           best,
           the ai recruiting team
        
        Do not include any names in the signature.
        The tone should be like a human writing a quick but thoughtful email.
        """
    )


def schedule_interview(
    scheduler: Agent, 
    candidate_email: str, 
    email_agent: Agent, 
    role: str
) -> str:
    """
    Schedule an interview and send confirmation email.
    
    Returns:
        Meeting details as a string
    """
    try:
        # Get current time in IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist_tz)

        tomorrow_ist = current_time_ist + timedelta(days=1)
        interview_time = tomorrow_ist.replace(hour=11, minute=0, second=0, microsecond=0)
        formatted_time = interview_time.strftime('%Y-%m-%dT%H:%M:%S')

        meeting_response = scheduler.run(
            f"""Schedule a 60-minute technical interview with these specifications:
            - Title: '{role} Technical Interview'
            - Date: {formatted_time}
            - Timezone: IST (India Standard Time)
            - Attendee: {candidate_email}
            
            Important Notes:
            - The meeting must be between 9 AM - 5 PM IST
            - Use IST (UTC+5:30) timezone for all communications
            - Include timezone information in the meeting details
            """
        )

        email_agent.run(
            f"""Send an interview confirmation email with these details:
            - Role: {role} position
            - Meeting Details: {meeting_response}
            
            Important:
            - Clearly specify that the time is in IST (India Standard Time)
            - Ask the candidate to join 5 minutes early
            - Include timezone conversion link if possible
            - Ask him to be confident and not so nervous and prepare well for the interview
            """
        )
        
        return str(meeting_response)
        
    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        raise ValueError(f"Unable to schedule interview: {str(e)}")
