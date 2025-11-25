"""
API Key management routes for Flask admin dashboard
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db_session
from app.services import AuthService

bp = Blueprint('api_keys', __name__)


@bp.route('/api-keys')
@login_required
def list_api_keys():
    """List user's API keys"""
    auth_service = AuthService(db_session)
    api_keys = auth_service.get_user_api_keys(current_user.id)
    return render_template('api_keys/list.html', api_keys=api_keys)


@bp.route('/api-keys/new', methods=['GET', 'POST'])
@login_required
def new_api_key():
    """Generate a new API key"""
    if request.method == 'POST':
        name = request.form.get('name')
        rate_limit = request.form.get('rate_limit', 100, type=int)
        expires_in_days = request.form.get('expires_in_days', type=int)

        if not name:
            flash('API key name is required', 'error')
            return render_template('api_keys/new.html')

        try:
            auth_service = AuthService(db_session)
            api_key = auth_service.create_api_key(
                user_id=current_user.id,
                name=name,
                rate_limit=rate_limit,
                expires_in_days=expires_in_days if expires_in_days else None
            )

            flash(f'API key created: {api_key.key}', 'success')
            flash('IMPORTANT: Copy this key now. You will not be able to see it again!', 'warning')
            return redirect(url_for('api_keys.list_api_keys'))

        except Exception as e:
            flash(f'Error creating API key: {str(e)}', 'error')

    return render_template('api_keys/new.html')


@bp.route('/api-keys/<int:key_id>/revoke', methods=['POST'])
@login_required
def revoke_api_key(key_id):
    """Revoke an API key"""
    auth_service = AuthService(db_session)

    # Verify the key belongs to the current user
    api_keys = auth_service.get_user_api_keys(current_user.id)
    if not any(k.id == key_id for k in api_keys):
        flash('API key not found', 'error')
        return redirect(url_for('api_keys.list_api_keys'))

    try:
        auth_service.revoke_api_key(key_id)
        flash('API key revoked successfully', 'success')
    except Exception as e:
        flash(f'Error revoking API key: {str(e)}', 'error')

    return redirect(url_for('api_keys.list_api_keys'))
