"""
Usage Tracker

Tracks API usage for billing purposes.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from app.models import UsageLog, APIKey

logger = logging.getLogger(__name__)


class UsageTracker:
    """Track API usage for billing"""

    def __init__(self, db: Session):
        self.db = db

    def log_request(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        models_generated: int = 0,
        tokens_used: int = 0
    ):
        """
        Log an API request for usage tracking.

        Args:
            api_key_id: API key ID
            endpoint: Endpoint path
            method: HTTP method
            status_code: Response status code
            response_time: Response time in milliseconds
            models_generated: Number of models generated
            tokens_used: LLM tokens used (if tracked)
        """
        usage_log = UsageLog(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            models_generated=models_generated,
            tokens_used=tokens_used
        )

        self.db.add(usage_log)
        self.db.commit()

        # Update API key last_used
        api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if api_key:
            api_key.last_used = datetime.utcnow()
            self.db.commit()

    def get_usage_stats(self, api_key_id: int, days: int = 30) -> dict:
        """
        Get usage statistics for an API key.

        Returns:
            dict with total_requests, total_models, avg_response_time
        """
        from sqlalchemy import func
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        stats = (
            self.db.query(
                func.count(UsageLog.id).label('total_requests'),
                func.sum(UsageLog.models_generated).label('total_models'),
                func.avg(UsageLog.response_time).label('avg_response_time')
            )
            .filter(
                UsageLog.api_key_id == api_key_id,
                UsageLog.timestamp >= start_date
            )
            .first()
        )

        return {
            'total_requests': stats.total_requests or 0,
            'total_models': stats.total_models or 0,
            'avg_response_time': round(stats.avg_response_time or 0, 2),
            'period_days': days
        }

    def check_rate_limit(self, api_key_id: int, window_minutes: int = 60) -> bool:
        """
        Check if API key is within rate limit.

        Returns:
            True if within limit, False if exceeded
        """
        from datetime import timedelta
        from sqlalchemy import func

        api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if not api_key:
            return False

        start_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        request_count = (
            self.db.query(func.count(UsageLog.id))
            .filter(
                UsageLog.api_key_id == api_key_id,
                UsageLog.timestamp >= start_time
            )
            .scalar()
        )

        # rate_limit is per hour, adjust for window
        limit = api_key.rate_limit * (window_minutes / 60)

        return request_count < limit
