from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, Notification
from helpers import login_required, update_system_notifications

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def index():
    update_system_notifications()
    notifications = Notification.query.order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(is_read=False).count()
    return render_template('notifications/index.html', notifications=notifications, unread_count=unread_count)


@notifications_bp.route('/<int:notification_id>/read')
@login_required
def mark_read(notification_id):
    notif = Notification.query.get_or_404(notification_id)
    notif.is_read = True
    db.session.commit()
    target = notif.link or url_for('notifications.index')
    return redirect(target)


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    Notification.query.delete()
    db.session.commit()
    flash('All notifications cleared.', 'info')
    return redirect(url_for('notifications.index'))
