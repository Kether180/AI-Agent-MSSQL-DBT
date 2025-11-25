"""
Migration management routes for Flask admin dashboard
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.database import db_session
from app.services import MigrationService
from app.models import Migration
import json

bp = Blueprint('migrations', __name__)


@bp.route('/migrations')
@login_required
def list_migrations():
    """List all migrations for current user"""
    if current_user.is_admin:
        migrations = db_session.query(Migration).order_by(Migration.created_at.desc()).all()
    else:
        migrations = db_session.query(Migration).filter(
            Migration.user_id == current_user.id
        ).order_by(Migration.created_at.desc()).all()

    return render_template('migrations/list.html', migrations=migrations)


@bp.route('/migrations/<int:migration_id>')
@login_required
def view_migration(migration_id):
    """View details of a specific migration"""
    migration = db_session.query(Migration).filter(Migration.id == migration_id).first()

    if not migration:
        flash('Migration not found', 'error')
        return redirect(url_for('migrations.list_migrations'))

    # Check permissions
    if not current_user.is_admin and migration.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('migrations.list_migrations'))

    # Get migration service to fetch models
    service = MigrationService(db_session)
    models = service.get_migration_models(migration_id)

    return render_template('migrations/detail.html', migration=migration, models=models)


@bp.route('/migrations/new', methods=['GET', 'POST'])
@login_required
def new_migration():
    """Create a new migration"""
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        metadata_file = request.files.get('metadata_file')

        if not project_name or not metadata_file:
            flash('Project name and metadata file are required', 'error')
            return render_template('migrations/new.html')

        try:
            # Parse metadata JSON
            metadata_content = metadata_file.read().decode('utf-8')
            metadata = json.loads(metadata_content)

            # Create migration
            service = MigrationService(db_session)
            migration = service.create_migration(
                user_id=current_user.id,
                metadata=metadata,
                project_name=project_name
            )

            flash(f'Migration created successfully: {migration.id}', 'success')
            return redirect(url_for('migrations.view_migration', migration_id=migration.id))

        except json.JSONDecodeError:
            flash('Invalid JSON metadata file', 'error')
        except Exception as e:
            flash(f'Error creating migration: {str(e)}', 'error')

    return render_template('migrations/new.html')


@bp.route('/migrations/<int:migration_id>/start', methods=['POST'])
@login_required
def start_migration(migration_id):
    """Start a migration"""
    migration = db_session.query(Migration).filter(Migration.id == migration_id).first()

    if not migration:
        return jsonify({'error': 'Migration not found'}), 404

    # Check permissions
    if not current_user.is_admin and migration.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if migration.status != 'pending':
        return jsonify({'error': f'Migration is already {migration.status}'}), 400

    try:
        service = MigrationService(db_session)
        service.start_migration(migration_id)
        return jsonify({'status': 'success', 'message': 'Migration started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/migrations/<int:migration_id>/status')
@login_required
def migration_status(migration_id):
    """Get current status of a migration (AJAX endpoint)"""
    migration = db_session.query(Migration).filter(Migration.id == migration_id).first()

    if not migration:
        return jsonify({'error': 'Migration not found'}), 404

    # Check permissions
    if not current_user.is_admin and migration.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'id': migration.id,
        'status': migration.status,
        'phase': migration.phase,
        'completed_models': migration.completed_models,
        'total_models': migration.total_models,
        'success_rate': migration.success_rate
    })
