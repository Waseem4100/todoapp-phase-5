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

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Todo Management API", 
    version="1.0.0"
)
app.router.redirect_slashes = False  # Disable automatic slash redirects
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
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel

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

# Todo models
class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(TodoBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

# Request models for login
class LoginRequest(BaseModel):
    email: str
    password: str

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

# Mock todo storage (in-memory for now)
mock_todos = []

def get_todo_by_id(todo_id: str):
    for todo in mock_todos:
        if todo["id"] == todo_id:
            return todo
    return None

def get_todos_for_user(user_id: str):
    return [todo for todo in mock_todos if todo["owner_id"] == user_id]

def create_todo_for_user(user_id: str, todo_data: TodoCreate):
    todo = {
        "id": str(uuid.uuid4()),
        "title": todo_data.title,
        "description": todo_data.description,
        "completed": todo_data.completed,
        "owner_id": user_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    mock_todos.append(todo)
    return todo

def update_todo(todo_id: str, todo_update: TodoUpdate):
    for i, todo in enumerate(mock_todos):
        if todo["id"] == todo_id:
            updated_data = todo_update.dict(exclude_unset=True)
            mock_todos[i].update(updated_data)
            mock_todos[i]["updated_at"] = datetime.utcnow()
            return mock_todos[i]
    return None

def delete_todo(todo_id: str):
    global mock_todos
    todo_to_remove = None
    for todo in mock_todos:
        if todo["id"] == todo_id:
            todo_to_remove = todo
            break
    
    if todo_to_remove:
        mock_todos.remove(todo_to_remove)
        return True
    return False

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
        raise HTTPException(status_code=400, detail=str(e))

@auth_router.post("/login")
def login(login_request: LoginRequest):
    """
    Login user and return access token
    """
    user = authenticate_user_mock(login_request.email, login_request.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Mock token creation - in real implementation, use your JWT logic
    import jwt
    import os
    
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

# Create todos router and define routes directly
# Disable redirect slashes to prevent 307 redirects
todos_router = APIRouter()

@todos_router.get("/", response_model=list[Todo])
def get_todos(skip: int = 0, limit: int = 100):
    """
    Get all todos (mock implementation)
    """
    # In a real implementation, this would filter by authenticated user
    return mock_todos[skip:skip+limit]

@todos_router.post("/", response_model=Todo, status_code=201)
def create_todo(todo_data: TodoCreate):
    """
    Create a new todo (mock implementation)
    """
    # In a real implementation, this would associate with authenticated user
    user_id = "mock_user_id"  # This would come from authentication in real implementation
    todo = create_todo_for_user(user_id, todo_data)
    return todo

@todos_router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: str):
    """
    Get a specific todo by ID
    """
    todo = get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@todos_router.put("/{todo_id}", response_model=Todo)
def update_todo_endpoint(todo_id: str, todo_update: TodoUpdate):
    """
    Update a specific todo
    """
    todo = update_todo(todo_id, todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@todos_router.delete("/{todo_id}")
def delete_todo_endpoint(todo_id: str):
    """
    Delete a specific todo
    """
    success = delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted successfully"}

logger.info("Todos routes defined successfully")

# Include API routes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(todos_router, prefix="/todos", tags=["todos"])
logger.info("Routers included successfully")

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