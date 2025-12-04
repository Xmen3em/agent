"""Utility functions for the AI Recruitment System."""
import PyPDF2
import time
import requests
from typing import Optional
from phi.utils.log import logger
from phi.tools.zoom import ZoomTool
from io import BytesIO


class CustomZoomTool(ZoomTool):
    """Custom Zoom tool with OAuth token management."""
    
    def __init__(
        self, 
        *, 
        account_id: Optional[str] = None, 
        client_id: Optional[str] = None, 
        client_secret: Optional[str] = None, 
        name: str = "zoom_tool"
    ):
        super().__init__(
            account_id=account_id, 
            client_id=client_id, 
            client_secret=client_secret, 
            name=name
        )
        self.token_url = "https://zoom.us/oauth/token"
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self) -> str:
        """Get or refresh the OAuth access token."""
        if self.access_token and time.time() < self.token_expires_at:
            return str(self.access_token)
            
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "account_credentials", "account_id": self.account_id}

        try:
            response = requests.post(
                self.token_url, 
                headers=headers, 
                data=data, 
                auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()

            token_info = response.json()
            self.access_token = token_info["access_token"]
            expires_in = token_info["expires_in"]
            self.token_expires_at = time.time() + expires_in - 60

            self._set_parent_token(str(self.access_token))
            return str(self.access_token)

        except requests.RequestException as e:
            logger.error(f"Error fetching access token: {e}")
            return ""

    def _set_parent_token(self, token: str) -> None:
        """Helper method to set the token in the parent ZoomTool class."""
        if token:
            self._ZoomTool__access_token = token


def extract_text_from_pdf(pdf_file: bytes) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_file: PDF file content as bytes
        
    Returns:
        Extracted text from the PDF
    """
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        raise ValueError(f"Error extracting PDF text: {str(e)}")


# Role requirements as a constant dictionary
ROLE_REQUIREMENTS = {
    "ai_ml_engineer": """
        Required Skills:
        - Python, PyTorch/TensorFlow
        - Machine Learning algorithms and frameworks
        - Deep Learning and Neural Networks
        - Data preprocessing and analysis
        - MLOps and model deployment
        - RAG, LLM, Finetuning and Prompt Engineering
    """,

    "frontend_engineer": """
        Required Skills:
        - React/Vue.js/Angular
        - HTML5, CSS3, JavaScript/TypeScript
        - Responsive design
        - State management
        - Frontend testing
    """,

    "backend_engineer": """
        Required Skills:
        - Python/Java/Node.js
        - REST APIs
        - Database design and management
        - System architecture
        - Cloud services (AWS/GCP/Azure)
        - Kubernetes, Docker, CI/CD
    """
}
