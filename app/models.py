"""
Database Models

SQLAlchemy models for User, APIKey, Migration, UsageLog, and ModelFile.
"""

import secrets
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from .database import Base


class User(Base):
    """
    User model for admin dashboard authentication.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    api_keys = relationship('APIKey', back_populates='user', cascade='all, delete-orphan')
    migrations = relationship('Migration', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class APIKey(Base):
    """
    API Key model for FastAPI authentication.

    Customers use API keys to access the public API.
    """
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100))  # e.g., "Production Key", "Test Key"
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # Requests per hour
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    expires_at = Column(DateTime)

    # Relationships
    user = relationship('User', back_populates='api_keys')
    usage_logs = relationship('UsageLog', back_populates='api_key', cascade='all, delete-orphan')
    migrations = relationship('Migration', back_populates='api_key')

    @staticmethod
    def generate_key() -> str:
        """Generate a secure random API key"""
        return f"mk_{secrets.token_urlsafe(48)}"  # mk = migration key

    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def __repr__(self):
        return f'<APIKey {self.name} ({self.key[:16]}...)>'


class Migration(Base):
    """
    Migration model to track MSSQL to dbt migrations.
    """
    __tablename__ = 'migrations'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    api_key_id = Column(Integer, ForeignKey('api_keys.id'))

    # Migration details
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    phase = Column(String(20))  # assessment, planning, execution, evaluation, complete
    project_name = Column(String(200))
    project_path = Column(String(500))

    # Metadata (MSSQL schema)
    metadata_json = Column(JSON)  # Stores the full MSSQL metadata

    # Progress tracking
    total_models = Column(Integer, default=0)
    completed_models = Column(Integer, default=0)
    failed_models = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)

    # State storage
    state_json = Column(JSON)  # Full LangGraph state
    assessment_json = Column(JSON)
    planning_json = Column(JSON)
    evaluation_json = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Error tracking
    error_message = Column(Text)
    errors_json = Column(JSON)  # List of all errors

    # Relationships
    user = relationship('User', back_populates='migrations')
    api_key = relationship('APIKey', back_populates='migrations')
    model_files = relationship('ModelFile', back_populates='migration', cascade='all, delete-orphan')

    def update_progress(self):
        """Update success rate from completed/failed counts"""
        if self.total_models > 0:
            self.success_rate = (self.completed_models / self.total_models) * 100
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f'<Migration {self.id} ({self.status})>'


class ModelFile(Base):
    """
    Generated dbt model files.
    """
    __tablename__ = 'model_files'

    id = Column(Integer, primary_key=True)
    migration_id = Column(Integer, ForeignKey('migrations.id'), nullable=False)

    # Model details
    name = Column(String(200), nullable=False)
    model_type = Column(String(50))  # staging, intermediate, fact, dimension
    status = Column(String(20))  # pending, completed, failed
    file_path = Column(String(500))
    source_object = Column(String(200))

    # Content
    sql_code = Column(Text)
    validation_score = Column(Float)
    attempts = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    migration = relationship('Migration', back_populates='model_files')

    def __repr__(self):
        return f'<ModelFile {self.name} ({self.status})>'


class UsageLog(Base):
    """
    Usage tracking for billing.

    Tracks API calls per API key for usage-based pricing.
    """
    __tablename__ = 'usage_logs'

    id = Column(Integer, primary_key=True)
    api_key_id = Column(Integer, ForeignKey('api_keys.id'), nullable=False)

    # Request details
    endpoint = Column(String(200))
    method = Column(String(10))
    status_code = Column(Integer)
    response_time = Column(Float)  # milliseconds

    # Usage details
    models_generated = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)  # If tracking LLM tokens

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    api_key = relationship('APIKey', back_populates='usage_logs')

    def __repr__(self):
        return f'<UsageLog {self.endpoint} ({self.timestamp})>'
