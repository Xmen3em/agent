# AI Recruitment System - FastAPI

A modern recruitment system powered by AI for automated resume analysis, candidate communication, and interview scheduling.

## Features

- 🤖 **AI-Powered Resume Analysis**: Automatically analyze resumes against job requirements using Hugging Face GPT-OSS-120B
- 📧 **Automated Email Communication**: Send personalized selection/rejection emails
- 📅 **Interview Scheduling**: Automatically schedule interviews via Zoom
- 🎨 **Modern Web Interface**: Clean, responsive HTML frontend
- 🚀 **FastAPI Backend**: High-performance REST API

## Prerequisites

- Python 3.12+
- **Hugging Face Token** - Get from https://huggingface.co/settings/tokens
- **Zoom Server-to-Server OAuth** - Create at https://marketplace.zoom.us/
- **Gmail App Password** - Generate at https://myaccount.google.com/apppasswords (requires 2FA)


## Installation

1. Install dependencies:
```bash
cd agent
pip install -e .
```

2. Create a `.env` file in the project root:
```env
HF_TOKEN=your_huggingface_token
ZOOM_ACCOUNT_ID=your_zoom_account_id
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSKEY=your_gmail_app_password  # NOT your regular Gmail password!
COMPANY_NAME=Your Company Name
```

## Running the Application

### Option 1: Using Python
```bash
python -m uvicorn agent.main:app --reload --host 0.0.0.0 --port 8000
```

### Or directly with Python
python src/agent/main.py
```

Then open your browser to: http://localhost:8000

## API Endpoints

### Configuration
- `GET /api/config` - Get configuration status
- `POST /api/config` - Update configuration

### Roles
- `GET /api/roles` - Get available roles and requirements

### Application Process
- `POST /api/upload-resume` - Upload resume PDF
- `POST /api/analyze-resume` - Analyze uploaded resume
- `POST /api/send-email` - Send selection/rejection email
- `POST /api/schedule-interview` - Schedule interview
- `POST /api/process-application` - Complete application process (email + interview)

## Project Structure


agent/
├── src/
│   └── agent/
│       ├── __init__.py
│       ├── main.py          # FastAPI application
│       ├── config.py        # Configuration management
│       ├── models.py        # Pydantic models
│       ├── agents.py        # AI agent creation
│       ├── utils.py         # Utility functions
│       └── static/
│           └── index.html   # Frontend interface
├── pyproject.toml
└── README.md


## Available Roles

1. **AI/ML Engineer**
   - Python, PyTorch/TensorFlow
   - Machine Learning algorithms
   - Deep Learning and Neural Networks
   - MLOps and model deployment
   - RAG, LLM, Fine-tuning

2. **Frontend Engineer**
   - React/Vue.js/Angular
   - HTML5, CSS3, JavaScript/TypeScript
   - Responsive design
   - State management

3. **Backend Engineer**
   - Python/Java/Node.js
   - REST APIs
   - Database design
   - Cloud services (AWS/GCP/Azure)
   - Docker, Kubernetes, CI/CD

## Development

### Install in development mode:
```bash
pip install -e ".[dev]"
```

### Run with auto-reload:
```bash
uvicorn agent.main:app --reload
```

## Configuration via Web Interface

1. Navigate to http://localhost:8000
2. Click on the "Configuration" tab
3. Enter your API keys and credentials
4. Click "Save Configuration"

## Usage Flow

1. **Configure System**: Add API keys in the Configuration tab
2. **Select Role**: Choose the position to apply for
3. **Upload Resume**: Upload a PDF resume
4. **Automatic Analysis**: AI analyzes the resume against requirements
5. **Email Notification**: Candidate receives selection/rejection email
6. **Interview Scheduling**: If selected, interview is automatically scheduled

## Technologies Used

- **Backend**: FastAPI, Uvicorn
- **AI**: Hugging Face GPT-OSS-120B (via OpenAI-compatible API), Phidata
- **Communication**: Zoom API, SMTP Email
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **File Processing**: PyPDF2

## Author

Abdelmoneim Mohamed
