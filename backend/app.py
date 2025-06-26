from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import uvicorn
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

class ChatRequest(BaseModel):
    prompt: str

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
        return {"response": generated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", port=5000, reload=False)
