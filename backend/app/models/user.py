# path: backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import uuid
from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String, default="user")   # "user" | "admin"
    is_active = Column(Boolean, default=True)
    google_id = Column(String, nullable=True, unique=True)
    api_key = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuerySession(Base):
    __tablename__ = "query_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    modality = Column(String, default="text")   # text | voice | image
    dsa_score = Column(Integer, nullable=True)
    is_favorite = Column(Boolean, default=False)
    share_token = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    difficulty = Column(String)   # Easy | Medium | Hard
    tags = Column(String)         # comma-separated: "array,hash-map"
    problem_text = Column(Text)
    solution_code = Column(Text)
    time_complexity = Column(String)
    space_complexity = Column(String)
    is_embedded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)