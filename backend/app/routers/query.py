# path: backend/app/routers/query.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import openai, base64, io, json, logging

from app.models.base import get_db
from app.models.user import User, QuerySession
from app.core.security import get_current_user
from app.core.config import settings
from app.agents.crew import run_crew_streaming

router = APIRouter()
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    query: str
    user_code: Optional[str] = None
    mode: str = "solve"   # solve | debug | optimize | all
    session_id: Optional[str] = None


@router.post("/text")
async def query_text(
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    async def generate():
        full_response = []
        async for chunk in run_crew_streaming(req.dict(), req.session_id or "direct"):
            full_response.append(chunk)
            yield json.dumps(chunk) + "\n"

        # Save session
        try:
            final = next((c for c in full_response if c.get("type") == "final"), {})
            session = QuerySession(
                user_id=current_user.id,
                query_text=req.query,
                response_text=final.get("content", ""),
                modality="text",
                dsa_score=final.get("dsa_score"),
            )
            db.add(session)
            db.commit()
        except Exception as e:
            logger.error(f"Session save error: {e}")

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.post("/voice")
async def query_voice(
    audio: UploadFile = File(...),
    mode: str = Form("solve"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Transcribe audio via Whisper then run text query pipeline."""
    if not settings.OPENAI_API_KEY.startswith("sk-"):
        raise HTTPException(status_code=400, detail="OpenAI API key required for voice")

    audio_bytes = await audio.read()
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.webm", io.BytesIO(audio_bytes), "audio/webm"),
        )
        query_text = transcription.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper error: {e}")

    async def generate():
        yield json.dumps({"type": "transcription", "text": query_text}) + "\n"
        async for chunk in run_crew_streaming({"query": query_text, "mode": mode}, "voice"):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.post("/image")
async def query_image(
    image: UploadFile = File(...),
    mode: str = Form("solve"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Extract problem text from image via GPT-4V then solve."""
    image_bytes = await image.read()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    media_type = image.content_type or "image/jpeg"

    if not settings.OPENAI_API_KEY.startswith("sk-"):
        raise HTTPException(status_code=400, detail="OpenAI API key required for image input")

    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{b64_image}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Extract the complete coding problem from this image. "
                                "Return only the problem statement, constraints, and examples. "
                                "No extra commentary."
                            ),
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        extracted_text = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision error: {e}")

    async def generate():
        yield json.dumps({"type": "ocr_result", "text": extracted_text}) + "\n"
        async for chunk in run_crew_streaming({"query": extracted_text, "mode": mode}, "image"):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
):
    sessions = (
        db.query(QuerySession)
        .filter(QuerySession.user_id == current_user.id)
        .order_by(QuerySession.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "query": s.query_text[:100],
            "modality": s.modality,
            "dsa_score": s.dsa_score,
            "is_favorite": s.is_favorite,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.post("/favorite/{session_id}")
async def toggle_favorite(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(QuerySession).filter(
        QuerySession.id == session_id,
        QuerySession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_favorite = not session.is_favorite
    db.commit()
    return {"is_favorite": session.is_favorite}