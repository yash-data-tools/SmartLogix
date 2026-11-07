import csv
import io
from functools import wraps
from datetime import datetime, date, timedelta
from flask import session, redirect, url_for, flash, Response
from models import db, Product, DispatchOrder, Notification

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def generate_code(prefix, model_class, code_field):
    """Generates unique sequential codes like PRD-2026-001, DSP-2026-001, etc."""
    year = datetime.now().year
    count = model_class.query.count() + 1
    code = f"{prefix}-{year}-{count:04d}"
    # Verify uniqueness
    while getattr(model_class, 'query').filter(getattr(model_class, code_field) == code).first():
        count += 1
        code = f"{prefix}-{year}-{count:04d}"
    return code


def update_system_notifications():
    """Scans inventory & dispatches and keeps system notifications fresh."""
    today = date.today()

    # 1. Check Expired Products
    expired_products = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date < today,
        Product.available_quantity > 0
    ).all()
    for p in expired_products:
        existing = Notification.query.filter_by(
            title=f"Expired Product: {p.name}",
            is_read=False
        ).first()
        if not existing:
            notif = Notification(
                title=f"Expired Product: {p.name}",
                message=f"Product {p.product_code} ({p.name}) expired on {p.expiry_date.strftime('%d-%b-%Y')} with {p.available_quantity} {p.unit} remaining.",
                type="danger",
                link="/expiry"
            )
            db.session.add(notif)

    # 2. Check Products Expiring in 7 Days
    soon_products = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date >= today,
        Product.expiry_date <= today + timedelta(days=7),
        Product.available_quantity > 0
    ).all()
    for p in soon_products:
        days_left = (p.expiry_date - today).days
        existing = Notification.query.filter_by(
            title=f"Expiring Soon (7d): {p.name}",
            is_read=False
        ).first()
        if not existing:
            notif = Notification(
                title=f"Expiring Soon (7d): {p.name}",
                message=f"{p.name} ({p.product_code}) will expire in {days_left} day(s) on {p.expiry_date.strftime('%d-%b-%Y')}. Action required!",
                type="warning",
                link="/expiry"
            )
            db.session.add(notif)

    # 3. Check Low Stock Products
    low_stock = Product.query.filter(
        Product.available_quantity <= Product.low_stock_threshold
    ).all()
    for p in low_stock:
        existing = Notification.query.filter_by(
            title=f"Low Stock Alert: {p.name}",
            is_read=False
        ).first()
        if not existing:
            notif = Notification(
                title=f"Low Stock Alert: {p.name}",
                message=f"Available quantity ({p.available_quantity} {p.unit}) is at or below threshold ({p.low_stock_threshold} {p.unit}).",
                type="warning",
                link="/inventory"
            )
            db.session.add(notif)

    # 4. Check Pending Dispatches
    pending_dispatches = DispatchOrder.query.filter_by(delivery_status='Pending').count()
    if pending_dispatches > 0:
        existing = Notification.query.filter_by(
            title="Pending Dispatches Requiring Action",
            is_read=False
        ).first()
        if not existing:
            notif = Notification(
                title="Pending Dispatches Requiring Action",
                message=f"There are {pending_dispatches} pending dispatch order(s) waiting for transporter assignment or departure.",
                type="info",
                link="/dispatch"
            )
            db.session.add(notif)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def export_csv_response(filename, headers, rows):
    """Helper to stream CSV file download directly from Flask."""
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    output = si.getvalue()
    si.close()

    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response
