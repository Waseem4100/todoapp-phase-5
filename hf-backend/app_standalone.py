import sys
import os

# Add the project root and src directory to the Python path to allow proper imports
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

# Insert paths at the beginning to ensure they're found first
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Todo Management API", version="1.0.0")
logger.info("FastAPI app initialized")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the User models directly to avoid import issues
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    password_confirm: str

class UserRead(UserBase):
    id: str
    created_at: datetime

# Define the AuthService logic directly to avoid import issues
def authenticate_user_mock(email: str, password: str):
    """Mock authentication - replace with real logic"""
    # This is a placeholder - implement real authentication logic
    # that connects to your database
    if email and password:  # Simplified check
        # Return mock user data
        return {
            "id": str(uuid.uuid4()),
            "email": email,
            "first_name": "Test",
            "last_name": "User",
            "created_at": datetime.utcnow()
        }
    return None

def register_user_mock(user_data: UserCreate):
    """Mock registration - replace with real logic"""
    # This is a placeholder - implement real registration logic
    # that connects to your database
    if user_data.password != user_data.password_confirm:
        raise ValueError("Passwords do not match")
    
    # Return mock user data
    return {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "created_at": datetime.utcnow()
    }

from fastapi import APIRouter

# Create auth router and define routes directly
auth_router = APIRouter()

@auth_router.post("/register", response_model=UserRead, status_code=201)
def register(user_data: UserCreate):
    """
    Register a new user
    """
    try:
        user = register_user_mock(user_data)
        return user
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

@auth_router.post("/login")
def login(email: str, password: str):
    """
    Login user and return access token
    """
    user = authenticate_user_mock(email, password)

    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Mock token creation - in real implementation, use your JWT logic
    import jwt
    import os
    from datetime import timedelta
    
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    access_token = create_access_token(data={"sub": user["id"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

logger.info("Auth routes defined successfully")

# Include API routes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
logger.info("Auth router included successfully")

# Add a route to check what routes are registered
@app.get("/routes")
def list_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

@app.get("/")
def read_root():
    return {"message": "Todo Management API running on Hugging Face Spaces", "status": "operational"}

from fastapi.responses import JSONResponse

# Error handling
@app.exception_handler(404)
async def not_found_error(request, exc):
    logger.error(f"404 error for path: {request.url.path}")
    return JSONResponse(status_code=404, content={"detail": f"Resource not found: {request.url.path}"})

# For Hugging Face Spaces compatibility
def start_server():
    port = int(os.getenv("PORT", 7860))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_server()