from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from mangum import Mangum
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import SessionLocal, engine, Base
from models import User, Note
from schemas import (
    UserCreate, UserResponse, NoteCreate, NoteResponse, 
    NoteUpdate, ShareNoteRequest, LoginRequest, Token,
    PublicNoteResponse
)

# Check if running on Vercel
IS_VERCEL = os.getenv("VERCEL") == "1"

# Initialize database tables safely
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    # Log error but don't crash the application
    print(f"Database initialization warning: {e}")

# Create FastAPI app with conditional configuration for Vercel
try:
    app = FastAPI(
        title="Notes API", 
        description="A simple notes app with sharing functionality",
        root_path="/api" if IS_VERCEL else ""
    )
except Exception as e:
    print(f"FastAPI initialization error: {e}")
    # Create a minimal app as fallback
    app = FastAPI(title="Notes API")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer()

# CORS middleware with error handling
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://namekart-frontend-w3gv.vercel.app",
            "https://*.vercel.app",  # Allow all Vercel app domains
            "http://localhost:5173",
            "http://localhost:3000", 
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
except Exception as e:
    print(f"CORS middleware setup error: {e}")

# Global exception handler for better error reporting
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Database dependency with error handling
def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        print(f"Database connection error: {e}")
        if db:
            db.rollback()
        raise HTTPException(status_code=503, detail="Database connection failed")
    finally:
        if db:
            db.close()

# Auth helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Routes
@app.get("/")
def read_root():
    try:
        return {
            "message": "Namekart Backend is running",
            "status": "active",
            "api": "Notes API",
            "version": "1.0.0",
            "environment": "Vercel" if IS_VERCEL else "Local",
            "api_prefix": "/api" if IS_VERCEL else "",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "message": "Namekart Backend - Basic Mode",
            "status": "active",
            "error": str(e)
        }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": "Vercel" if IS_VERCEL else "Local",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(id=db_user.id, username=db_user.username, email=db_user.email)

@app.post("/auth/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(id=current_user.id, username=current_user.username, email=current_user.email)

@app.get("/notes", response_model=List[NoteResponse])
def get_user_notes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.owner_id == current_user.id).all()
    return notes

@app.post("/notes", response_model=NoteResponse)
def create_note(note: NoteCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_note = Note(
        title=note.title,
        content=note.content,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns the note or if it's shared
    if note.owner_id != current_user.id and not note.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to view this note")
    
    return note

@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_update: NoteUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content
    
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(note)
    db.commit()
    return {"message": "Note deleted successfully"}

@app.post("/notes/{note_id}/share")
def share_note(note_id: int, share_request: ShareNoteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    note.is_public = share_request.is_public
    note.updated_at = datetime.utcnow()
    db.commit()
    
    share_url = f"/shared/{note.id}" if share_request.is_public else None
    return {"message": "Note sharing updated", "share_url": share_url, "is_public": note.is_public}

@app.get("/public-notes", response_model=List[PublicNoteResponse])
def get_public_notes(db: Session = Depends(get_db)):
    """Get all public notes from all users with owner information"""
    notes = db.query(Note, User.username).join(User, Note.owner_id == User.id).filter(Note.is_public == True).order_by(Note.updated_at.desc()).all()
    
    result = []
    for note, owner_username in notes:
        result.append(PublicNoteResponse(
            id=note.id,
            title=note.title,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at,
            is_public=note.is_public,
            owner_id=note.owner_id,
            owner_username=owner_username
        ))
    
    return result

@app.get("/shared/{note_id}", response_model=PublicNoteResponse)
def get_shared_note(note_id: int, db: Session = Depends(get_db)):
    note_with_author = db.query(Note, User.username).join(User, Note.owner_id == User.id).filter(Note.id == note_id, Note.is_public == True).first()
    if not note_with_author:
        raise HTTPException(status_code=404, detail="Shared note not found")
    
    note, owner_username = note_with_author
    return PublicNoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
        is_public=note.is_public,
        owner_id=note.owner_id,
        owner_username=owner_username
    )

# Create Mangum handler for Vercel serverless deployment
handler = Mangum(app, lifespan="off")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)