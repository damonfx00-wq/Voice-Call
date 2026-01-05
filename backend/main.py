"""FastAPI Main Application - Real-time Voice Communication"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import asyncio
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Voice Call AI Assistant - Real-time",
    description="Real-time voice communication with AI",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client with NVIDIA API
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", "")
)

# Store active connections
active_connections: Dict[str, Dict] = {}

import datetime

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    session_id: Optional[str] = None  # Optional session ID to resume conversation
    user_id: Optional[str] = None  # Optional user identifier


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    session_id: str  # Return session ID for future requests


class TranscriptSaveRequest(BaseModel):
    transcript: List[Dict[str, Any]]
    duration: str
    phone_number: Optional[str] = None
    session_id: Optional[str] = None  # Link transcript to session



# API Routes
@app.post("/api/transcript/save")
async def save_transcript(request: TranscriptSaveRequest):
    """
    Save call transcript to a local directory
    """
    try:
        # Create transcripts directory if it doesn't exist
        transcripts_dir = os.path.join(os.getcwd(), "transcripts")
        if not os.path.exists(transcripts_dir):
            os.makedirs(transcripts_dir)
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        phone_suffix = f"_{request.phone_number}" if request.phone_number else ""
        filename = f"transcript_{timestamp}{phone_suffix}.txt"
        filepath = os.path.join(transcripts_dir, filename)
        
        # Format transcript content
        content = f"Call Transcript - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Duration: {request.duration}\n"
        if request.phone_number:
            content += f"Phone Number: {request.phone_number}\n"
        content += "-" * 40 + "\n\n"
        
        for item in request.transcript:
            speaker = "You" if item.get("sender") == "user" else "AI Assistant"
            content += f"[{item.get('timestamp')}] {speaker}: {item.get('text')}\n\n"
        
        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {"success": True, "message": f"Transcript saved to {filename}", "path": filepath}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Call AI Assistant API - Real-time",
        "version": "2.0.0",
        "status": "running",
        "features": ["websocket", "streaming", "real-time"]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "active_connections": len(active_connections)}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI assistant (HTTP endpoint with session management)
    """
    try:
        from app.agents.agent import IntelligentAgent
        
        # Create or resume agent with session
        agent = IntelligentAgent(
            api_key=os.getenv("NVIDIA_API_KEY"),
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        # Get response from agent
        response_text = agent.chat(request.message, stream=request.stream)
        
        # Return response with session ID
        return ChatResponse(
            response=response_text,
            success=True,
            session_id=agent.get_session_id()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def list_sessions(user_id: Optional[str] = None):
    """
    List all conversation sessions
    """
    try:
        from app.memory import ConversationMemory
        memory = ConversationMemory()
        sessions = memory.list_sessions(user_id)
        return {"success": True, "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get a specific session with full conversation history
    """
    try:
        from app.memory import ConversationMemory
        memory = ConversationMemory()
        session_data = memory.get_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "session": session_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a conversation session
    """
    try:
        from app.memory import ConversationMemory
        memory = ConversationMemory()
        success = memory.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "message": "Session deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice communication
    """
    await websocket.accept()
    connection_id = id(websocket)
    
    # Initialize connection state
    active_connections[connection_id] = {
        "websocket": websocket,
        "conversation_history": [],
        "is_speaking": False
    }
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to AI voice assistant",
            "connection_id": connection_id
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "transcript":
                # User speech transcript received
                user_message = data.get("message", "")
                is_final = data.get("is_final", False)
                
                if is_final and user_message.strip():
                    # Process final transcript
                    await process_user_message(connection_id, user_message, websocket)
                else:
                    # Send interim transcript acknowledgment
                    await websocket.send_json({
                        "type": "interim",
                        "transcript": user_message
                    })
            
            elif message_type == "interrupt":
                # User interrupted AI speech
                active_connections[connection_id]["is_speaking"] = False
                await websocket.send_json({
                    "type": "interrupted",
                    "message": "AI speech interrupted"
                })
            
            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        # Clean up connection
        if connection_id in active_connections:
            del active_connections[connection_id]
        print(f"Client {connection_id} disconnected")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        if connection_id in active_connections:
            del active_connections[connection_id]


async def process_user_message(connection_id: int, user_message: str, websocket: WebSocket):
    """Process user message and stream AI response"""
    try:
        conn_data = active_connections[connection_id]
        
        # Add user message to history
        conn_data["conversation_history"].append({
            "role": "user",
            "content": user_message
        })
        
        # Keep only last 10 messages
        if len(conn_data["conversation_history"]) > 10:
            conn_data["conversation_history"] = conn_data["conversation_history"][-10:]
        
        # System prompt
        system_message = {
            "role": "system",
            "content": """You are a helpful AI assistant in a live voice call. 
            - Keep responses brief and conversational (2-3 sentences max)
            - Speak naturally as if in a phone conversation
            - Be friendly and helpful
            - If asked about capabilities, mention you can help with questions and conversations"""
        }
        
        # Prepare messages
        messages = [system_message] + conn_data["conversation_history"]
        
        # Mark as speaking
        conn_data["is_speaking"] = True
        
        # Send start of response
        await websocket.send_json({
            "type": "response_start",
            "message": "AI is responding"
        })
        
        # Stream AI response
        full_response = ""
        stream = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.7,
            max_tokens=512,  # Shorter for faster responses
            stream=True
        )
        
        for chunk in stream:
            if not conn_data["is_speaking"]:
                # User interrupted
                break
            
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                
                # Send chunk to client
                await websocket.send_json({
                    "type": "response_chunk",
                    "content": content,
                    "full_response": full_response
                })
        
        # Send end of response
        await websocket.send_json({
            "type": "response_end",
            "full_response": full_response
        })
        
        # Add to conversation history
        conn_data["conversation_history"].append({
            "role": "assistant",
            "content": full_response
        })
        
        conn_data["is_speaking"] = False
        
    except Exception as e:
        print(f"Error processing message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
