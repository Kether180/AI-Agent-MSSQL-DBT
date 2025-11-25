"""
Flask Admin Dashboard Entry Point

Run this to start the Flask admin dashboard on port 5000.

Usage:
    python run_flask.py
"""

import os
import sys

# Ensure ANTHROPIC_API_KEY is set (optional for development)
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("WARNING: ANTHROPIC_API_KEY not set. Agents will use fallback mode.")
    print("Set it with: export ANTHROPIC_API_KEY=your_key_here")
    print()

from flask_app import create_app

if __name__ == "__main__":
    app = create_app()

    print("=" * 60)
    print("Flask Admin Dashboard Starting...")
    print("=" * 60)
    print(f"Dashboard URL: http://localhost:5000")
    print(f"Login with your admin credentials")
    print()
    print("To create an admin user, run:")
    print('  python -c "from app.database import SessionLocal; from app.services import AuthService; db = SessionLocal(); auth = AuthService(db); user = auth.create_user(\'admin@test.com\', \'admin123\', \'Admin\', True); print(f\'Created: {user.email}\')"')
    print("=" * 60)
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
