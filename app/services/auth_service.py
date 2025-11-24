"""
Authentication Service

User and API key authentication logic.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.models import User, APIKey

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication and authorization service"""

    def __init__(self, db: Session):
        self.db = db

    # User authentication
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.

        Returns:
            User if authenticated, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()

        if user and user.is_active and user.check_password(password):
            user.last_login = datetime.utcnow()
            self.db.commit()
            return user

        return None

    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        is_admin: bool = False
    ) -> User:
        """Create a new user"""
        user = User(
            email=email,
            full_name=full_name,
            is_admin=is_admin,
            is_active=True
        )
        user.set_password(password)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Created user: {email}")
        return user

    # API key authentication
    def authenticate_api_key(self, key: str) -> Optional[APIKey]:
        """
        Authenticate API key.

        Returns:
            APIKey if valid, None otherwise
        """
        api_key = self.db.query(APIKey).filter(APIKey.key == key).first()

        if api_key and api_key.is_valid():
            return api_key

        return None

    def create_api_key(
        self,
        user_id: int,
        name: str,
        rate_limit: int = 100,
        expires_in_days: Optional[int] = None
    ) -> APIKey:
        """
        Create a new API key for a user.

        Args:
            user_id: User ID
            name: Key name/description
            rate_limit: Requests per hour
            expires_in_days: Days until expiration (None = never)

        Returns:
            APIKey instance
        """
        api_key = APIKey(
            user_id=user_id,
            key=APIKey.generate_key(),
            name=name,
            rate_limit=rate_limit,
            is_active=True
        )

        if expires_in_days:
            api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        logger.info(f"Created API key '{name}' for user {user_id}")
        return api_key

    def revoke_api_key(self, api_key_id: int):
        """Revoke (deactivate) an API key"""
        api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if api_key:
            api_key.is_active = False
            self.db.commit()
            logger.info(f"Revoked API key {api_key_id}")

    def get_user_api_keys(self, user_id: int) -> list:
        """Get all API keys for a user"""
        return (
            self.db.query(APIKey)
            .filter(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
            .all()
        )
