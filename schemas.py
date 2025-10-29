"""
Database Schemas for GestureAI

Each Pydantic model represents a collection in MongoDB. The collection name
is the lowercase of the class name (e.g., Gesture -> "gesture").
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Gesture(BaseModel):
    """Custom hand gesture definition"""
    name: str = Field(..., description="Human-friendly name of the gesture")
    intent: str = Field(..., description="What this gesture should do, e.g., 'next_slide'")
    app: Optional[str] = Field(None, description="Optional app or device this applies to")
    sensitivity: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Detection sensitivity")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Any extra config")


class VoiceCommand(BaseModel):
    """Custom voice phrase mapping"""
    phrase: str = Field(..., description="Natural language phrase to trigger")
    intent: str = Field(..., description="Action to execute, e.g., 'open_notes'")
    language: Optional[str] = Field("en", description="ISO language code")
    app: Optional[str] = Field(None, description="Target app or device")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Workflow(BaseModel):
    """Optional multi-step automation"""
    name: str
    steps: List[Dict[str, Any]] = Field(..., description="List of actions/intents with parameters")
    trigger: Optional[str] = Field(None, description="Gesture or voice phrase to start this workflow")
