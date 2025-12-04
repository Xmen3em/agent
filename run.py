"""
Quick start script for AI Recruitment System
Run this file directly to start the server
"""
import uvicorn
from agent.config import settings

if __name__ == "__main__":
    print("🚀 Starting AI Recruitment System...")
    print(f"📍 Server will be available at: http://{settings.api_host}:{settings.api_port}")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "agent.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
