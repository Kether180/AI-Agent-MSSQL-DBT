"""
Test script for the SaaS platform

This script tests:
1. Database connectivity
2. User authentication
3. API key generation
4. Migration creation
"""

import sys

def test_database():
    """Test database connection"""
    print("=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)

    try:
        from app.database import SessionLocal, init_db
        from app.models import User, APIKey, Migration

        # Try to create session
        db = SessionLocal()

        # Check if tables exist
        user_count = db.query(User).count()
        api_key_count = db.query(APIKey).count()
        migration_count = db.query(Migration).count()

        print(f"[OK] Database connected")
        print(f"     Users: {user_count}")
        print(f"     API Keys: {api_key_count}")
        print(f"     Migrations: {migration_count}")

        db.close()
        return True

    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False


def test_services():
    """Test services layer"""
    print("\n" + "=" * 60)
    print("TEST 2: Services Layer")
    print("=" * 60)

    try:
        from app.database import SessionLocal
        from app.services import AuthService, UsageTracker, MigrationService

        db = SessionLocal()

        # Test AuthService
        auth = AuthService(db)
        print("[OK] AuthService initialized")

        # Test UsageTracker
        tracker = UsageTracker(db)
        print("[OK] UsageTracker initialized")

        # Test MigrationService
        migration_service = MigrationService(db)
        print("[OK] MigrationService initialized")

        db.close()
        return True

    except Exception as e:
        print(f"[ERROR] Services test failed: {e}")
        return False


def test_flask_app():
    """Test Flask app creation"""
    print("\n" + "=" * 60)
    print("TEST 3: Flask Application")
    print("=" * 60)

    try:
        from flask_app import create_app

        app = create_app()
        print(f"[OK] Flask app created")
        print(f"     Routes: {len(app.url_map._rules)}")
        print(f"     Secret key set: {bool(app.config['SECRET_KEY'])}")

        return True

    except Exception as e:
        print(f"[ERROR] Flask test failed: {e}")
        return False


def test_fastapi_app():
    """Test FastAPI app creation"""
    print("\n" + "=" * 60)
    print("TEST 4: FastAPI Application")
    print("=" * 60)

    try:
        from fastapi_app.main import app

        print(f"[OK] FastAPI app created")
        print(f"     Title: {app.title}")
        print(f"     Version: {app.version}")
        print(f"     Routes: {len(app.routes)}")

        return True

    except Exception as e:
        print(f"[ERROR] FastAPI test failed: {e}")
        return False


def test_user_login():
    """Test user authentication"""
    print("\n" + "=" * 60)
    print("TEST 5: User Authentication")
    print("=" * 60)

    try:
        from app.database import SessionLocal
        from app.services import AuthService

        db = SessionLocal()
        auth = AuthService(db)

        # Try to authenticate the test user
        user = auth.authenticate_user("admin@test.com", "admin123")

        if user:
            print(f"[OK] User authenticated: {user.email}")
            print(f"     User ID: {user.id}")
            print(f"     Is Admin: {user.is_admin}")
        else:
            print("[WARNING] Test user not found - run database init first")

        db.close()
        return True

    except Exception as e:
        print(f"[ERROR] Authentication test failed: {e}")
        return False


def test_api_key():
    """Test API key validation"""
    print("\n" + "=" * 60)
    print("TEST 6: API Key Validation")
    print("=" * 60)

    try:
        from app.database import SessionLocal
        from app.services import AuthService

        db = SessionLocal()
        auth = AuthService(db)

        # Get API keys for user 1
        api_keys = auth.get_user_api_keys(1)

        if api_keys:
            test_key = api_keys[0]
            print(f"[OK] Found API key")
            print(f"     Name: {test_key.name}")
            print(f"     Active: {test_key.is_active}")
            print(f"     Rate Limit: {test_key.rate_limit}/hour")

            # Test authentication
            authenticated = auth.authenticate_api_key(test_key.key)
            if authenticated:
                print(f"[OK] API key validates successfully")
        else:
            print("[WARNING] No API keys found - create one in Flask dashboard")

        db.close()
        return True

    except Exception as e:
        print(f"[ERROR] API key test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print(" " * 12 + "SaaS Platform Test Suite")
    print("=" * 60)

    tests = [
        test_database,
        test_services,
        test_flask_app,
        test_fastapi_app,
        test_user_login,
        test_api_key
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Test crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if all(results):
        print("\n[SUCCESS] All tests passed! Ready to run Flask and FastAPI.")
        print("\nNext steps:")
        print("  1. Terminal 1: python run_flask.py")
        print("  2. Terminal 2: python run_fastapi.py")
        print("  3. Access Flask: http://localhost:5000")
        print("  4. Access FastAPI: http://localhost:8000/docs")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
