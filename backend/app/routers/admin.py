# path: backend/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from app.models.base import get_db
from app.models.user import User, QuerySession, Dataset
from app.core.security import require_admin
from app.rag.vectorstore import add_documents

router = APIRouter()


class DatasetCreate(BaseModel):
    title: str
    slug: str
    difficulty: str
    tags: str
    problem_text: str
    solution_code: str
    time_complexity: str = "O(n)"
    space_complexity: str = "O(n)"


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar()
    total_queries = db.query(func.count(QuerySession.id)).scalar()
    total_datasets = db.query(func.count(Dataset.id)).scalar()

    # Queries per day for last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily = (
        db.query(
            func.date(QuerySession.created_at).label("date"),
            func.count(QuerySession.id).label("count"),
        )
        .filter(QuerySession.created_at >= seven_days_ago)
        .group_by(func.date(QuerySession.created_at))
        .all()
    )

    modality_breakdown = (
        db.query(QuerySession.modality, func.count(QuerySession.id))
        .group_by(QuerySession.modality)
        .all()
    )

    return {
        "total_users": total_users,
        "total_queries": total_queries,
        "total_datasets": total_datasets,
        "daily_queries": [{"date": str(d.date), "count": d.count} for d in daily],
        "modality_breakdown": {m: c for m, c in modality_breakdown},
    }


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db), _=Depends(require_admin), skip: int = 0, limit: int = 50
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "is_active": u.is_active}
        for u in users
    ]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in data.items():
        if hasattr(user, k) and k not in ("id", "hashed_password"):
            setattr(user, k, v)
    db.commit()
    return {"status": "updated"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"status": "deleted"}


@router.get("/datasets")
async def list_datasets(db: Session = Depends(get_db), _=Depends(require_admin)):
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "difficulty": d.difficulty,
            "tags": d.tags,
            "is_embedded": d.is_embedded,
        }
        for d in datasets
    ]


@router.post("/datasets")
async def create_dataset(
    data: DatasetCreate, db: Session = Depends(get_db), _=Depends(require_admin)
):
    import uuid
    existing = db.query(Dataset).filter(Dataset.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")

    dataset = Dataset(id=str(uuid.uuid4()), **data.dict())
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Embed immediately
    add_documents([{**data.dict(), "id": dataset.id}])
    dataset.is_embedded = True
    db.commit()

    return {"status": "created", "id": dataset.id}


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str, db: Session = Depends(get_db), _=Depends(require_admin)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(dataset)
    db.commit()
    return {"status": "deleted"}