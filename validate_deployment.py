#!/usr/bin/env python3
"""
Vercel Deployment Validation Script
This script helps validate that your backend is properly configured for Vercel deployment.
"""

import os
import sys
import importlib.util

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not available, checking system environment only")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

def check_file_exists(file_path, description):
    """Check if a file exists and print result"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (NOT FOUND)")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    required_packages = [
        ('fastapi', 'fastapi'),
        ('sqlalchemy', 'sqlalchemy'), 
        ('pydantic', 'pydantic'),
        ('jose', 'jose'),
        ('passlib', 'passlib'),
        ('bcrypt', 'bcrypt'),
        ('python_multipart', 'multipart'),
        ('python-dotenv', 'dotenv'),
        ('psycopg2', 'psycopg2'),
        ('mangum', 'mangum')
    ]
    
    print("\n📦 Checking Dependencies:")
    all_good = True
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}: Available")
        except ImportError:
            print(f"❌ {package_name}: NOT AVAILABLE")
            all_good = False
    
    return all_good

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\n🔧 Checking Environment Variables:")
    
    # Check if .env file exists
    env_file_exists = os.path.exists('.env')
    if env_file_exists:
        print("✅ .env file: Found")
    else:
        print("⚠️  .env file: Not found (using system environment only)")
    
    # For local development
    env_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL')
    }
    
    for var_name, var_value in env_vars.items():
        if var_value:
            # Show partial value for security
            masked_value = var_value[:8] + "***" if len(var_value) > 8 else "***"
            print(f"✅ {var_name}: Set ({masked_value})")
        else:
            print(f"⚠️  {var_name}: Not set (will use default)")

def check_vercel_config():
    """Check Vercel configuration"""
    print("\n🚀 Checking Vercel Configuration:")
    
    # Check vercel.json
    vercel_config_valid = check_file_exists('vercel.json', 'Vercel config')
    
    if vercel_config_valid:
        try:
            import json
            with open('vercel.json', 'r') as f:
                config = json.load(f)
                
            # Check required sections
            if 'builds' in config:
                print("✅ Vercel builds configuration: Present")
            else:
                print("❌ Vercel builds configuration: Missing")
                
            if 'routes' in config:
                print("✅ Vercel routes configuration: Present")
            else:
                print("❌ Vercel routes configuration: Missing")
                
        except json.JSONDecodeError:
            print("❌ Vercel config: Invalid JSON format")
    
    # Check .vercelignore
    check_file_exists('.vercelignore', 'Vercel ignore file')

def main():
    """Main validation function"""
    print("🔍 Namekart Backend - Vercel Deployment Validation")
    print("=" * 50)
    
    # Check core files
    print("\n📄 Checking Core Files:")
    files_to_check = [
        ('main.py', 'Main FastAPI application'),
        ('requirements.txt', 'Python dependencies'),
        ('database.py', 'Database configuration'),
        ('models.py', 'Database models'),
        ('schemas.py', 'Pydantic schemas')
    ]
    
    all_files_present = True
    for filename, description in files_to_check:
        if not check_file_exists(filename, description):
            all_files_present = False
    
    # Check dependencies
    deps_available = check_dependencies()
    
    # Check environment variables
    check_environment_variables()
    
    # Check Vercel configuration
    check_vercel_config()
    
    # Final assessment
    print("\n" + "=" * 50)
    
    # Check critical issues vs warnings
    critical_issues = not all_files_present
    
    # Dependencies are critical only if core ones are missing
    core_deps = ['fastapi', 'sqlalchemy', 'pydantic', 'mangum']
    missing_core_deps = False
    
    for package_name, import_name in [('fastapi', 'fastapi'), ('sqlalchemy', 'sqlalchemy'), ('pydantic', 'pydantic'), ('mangum', 'mangum')]:
        try:
            __import__(import_name)
        except ImportError:
            missing_core_deps = True
            break
    
    if critical_issues or missing_core_deps:
        print("❌ Backend needs attention before deployment")
        print("Please fix the critical issues listed above")
        if missing_core_deps:
            print("\n🚨 Critical: Install missing core dependencies with:")
            print("pip install -r requirements.txt")
    else:
        print("🎉 Backend is ready for Vercel deployment!")
        print("\n📄 Note: Environment variable warnings are normal for local validation.")
        print("Set these in your Vercel dashboard when deploying.")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Connect your GitHub repository to Vercel")
        print("3. Set environment variables in Vercel dashboard:")
        print("   - SECRET_KEY")
        print("   - DATABASE_URL")
        print("   - VERCEL=1")
        print("4. Deploy!")

if __name__ == "__main__":
    main()