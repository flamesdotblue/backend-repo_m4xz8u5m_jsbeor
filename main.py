import os
from typing import List, Optional, Any, Dict
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Gesture, VoiceCommand, Workflow  # ensure schemas are defined

app = FastAPI(title="GestureAI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        try:
            return ObjectId(str(v))
        except Exception as e:
            raise ValueError("Invalid ObjectId") from e


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {**doc}
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    # Convert datetimes to isoformat if present
    for k, v in list(out.items()):
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
    return out


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Configured"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# Domain endpoints
@app.post("/gestures")
def create_gesture(gesture: Gesture):
    from database import create_document
    try:
        inserted_id = create_document("gesture", gesture)
        return {"id": inserted_id, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gestures")
def list_gestures(limit: Optional[int] = 20):
    from database import get_documents
    try:
        docs = get_documents("gesture", limit=limit)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voices")
def create_voice(cmd: VoiceCommand):
    from database import create_document
    try:
        inserted_id = create_document("voicecommand", cmd)
        return {"id": inserted_id, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/voices")
def list_voices(limit: Optional[int] = 20):
    from database import get_documents
    try:
        docs = get_documents("voicecommand", limit=limit)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suggestions")
def suggestions():
    """Return lightweight adaptive suggestions based on recent items."""
    try:
        from database import get_documents
        recent_gestures = get_documents("gesture", limit=3)
        recent_voices = get_documents("voicecommand", limit=3)
    except Exception:
        recent_gestures = []
        recent_voices = []

    base = [
        {"title": "Wave to silence notifications", "category": "Focus"},
        {"title": "Pinch to zoom in any app", "category": "Navigation"},
        {"title": "Say \"open notes\" to start typing", "category": "Voice"},
    ]

    dynamic = []
    for g in recent_gestures:
        dynamic.append({
            "title": f"Use '{g.get('name', 'gesture')}' to trigger {g.get('intent', 'an action')}",
            "category": g.get('app') or "Custom",
        })
    for v in recent_voices:
        dynamic.append({
            "title": f"Say '{v.get('phrase', 'command')}' to {v.get('intent', 'do something')}",
            "category": v.get('app') or "Custom",
        })

    return {"suggestions": (dynamic or base)[:6]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
