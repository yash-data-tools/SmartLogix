from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify
from models import db, Product, Category, Supplier, Transporter, DispatchOrder, IncomingGood, Notification
from helpers import login_required, update_system_notifications
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Update system notifications in the background
    update_system_notifications()

    today = date.today()

    # Core statistics
    total_products = Product.query.count()
    total_stock_qty = db.session.query(func.coalesce(func.sum(Product.available_quantity), 0)).scalar()
    total_incoming_qty = db.session.query(func.coalesce(func.sum(IncomingGood.quantity_received), 0)).scalar()
    total_dispatched_qty = db.session.query(
        func.coalesce(func.sum(DispatchOrder.quantity_dispatched), 0)
    ).filter(DispatchOrder.delivery_status != 'Cancelled').scalar()

    low_stock_count = Product.query.filter(
        Product.available_quantity <= Product.low_stock_threshold
    ).count()

    expired_count = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date < today
    ).count()

    expiring_soon_count = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date >= today,
        Product.expiry_date <= today + timedelta(days=30)
    ).count()

    total_transporters = Transporter.query.count()
    active_deliveries = DispatchOrder.query.filter(
        DispatchOrder.delivery_status.in_(['Pending', 'Ready for Dispatch', 'In Transit'])
    ).count()

    # Recent incoming and dispatch activities
    recent_incoming = IncomingGood.query.order_by(IncomingGood.date_of_arrival.desc(), IncomingGood.id.desc()).limit(5).all()
    recent_dispatches = DispatchOrder.query.order_by(DispatchOrder.dispatch_date.desc(), DispatchOrder.id.desc()).limit(5).all()
    critical_stock = Product.query.filter(
        Product.available_quantity <= Product.low_stock_threshold
    ).order_by(Product.available_quantity.asc()).limit(5).all()
    expiring_products = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date <= today + timedelta(days=30)
    ).order_by(Product.expiry_date.asc()).limit(5).all()

    return render_template(
        'dashboard/index.html',
        total_products=total_products,
        total_stock_qty=total_stock_qty,
        total_incoming_qty=total_incoming_qty,
        total_dispatched_qty=total_dispatched_qty,
        low_stock_count=low_stock_count,
        expired_count=expired_count,
        expiring_soon_count=expiring_soon_count,
        total_transporters=total_transporters,
        active_deliveries=active_deliveries,
        recent_incoming=recent_incoming,
        recent_dispatches=recent_dispatches,
        critical_stock=critical_stock,
        expiring_products=expiring_products,
        today=today
    )


@dashboard_bp.route('/api/dashboard-charts')
@login_required
def chart_data():
    """Provides JSON data for all 4 dynamic Chart.js charts."""
    today = date.today()

    # 1. Monthly Incoming & Outgoing (Last 6 Months)
    # Generate list of past 6 months (labels and counts)
    month_labels = []
    incoming_monthly = []
    dispatched_monthly = []

    for i in range(5, -1, -1):
        # Calculate year and month
        month_target = (today.month - i - 1) % 12 + 1
        year_target = today.year + (today.month - i - 1) // 12
        month_name = datetime(year_target, month_target, 1).strftime('%b %Y')
        month_labels.append(month_name)

        # Incoming qty sum for this month & year
        in_qty = db.session.query(func.coalesce(func.sum(IncomingGood.quantity_received), 0)).filter(
            IncomingGood.month == month_target,
            IncomingGood.year == year_target
        ).scalar()
        incoming_monthly.append(int(in_qty))

        # Dispatched qty sum for this month
        start_date = datetime(year_target, month_target, 1)
        if month_target == 12:
            end_date = datetime(year_target + 1, 1, 1)
        else:
            end_date = datetime(year_target, month_target + 1, 1)

        out_qty = db.session.query(func.coalesce(func.sum(DispatchOrder.quantity_dispatched), 0)).filter(
            DispatchOrder.dispatch_date >= start_date,
            DispatchOrder.dispatch_date < end_date,
            DispatchOrder.delivery_status != 'Cancelled'
        ).scalar()
        dispatched_monthly.append(int(out_qty))

    # 2. Stock Distribution by Category
    categories = Category.query.all()
    category_labels = []
    category_stock = []
    for cat in categories:
        cat_stock = db.session.query(func.coalesce(func.sum(Product.available_quantity), 0)).filter(
            Product.category_id == cat.id
        ).scalar()
        category_labels.append(cat.name)
        category_stock.append(int(cat_stock))

    # 3. Expiry Status Breakdown
    expired_qty = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date < today
    ).count()

    critical_7d = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date >= today,
        Product.expiry_date <= today + timedelta(days=7)
    ).count()

    warning_30d = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.expiry_date > today + timedelta(days=7),
        Product.expiry_date <= today + timedelta(days=30)
    ).count()

    safe_products = Product.query.filter(
        (Product.expiry_date.is_(None)) | (Product.expiry_date > today + timedelta(days=30))
    ).count()

    return jsonify({
        'monthly_labels': month_labels,
        'incoming_monthly': incoming_monthly,
        'dispatched_monthly': dispatched_monthly,
        'category_labels': category_labels,
        'category_stock': category_stock,
        'expiry_labels': ['Expired (0d)', 'Expiring in 7d', 'Expiring in 30d', 'Safe / Non-perishable'],
        'expiry_counts': [expired_qty, critical_7d, warning_30d, safe_products]
    })
