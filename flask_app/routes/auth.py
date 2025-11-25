"""
Authentication routes for Flask admin dashboard
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.database import db_session
from app.services import AuthService

bp = Blueprint('auth', __name__)


@bp.route('/')
def index():
    """Redirect to login or dashboard"""
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        auth_service = AuthService(db_session)
        user = auth_service.authenticate_user(email, password)

        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout current user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
