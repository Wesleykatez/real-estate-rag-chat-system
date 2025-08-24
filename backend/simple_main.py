from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
from datetime import datetime
import json
import shutil
from pathlib import Path
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Configure Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize FastAPI app
app = FastAPI(title="Dubai Real Estate RAG Chat System", version="1.2.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://192.168.1.241:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File upload settings
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# In-memory storage for testing
conversations = {}
messages = {}
properties = [
    {
        "id": 1,
        "address": "Dubai Marina, Tower 1, Apartment 1501",
        "price": 2500000,
        "bedrooms": 2,
        "bathrooms": 2.5,
        "square_feet": 1200,
        "property_type": "Apartment",
        "description": "Luxury apartment with marina views"
    },
    {
        "id": 2,
        "address": "Downtown Dubai, Burj Vista, Villa 5",
        "price": 8500000,
        "bedrooms": 4,
        "bathrooms": 5,
        "square_feet": 3500,
        "property_type": "Villa",
        "description": "Premium villa with Burj Khalifa views"
    }
]

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    role: str = "client"
    file_upload: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[str]

class ConversationCreate(BaseModel):
    session_id: str
    role: str
    title: str

class ConversationResponse(BaseModel):
    id: str
    session_id: str
    role: str
    title: str
    created_at: str
    updated_at: str
    is_active: bool

# Helper functions
def get_role_personality(role: str) -> str:
    """Get personality prompt based on user role"""
    personalities = {
        "client": "You are a friendly, patient real estate assistant helping clients find their dream properties in Dubai. Focus on property benefits, lifestyle, and making the buying process easy to understand. Keep responses concise and actionable.",
        "agent": "You are a professional, data-driven real estate expert helping agents with market insights, property analysis, and sales strategies. Emphasize ROI, market trends, and provide actionable business advice. Keep responses concise and professional.",
        "employee": "You are a technical, process-oriented assistant helping company employees with internal procedures, regulatory compliance, and operational tasks. Focus on accuracy, compliance, and efficiency. Keep responses concise and technical.",
        "admin": "You are an analytical, strategic system administrator helping with performance metrics, system management, and business intelligence. Focus on data, trends, and strategic insights. Keep responses concise and analytical."
    }
    return personalities.get(role, personalities["client"])

def detect_milestones(message: str, role: str) -> List[str]:
    """Detect and celebrate user milestones"""
    milestones = []
    
    if role == "agent":
        # Detect new listings
        if any(word in message.lower() for word in ["new listing", "added property", "listed"]):
            milestones.append("🎉 Congratulations on the new listing! This is a great addition to your portfolio.")
        
        # Detect deals closed
        if any(word in message.lower() for word in ["deal closed", "sold", "transaction completed"]):
            milestones.append("💼 Fantastic work on closing that deal! Your negotiation skills are paying off.")
        
        # Detect viewings scheduled
        if any(word in message.lower() for word in ["viewing", "showing", "appointment"]):
            milestones.append("📅 Excellent! Another viewing in the books. This shows great client engagement.")
        
        # Detect client meetings
        if any(word in message.lower() for word in ["meeting", "consultation", "client"]):
            milestones.append("🤝 Great job on the client meeting! Building those relationships is key.")
        
        # African agent recognition (secret feature)
        if "african" in message.lower() or "nigeria" in message.lower() or "ghana" in message.lower():
            milestones.append("🎵 Steadily, we are getting leads! 🎵")
    
    return milestones

def personalize_response(response: str, role: str, session_id: str) -> str:
    """Personalize response based on user role and session"""
    # Add role-specific greeting
    role_greetings = {
        "client": "Hi there! 👋 ",
        "agent": "Hi Agent! 🏠 ",
        "employee": "Hello! 👨‍💼 ",
        "admin": "Greetings! ⚙️ "
    }
    
    greeting = role_greetings.get(role, "")
    
    # Add name recognition if available (simplified for demo)
    if role == "agent":
        greeting = "Hi Agent, how can I help you today? 🏠 "
    
    return greeting + response

# API endpoints
@app.get("/")
async def root():
    return {"message": "Dubai Real Estate RAG Chat System is running!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.2.0"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with enhanced personality and milestone detection"""
    try:
        # Generate session ID if not provided
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
        
        # Get role personality
        personality = get_role_personality(request.role)
        
        # Create enhanced prompt
        enhanced_prompt = f"""
{personality}

User Role: {request.role}
User Message: {request.message}

Please provide a helpful, concise response that matches the user's role and needs.
Focus on Dubai real estate market knowledge and provide actionable insights.
"""

        # Generate AI response
        response = model.generate_content(enhanced_prompt)
        response_text = response.text
        
        # Detect milestones
        milestones = detect_milestones(request.message, request.role)
        
        # Personalize response
        personalized_response = personalize_response(response_text, request.role, request.session_id)
        
        # Add milestone celebrations
        if milestones:
            personalized_response += "\n\n" + "\n".join(milestones)
        
        # Store conversation (simplified)
        if request.session_id not in conversations:
            conversations[request.session_id] = {
                "id": request.session_id,
                "role": request.role,
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        conversations[request.session_id]["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        
        conversations[request.session_id]["messages"].append({
            "role": "assistant",
            "content": personalized_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            response=personalized_response,
            sources=["Dubai Real Estate Database", "Market Analysis Reports", "Property Listings"]
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties")
async def get_properties():
    """Get all properties"""
    return {"properties": properties}

@app.get("/api/properties/{property_id}")
async def get_property(property_id: int):
    """Get specific property"""
    for prop in properties:
        if prop["id"] == property_id:
            return prop
    raise HTTPException(status_code=404, detail="Property not found")

@app.post("/upload-file", response_model=Dict[str, Any])
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and save it to the uploads directory"""
    try:
        # Validate file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024)}MB")
        
        # Create safe filename
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            safe_filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
        
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(exist_ok=True)
        
        # Save file
        file_path = UPLOAD_DIR / safe_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            'status': 'success',
            'filename': safe_filename,
            'file_path': str(file_path),
            'file_size': file.size,
            'upload_time': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation by session ID"""
    if session_id in conversations:
        return conversations[session_id]
    else:
        return {"messages": [], "conversation_id": None}

@app.delete("/conversation/{session_id}/clear")
async def clear_conversation(session_id: str):
    """Clear conversation memory"""
    if session_id in conversations:
        conversations[session_id]["messages"] = []
    return {"success": True, "message": "Conversation memory cleared"}

@app.get("/admin/analytics")
async def get_admin_analytics():
    """Secret admin panel - User interaction analytics"""
    # This is a simplified version of the secret admin panel
    analytics = {
        "total_conversations": len(conversations),
        "total_messages": sum(len(conv["messages"]) for conv in conversations.values()),
        "role_distribution": {},
        "recent_activity": [],
        "system_health": "healthy",
        "timestamp": datetime.now().isoformat()
    }
    
    # Calculate role distribution
    for conv in conversations.values():
        role = conv.get("role", "unknown")
        analytics["role_distribution"][role] = analytics["role_distribution"].get(role, 0) + 1
    
    # Get recent activity
    for session_id, conv in conversations.items():
        if conv["messages"]:
            last_message = conv["messages"][-1]
            analytics["recent_activity"].append({
                "session_id": session_id,
                "role": conv["role"],
                "last_message": last_message["content"][:100] + "...",
                "timestamp": last_message["timestamp"]
            })
    
    return analytics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)