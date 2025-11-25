"""
Dashboard routes for Flask admin dashboard
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.database import db_session
from app.models import Migration, User, APIKey
from sqlalchemy import func

bp = Blueprint('dashboard', __name__)


@bp.route('/dashboard')
@login_required
def index():
    """Main dashboard page"""

    # Get statistics
    total_migrations = db_session.query(Migration).count()
    user_migrations = db_session.query(Migration).filter(
        Migration.user_id == current_user.id
    ).count()

    completed_migrations = db_session.query(Migration).filter(
        Migration.status == 'completed'
    ).count()

    running_migrations = db_session.query(Migration).filter(
        Migration.status == 'running'
    ).count()

    # Get recent migrations
    recent_migrations = db_session.query(Migration).filter(
        Migration.user_id == current_user.id
    ).order_by(Migration.created_at.desc()).limit(10).all()

    # Calculate success rate
    if total_migrations > 0:
        success_rate = (completed_migrations / total_migrations) * 100
    else:
        success_rate = 0

    stats = {
        'total_migrations': total_migrations if current_user.is_admin else user_migrations,
        'completed_migrations': completed_migrations,
        'running_migrations': running_migrations,
        'success_rate': round(success_rate, 1)
    }

    return render_template('dashboard.html', stats=stats, recent_migrations=recent_migrations)
