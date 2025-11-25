"""
User management routes for Flask admin dashboard (Admin only)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db_session
from app.services import AuthService
from app.models import User
from functools import wraps

bp = Blueprint('users', __name__)


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/users')
@admin_required
def list_users():
    """List all users (admin only)"""
    users = db_session.query(User).order_by(User.created_at.desc()).all()
    return render_template('users/list.html', users=users)


@bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    """Create a new user (admin only)"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        is_admin = request.form.get('is_admin') == 'on'

        if not email or not password or not full_name:
            flash('All fields are required', 'error')
            return render_template('users/new.html')

        try:
            auth_service = AuthService(db_session)
            user = auth_service.create_user(
                email=email,
                password=password,
                full_name=full_name,
                is_admin=is_admin
            )
            flash(f'User created successfully: {user.email}', 'success')
            return redirect(url_for('users.list_users'))

        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'error')

    return render_template('users/new.html')


@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    """Toggle user active status (admin only)"""
    user = db_session.query(User).filter(User.id == user_id).first()

    if not user:
        flash('User not found', 'error')
        return redirect(url_for('users.list_users'))

    user.is_active = not user.is_active
    db_session.commit()

    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.email} {status}', 'success')
    return redirect(url_for('users.list_users'))
