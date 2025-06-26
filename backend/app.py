from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import uvicorn
import logging
from dotenv import load_dotenv
from s3_service import S3Service
from datetime import datetime
import json

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str

# Initialize S3 service (bucket name from environment variable)
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
s3_service = S3Service(bucket_name=S3_BUCKET) if S3_BUCKET else None

@app.get("/")
def hello():
    return {"message": "Hello from Docker on EC2!"}

@app.post("/chat")
async def chat(body: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not set")
    
    user_prompt = body.prompt
    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ]
    }
    params = {"key": api_key}
    
    try:
        response = requests.post(gemini_url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        gemini_response = response.json()
        generated = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Store chat conversation in S3 if bucket is configured
        if s3_service and S3_BUCKET:
            try:
                timestamp = datetime.now().isoformat()
                chat_log = {
                    "timestamp": timestamp,
                    "user_prompt": user_prompt,
                    "ai_response": generated
                }
                key = f"chat-logs/{timestamp}-chat.json"
                s3_service.upload_file(
                    file_content=json.dumps(chat_log).encode('utf-8'),
                    key=key,
                    content_type="application/json"
                )
                logger.info(f"Stored chat log in S3: {key}")
            except Exception as e:
                logger.error(f"Failed to store chat log in S3: {str(e)}")
                # Don't fail the chat if S3 storage fails
        
        return {"response": generated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/s3/status")
def s3_status():
    """Check S3 connectivity and bucket access"""
    if not s3_service or not S3_BUCKET:
        return {"status": "S3 not configured"}
    
    try:
        bucket_accessible = s3_service.check_bucket_access()
        return {
            "status": "S3 configured",
            "bucket": S3_BUCKET,
            "accessible": bucket_accessible
        }
    except Exception as e:
        return {
            "status": "S3 error",
            "error": str(e)
        }

@app.get("/s3/chat-logs")
def get_chat_logs():
    """List recent chat logs from S3"""
    if not s3_service or not S3_BUCKET:
        raise HTTPException(status_code=404, detail="S3 not configured")
    
    try:
        files = s3_service.list_files(prefix="chat-logs/")
        return {"chat_logs": files[-10:]}  # Return last 10 files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chat logs: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", port=5000, reload=False)
