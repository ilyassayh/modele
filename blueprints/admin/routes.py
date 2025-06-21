from flask import Blueprint, render_template, abort, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User, db
from models.estimate import Estimate
from datetime import datetime, timedelta
import json
import os
import sqlite3

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    # Get comprehensive statistics
    stats = {
        'total_users': User.query.count(),
        'total_estimates': Estimate.query.count(),
        'total_photos': Estimate.query.filter_by(estimate_type='photo').count(),
        'total_manual': Estimate.query.filter_by(estimate_type='manual').count(),
        'new_users_today': User.query.filter(
            User.id >= 1  # Assuming auto-increment, this gets recent users
        ).count(),
        'estimates_today': Estimate.query.filter(
            Estimate.timestamp >= datetime.utcnow().date()
        ).count()
    }
    
    # Get recent activity
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    recent_estimates = Estimate.query.order_by(Estimate.timestamp.desc()).limit(5).all()
    
    # Get estimate statistics by type
    estimate_stats = {
        'photo_estimates': Estimate.query.filter_by(estimate_type='photo').count(),
        'manual_estimates': Estimate.query.filter_by(estimate_type='manual').count(),
        'avg_cost': 'N/A'  # Could be calculated if cost is stored as numeric
    }
    
    users = User.query.all()
    return render_template('admin/admin.html', 
                         stats=stats, 
                         users=users, 
                         recent_users=recent_users,
                         recent_estimates=recent_estimates,
                         estimate_stats=estimate_stats)

@admin_bp.route('/admin/users')
@login_required
def admin_users():
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/estimates')
@login_required
def admin_estimates():
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    estimates = Estimate.query.order_by(Estimate.timestamp.desc()).all()
    today = datetime.utcnow().date()
    return render_template('admin/estimates.html', estimates=estimates, today=today)

@admin_bp.route('/admin/settings')
@login_required
def admin_settings():
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    # Get system information
    system_info = {
        'database_size': get_database_size(),
        'total_files': count_uploaded_files(),
        'system_uptime': get_system_uptime(),
        'python_version': get_python_version()
    }
    
    return render_template('admin/settings.html', system_info=system_info)

@admin_bp.route('/admin/backup')
@login_required
def admin_backup():
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    try:
        # Create backup directory if it doesn't exist
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy database
        import shutil
        shutil.copy2('instance/site.db', backup_path)
        
        flash(f'Backup created successfully: {backup_filename}', 'success')
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_settings'))

@admin_bp.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
def toggle_admin_status(user_id):
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot modify your own admin status!', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'admin' if user.is_admin else 'user'
    flash(f'User {user.email} is now a {status}', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin.admin_users'))
    
    # Delete associated estimates first
    Estimate.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.email} has been deleted', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/estimate/<int:estimate_id>/delete', methods=['POST'])
@login_required
def delete_estimate(estimate_id):
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    estimate = Estimate.query.get_or_404(estimate_id)
    db.session.delete(estimate)
    db.session.commit()
    
    flash(f'Estimate {estimate_id} has been deleted', 'success')
    return redirect(url_for('admin.admin_estimates'))

@admin_bp.route('/admin/stats')
@login_required
def admin_stats():
    if not getattr(current_user, 'is_admin', False):
        return abort(403)
    
    # Get detailed statistics
    total_users = User.query.count()
    total_estimates = Estimate.query.count()
    photo_estimates = Estimate.query.filter_by(estimate_type='photo').count()
    manual_estimates = Estimate.query.filter_by(estimate_type='manual').count()
    
    # Get estimates by date (last 7 days)
    dates = []
    estimate_counts = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = Estimate.query.filter(
            Estimate.timestamp >= date,
            Estimate.timestamp < date + timedelta(days=1)
        ).count()
        dates.append(date.strftime('%m/%d'))
        estimate_counts.append(count)
    
    dates.reverse()
    estimate_counts.reverse()
    
    return jsonify({
        'total_users': total_users,
        'total_estimates': total_estimates,
        'photo_estimates': photo_estimates,
        'manual_estimates': manual_estimates,
        'dates': dates,
        'estimate_counts': estimate_counts
    })

# Helper functions for system information
def get_database_size():
    try:
        db_path = 'instance/site.db'
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        return "N/A"
    except:
        return "N/A"

def count_uploaded_files():
    try:
        upload_dir = 'uploads'
        if os.path.exists(upload_dir):
            return len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
        return 0
    except:
        return 0

def get_system_uptime():
    try:
        import psutil
        uptime_seconds = psutil.boot_time()
        uptime_days = (datetime.now() - datetime.fromtimestamp(uptime_seconds)).days
        return f"{uptime_days} days"
    except:
        return "N/A"

def get_python_version():
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}" 