"""
API FastAPI pour le système de notification
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationScheme
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import secrets

from models import db, User, Notification, PerformanceMetric
from core.notification_system import AcademicNotifier, EmergencyType, Priority

# Initialisation FastAPI
app = FastAPI(
    title="FlashNotify API",
    description="API moderne pour le système de notification académique",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sécurité
security = HTTPBearer()

# Mock d'authentification (à remplacer par un système réel)
API_KEYS = {
    "admin": secrets.token_hex(16),
    "user": secrets.token_hex(16)
}

def verify_token(credentials: HTTPAuthorizationScheme = Depends(security)):
    """Vérifie le token d'authentification"""
    if credentials.credentials not in API_KEYS.values():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Modèles Pydantic
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    prefers_email: bool = True

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    prefers_email: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    body: str
    emergency_type: Optional[str] = "académique"
    priority: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    emergency_type: str
    priority: str
    channels: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationRequest(BaseModel):
    user_email: str
    title: str
    body: str
    emergency_type: Optional[str] = "académique"

class StatsResponse(BaseModel):
    total_notifications: int
    total_users: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_notifications: List[Dict[str, Any]]

class PerformanceMetricsResponse(BaseModel):
    method_name: str
    duration: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Initialisation du notifier
notifier = AcademicNotifier()

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    # Ici on pourrait initialiser la base de données
    pass

# Routes API

@app.post("/api/v2/users/", response_model=UserResponse, tags=["Utilisateurs"])
async def create_user(user: UserCreate, token: str = Depends(verify_token)):
    """Crée un nouvel utilisateur"""
    try:
        db_user = User(
            name=user.name,
            email=user.email,
            phone=user.phone,
            prefers_email=user.prefers_email
