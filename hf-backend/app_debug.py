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

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple inline route definitions as backup
from fastapi import APIRouter

# Define auth router directly if imports fail
auth_router = APIRouter()

@auth_router.post("/register")
def register_debug():
    return {"message": "Register endpoint reached", "status": "success"}

@auth_router.post("/login")
def login_debug():
    return {"message": "Login endpoint reached", "status": "success"}

# Include the auth router
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Try to import and add the todos router as well
try:
    import src.api.routes.todos
    todos_router = src.api.routes.todos.router
    app.include_router(todos_router, prefix="/todos", tags=["todos"])
    logger.info("Successfully imported and added todos router")
except ImportError as e:
    logger.error(f"Failed to import todos router: {e}")
    
    # Create a simple todos router as fallback
    todos_router = APIRouter()
    
    @todos_router.get("/")
    def todos_fallback():
        return {"message": "Todos endpoint - fallback", "error": str(e)}
    
    app.include_router(todos_router, prefix="/todos", tags=["todos"])

@app.get("/")
def read_root():
    return {"message": "Todo Management API running on Hugging Face Spaces", "status": "operational", "python_path": sys.path}

# Try to set up database if possible
try:
    from sqlmodel import SQLModel
    from src.database.database import engine

    @app.on_event("startup")
    def on_startup():
        try:
            # Create database tables
            logger.info("Creating database tables...")
            SQLModel.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            # Don't crash the app if database initialization fails
            pass
except ImportError as e:
    logger.error(f"Failed to import database components: {e}")

from fastapi.responses import JSONResponse

# Error handling
@app.exception_handler(404)
async def not_found_error(request, exc):
    logger.error(f"404 error for path: {request.url.path}")
    return JSONResponse(status_code=404, content={"detail": f"Resource not found: {request.url.path}"})

@app.exception_handler(500)
async def internal_error(request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.exception_handler(TypeError)
async def type_error_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": f"Type error: {str(exc)}"})

# For Hugging Face Spaces compatibility
def start_server():
    port = int(os.getenv("PORT", 7860))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_server()