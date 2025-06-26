from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import uvicorn
import boto3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize S3 client
s3_client = boto3.client('s3')
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "akash-chat-app-bucket-2025")

class ChatRequest(BaseModel):
    prompt: str

class ChatHistory(BaseModel):
    user_message: str
    ai_response: str
    timestamp: str

@app.get("/")
def hello():
    return {"message": "Hello from Docker on EC2!"}

@app.get("/s3/status")
def s3_status():
    """Check S3 connectivity and bucket access"""
    try:
        # List objects in bucket to test access
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        return {
            "status": "connected",
            "bucket": S3_BUCKET_NAME,
            "message": "S3 bucket is accessible"
        }
    except Exception as e:
        return {
            "status": "error",
            "bucket": S3_BUCKET_NAME,
            "error": str(e)
        }

@app.post("/chat")
async def chat(body: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not set")
    
    user_prompt = body.prompt
    timestamp = datetime.now().isoformat()
    
    # Call Gemini API
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
        ai_response = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Save chat history to S3
        try:
            await save_chat_to_s3(user_prompt, ai_response, timestamp)
        except Exception as s3_error:
            print(f"Failed to save to S3: {s3_error}")
            # Continue even if S3 save fails
        
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_chat_to_s3(user_message: str, ai_response: str, timestamp: str):
    """Save chat conversation to S3"""
    try:
        chat_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": timestamp
        }
        
        # Create S3 key with timestamp for uniqueness
        s3_key = f"chat-history/{timestamp.split('T')[0]}/{timestamp}.json"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(chat_data),
            ContentType='application/json'
        )
        
        print(f"Chat saved to S3: {s3_key}")
    except Exception as e:
        print(f"Error saving to S3: {e}")
        raise e

@app.get("/s3/chat-history")
def get_chat_history(limit: int = 10):
    """Retrieve recent chat history from S3"""
    try:
        # List objects in chat-history folder
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix="chat-history/",
            MaxKeys=limit
        )
        
        chat_history = []
        
        if 'Contents' in response:
            # Sort by last modified (newest first)
            objects = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
            
            for obj in objects[:limit]:
                try:
                    # Get object content
                    content = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=obj['Key'])
                    chat_data = json.loads(content['Body'].read().decode('utf-8'))
                    chat_history.append(chat_data)
                except Exception as e:
                    print(f"Error reading object {obj['Key']}: {e}")
                    continue
        
        return {
            "status": "success",
            "count": len(chat_history),
            "chat_history": chat_history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@app.get("/s3/chat-history/count")
def get_chat_count():
    """Get total number of chats stored in S3"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix="chat-history/"
        )
        
        count = response.get('KeyCount', 0)
        
        return {
            "status": "success",
            "total_chats": count,
            "bucket": S3_BUCKET_NAME
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting chats: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", port=5000, reload=False)
