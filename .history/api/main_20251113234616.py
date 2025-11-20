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
        )
        db.session.add(db_user)
        db.session.commit()
        db.session.refresh(db_user)
        return db_user
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v2/users/", response_model=List[UserResponse], tags=["Utilisateurs"])
async def get_users(token: str = Depends(verify_token), skip: int = 0, limit: int = 100):
    """Récupère tous les utilisateurs"""
    users = User.query.offset(skip).limit(limit).all()
    return users

@app.get("/api/v2/users/{user_id}/", response_model=UserResponse, tags=["Utilisateurs"])
async def get_user(user_id: int, token: str = Depends(verify_token)):
    """Récupère un utilisateur par ID"""
    user = User.query.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@app.post("/api/v2/notifications/", response_model=Dict[str, Any], tags=["Notifications"])
async def send_notification(notification: NotificationRequest, token: str = Depends(verify_token)):
    """Envoie une notification à un utilisateur"""
    try:
        # Recherche de l'utilisateur par email
        user = User.query.filter_by(email=notification.user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Validation du type d'urgence
        emergency_type = EmergencyType.ACADEMIC
        for et in EmergencyType:
            if et.value == notification.emergency_type:
                emergency_type = et
                break
        
        # Envoi de la notification
        user_dict = user.to_dict()
        notification_data = notifier.notify(
            user_dict, 
            notification.title, 
            notification.body, 
            emergency_type
        )
        
        # Sauvegarde en base de données
        priority_name = notification_data.get('priority', 'MEDIUM')
        channels = ', '.join([r['channel'] for r in notification_data['results'] if r])
        
        db_notification = Notification(
            user_id=user.id,
            title=notification.title,
            body=notification.body,
            emergency_type=emergency_type.value,
            priority=priority_name,
            channels=channels,
            status='sent'
        )
        db.session.add(db_notification)
        db.session.commit()
        
        return {
            "message": "Notification envoyée avec succès",
            "notification_data": notification_data,
            "notification_id": db_notification.id
        }
        
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/notifications/", response_model=List[NotificationResponse], tags=["Notifications"])
async def get_notifications(
    token: str = Depends(verify_token),
    skip: int = 0, 
    limit: int = 100,
    emergency_type: Optional[str] = None,
    priority: Optional[str] = None
):
    """Récupère les notifications avec filtres optionnels"""
    query = Notification.query
    
    if emergency_type:
        query = query.filter_by(emergency_type=emergency_type)
    
    if priority:
        query = query.filter_by(_priority=priority)
    
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications

@app.get("/api/v2/notifications/{notification_id}/", response_model=NotificationResponse, tags=["Notifications"])
async def get_notification(notification_id: int, token: str = Depends(verify_token)):
    """Récupère une notification par ID"""
    notification = Notification.query.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    return notification

@app.get("/api/v2/stats/", response_model=StatsResponse, tags=["Statistiques"])
async def get_stats(token: str = Depends(verify_token)):
    """Récupère les statistiques du système"""
    stats = {
        'total_notifications': Notification.query.count(),
        'total_users': User.query.count(),
        'by_type': {},
        'by_priority': {},
        'recent_notifications': []
    }
    
    for et in EmergencyType:
        count = Notification.query.filter_by(emergency_type=et.value).count()
        stats['by_type'][et.value] = count
    
    for p in Priority:
        count = Notification.query.filter_by(_priority=p.name).count()
        stats['by_priority'][p.name] = count
    
    recent = Notification.query.order_by(Notification.created_at.desc()).limit(10).all()
    stats['recent_notifications'] = [n.to_dict() for n in recent]
    
    return stats

@app.get("/api/v2/performance/", response_model=List[PerformanceMetricsResponse], tags=["Performance"])
async def get_performance_metrics(token: str = Depends(verify_token)):
    """Récupère les métriques de performance"""
    metrics = PerformanceMetric.query.order_by(PerformanceMetric.timestamp.desc()).limit(100).all()
    return metrics

@app.get("/api/v2/health/", tags=["Santé"])
async def health_check():
    """Vérification de santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "notification_system": "active"
        }
    }

# Personnalisation de la documentation OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="FlashNotify API",
        version="2.0.0",
        description="API moderne pour le système de notification académique avec FastAPI",
        routes=app.routes,
    )
    
    # Ajout de la sécurité à tous les endpoints
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Application de la sécurité à tous les endpoints sauf health check
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if method.get("operationId") != "health_check_api_v2_health_get":
                method["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi