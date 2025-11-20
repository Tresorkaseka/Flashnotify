"""
Script de lancement de l'API FastAPI
"""
import uvicorn
from api.main import app
import os

if __name__ == "__main__":
    port = int(os.environ.get("FASTAPI_PORT", 8000))
    host = os.environ.get("FASTAPI_HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )