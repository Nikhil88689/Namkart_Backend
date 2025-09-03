#!/usr/bin/env python3
"""
Simple test script to verify the Vercel handler works correctly
"""

import os
import sys

# Set Vercel environment variable for testing
os.environ["VERCEL"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

try:
    # Import the handler
    from main import handler, app
    
    print("✅ Handler imported successfully")
    print("✅ App created successfully")
    
    # Test basic import
    print(f"✅ App title: {app.title}")
    print(f"✅ App root path: {app.root_path}")
    
    # Simulate a basic request event
    test_event = {
        "httpMethod": "GET",
        "path": "/",
        "headers": {},
        "body": None,
        "isBase64Encoded": False
    }
    
    test_context = {}
    
    # Test the handler
    print("\n🧪 Testing handler...")
    try:
        response = handler(test_event, test_context)
        print("✅ Handler executed successfully")
        print(f"✅ Response status: {response.get('statusCode', 'Unknown')}")
    except Exception as e:
        print(f"❌ Handler test failed: {e}")
    
    print("\n🎉 Basic validation completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)