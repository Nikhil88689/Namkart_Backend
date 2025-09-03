"""
Database initialization script for PostgreSQL
Run this script to create the required tables in your Aiven PostgreSQL database
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env.local first, then .env
load_dotenv('.env.local')
load_dotenv('.env')
load_dotenv()

print(f"🔧 Environment files loaded")
print(f"📍 DATABASE_URL set: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")

# Add the parent directory to the path to import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, engine
from models import User, Note

def init_database():
    """Initialize the database with required tables"""
    try:
        print("Creating database tables...")
        
        # Import after environment variables are loaded
        from database import Base, engine
        from models import User, Note
        
        # Check if we're using PostgreSQL
        db_url = os.getenv('DATABASE_URL', 'Not set')
        if not db_url.startswith('postgresql'):
            print(f"❌ DATABASE_URL is not set to PostgreSQL!")
            print(f"Current URL: {db_url}")
            return False
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print("Tables created: users, notes")
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
            
        return True
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("💡 Make sure DATABASE_URL is set correctly in .env file")
        return False

def check_tables():
    """Check if tables exist and show their structure"""
    try:
        with engine.connect() as connection:
            # Check if tables exist
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📋 Existing tables: {', '.join(tables) if tables else 'None'}")
            
            for table in tables:
                print(f"\n🔍 Structure of table '{table}':")
                result = connection.execute(text(f"""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position
                """))
                
                for row in result.fetchall():
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    print(f"  - {row[0]}: {row[1]} ({nullable})")
                    
    except Exception as e:
        print(f"❌ Error checking tables: {e}")

if __name__ == "__main__":
    print("🚀 Initializing PostgreSQL database for Notes App...")
    print(f"📍 Database URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}{'...' if len(os.getenv('DATABASE_URL', '')) > 50 else ''}")
    
    success = init_database()
    if success:
        check_tables()
        print("\n✅ Database initialization completed!")
        print("You can now deploy your app to Vercel.")
    else:
        print("\n❌ Database initialization failed!")
        print("Please check your DATABASE_URL and try again.")
        sys.exit(1)