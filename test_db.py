"""
Test script to verify PostgreSQL connection
Run this before deploying to ensure everything works
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env.local first, then .env
load_dotenv('.env.local')
load_dotenv('.env')
load_dotenv()

print(f"🔧 Environment files loaded")
print(f"📍 DATABASE_URL set: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_connection():
    """Test the database connection"""
    try:
        # Import after environment variables are loaded
        from database import engine
        from sqlalchemy import text
        
        print("🔍 Testing PostgreSQL connection...")
        db_url = os.getenv('DATABASE_URL', 'Not set')
        print(f"📍 Database URL: {db_url[:50]}{'...' if len(db_url) > 50 else ''}")
        
        if not db_url.startswith('postgresql'):
            print("❌ DATABASE_URL is not set to PostgreSQL!")
            print(f"Current URL: {db_url}")
            return False
        
        with engine.connect() as connection:
            # Test basic connection
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"🐘 PostgreSQL version: {version}")
            
            # Test database name
            result = connection.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]
            print(f"📊 Connected to database: {db_name}")
            
            # Test SSL connection
            result = connection.execute(text("SHOW ssl;"))
            ssl_status = result.fetchone()[0]
            print(f"🔒 SSL status: {ssl_status}")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure DATABASE_URL is set correctly in .env file")
        return False

def test_crud_operations():
    """Test basic CRUD operations"""
    try:
        from database import SessionLocal
        from models import User, Note
        from passlib.context import CryptContext
        
        print("\n🧪 Testing CRUD operations...")
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        db = SessionLocal()
        
        # Test user creation
        test_username = "test_user_vercel"
        
        # Clean up any existing test user
        existing_user = db.query(User).filter(User.username == test_username).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        # Create test user
        hashed_password = pwd_context.hash("test_password")
        test_user = User(
            username=test_username,
            email="test@example.com",
            hashed_password=hashed_password
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created test user: {test_user.username} (ID: {test_user.id})")
        
        # Test note creation
        test_note = Note(
            title="Test Note for Vercel",
            content="This is a test note to verify PostgreSQL connection works.",
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(test_note)
        db.commit()
        db.refresh(test_note)
        print(f"✅ Created test note: {test_note.title} (ID: {test_note.id})")
        
        # Test reading
        notes = db.query(Note).filter(Note.owner_id == test_user.id).all()
        print(f"✅ Retrieved {len(notes)} notes for user")
        
        # Clean up
        db.delete(test_note)
        db.delete(test_user)
        db.commit()
        print("✅ Cleaned up test data")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ CRUD test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing PostgreSQL setup for Vercel deployment...\n")
    
    # Test connection
    connection_ok = test_connection()
    
    if connection_ok:
        # Test CRUD operations
        crud_ok = test_crud_operations()
        
        if crud_ok:
            print("\n🎉 All tests passed! Your app is ready for Vercel deployment.")
            print("\n📋 Next steps:")
            print("1. Run: vercel --prod")
            print("2. Set environment variables in Vercel dashboard:")
            print("   - DATABASE_URL: your_postgresql_url")
            print("   - SECRET_KEY: your_secure_secret_key")
            print("   - VERCEL: true")
        else:
            print("\n❌ CRUD tests failed. Please check your database setup.")
    else:
        print("\n❌ Connection test failed. Please check your DATABASE_URL.")