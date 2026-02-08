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

# Let's try a different approach - directly import and use the routes
try:
    logger.info("Attempting to import auth routes directly...")
    
    # Import the dependencies needed for the auth routes
    from fastapi import APIRouter, Depends, HTTPException
    from sqlmodel import Session
    from src.database.database import get_session
    from src.models.user import UserCreate, UserRead
    from src.services.auth_service import AuthService
    from src.api.deps import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    from datetime import timedelta
    
    # Create auth router and define routes directly
    auth_router = APIRouter()

    @auth_router.post("/register", response_model=UserRead, status_code=201)
    def register(user_data: UserCreate, session: Session = Depends(get_session)):
        """
        Register a new user
        """
        try:
            user = AuthService.register_user(session, user_data)
            return user
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @auth_router.post("/login")
    def login(email: str, password: str, session: Session = Depends(get_session)):
        """
        Login user and return access token
        """
        user = AuthService.authenticate_user(session, email, password)

        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at
            }
        }

    logger.info("Auth routes defined successfully")

    # Include API routes
    app.include_router(auth_router, prefix="/auth", tags=["authentication"])
    logger.info("Auth router included successfully")

except Exception as e:
    logger.error(f"Error defining auth routes: {e}")
    logger.error(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
    
    # Store the error message in a variable accessible to the functions
    error_msg = str(e)
    
    # Fallback: create simple routes
    from fastapi import APIRouter
    auth_router = APIRouter()
    
    @auth_router.post("/register")
    def register_fallback():
        return {"error": f"Register failed: {error_msg}", "status": "error"}
        
    @auth_router.post("/login")
    def login_fallback():
        return {"error": f"Login failed: {error_msg}", "status": "error"}
    
    app.include_router(auth_router, prefix="/auth", tags=["authentication"])

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