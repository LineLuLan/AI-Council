
from db import Base
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    stack_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    
    # --- NEW FIELDS ---
    display_name = Column(String, nullable=True)
    is_verified = Column(Boolean, default=True)
    # auto-set this when we create the row
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
  

class ChatRequest(BaseModel):
    prompt: str
    model: str = "gemma3:270m" # Default model


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None