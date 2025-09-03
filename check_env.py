"""
Simple script to check if environment variables are loading correctly
"""

import os
from dotenv import load_dotenv

print("🔍 Checking environment variable setup...\n")

# Try loading from different .env files
env_files = ['.env', '.env.local', '.env.production']

for env_file in env_files:
    if os.path.exists(env_file):
        print(f"✅ Found {env_file}")
        load_dotenv(env_file)
    else:
        print(f"❌ {env_file} not found")

print(f"\n📋 Environment Variables:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
print(f"SECRET_KEY: {'SET' if os.getenv('SECRET_KEY') else 'NOT SET'}")
print(f"VERCEL: {os.getenv('VERCEL', 'NOT SET')}")

# Check if DATABASE_URL is PostgreSQL
db_url = os.getenv('DATABASE_URL', '')
if db_url.startswith('postgresql'):
    print(f"\n✅ DATABASE_URL is correctly set to PostgreSQL")
    print(f"🔗 Host: {db_url.split('@')[1].split(':')[0] if '@' in db_url else 'Unknown'}")
elif db_url.startswith('sqlite'):
    print(f"\n❌ DATABASE_URL is set to SQLite instead of PostgreSQL")
else:
    print(f"\n❌ DATABASE_URL format is unrecognized or not set")

print(f"\n🎯 Current working directory: {os.getcwd()}")