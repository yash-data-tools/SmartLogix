from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db, Product, Category
from helpers import login_required, export_csv_response

expiry_bp = Blueprint('expiry', __name__)

@expiry_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)

    today = date.today()
    seven_days = today + timedelta(days=7)
    thirty_days = today + timedelta(days=30)

    # Base query for products with expiry dates
    query = Product.query.filter(Product.expiry_date.isnot(None))

    if search_query:
        query = query.filter(
            (Product.name.ilike(f'%{search_query}%')) |
            (Product.product_code.ilike(f'%{search_query}%'))
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Filter by selected status tab
    if status_filter == 'expired':
        query = query.filter(Product.expiry_date < today)
    elif status_filter == 'expiring_7d':
        query = query.filter(Product.expiry_date >= today, Product.expiry_date <= seven_days)
    elif status_filter == 'expiring_30d':
        query = query.filter(Product.expiry_date > seven_days, Product.expiry_date <= thirty_days)
    elif status_filter == 'safe':
        query = query.filter(Product.expiry_date > thirty_days)

    # Sort so most urgent are top
    products = query.order_by(Product.expiry_date.asc()).all()

    # Stat counts for badges
    expired_count = Product.query.filter(Product.expiry_date.isnot(None), Product.expiry_date < today).count()
    expiring_7d_count = Product.query.filter(Product.expiry_date.isnot(None), Product.expiry_date >= today, Product.expiry_date <= seven_days).count()
    expiring_30d_count = Product.query.filter(Product.expiry_date.isnot(None), Product.expiry_date > seven_days, Product.expiry_date <= thirty_days).count()
    safe_count = Product.query.filter(Product.expiry_date.isnot(None), Product.expiry_date > thirty_days).count()
    all_count = Product.query.filter(Product.expiry_date.isnot(None)).count()

    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'expiry/index.html',
        products=products,
        today=today,
        status_filter=status_filter,
        search_query=search_query,
        category_id=category_id,
        categories=categories,
        expired_count=expired_count,
        expiring_7d_count=expiring_7d_count,
        expiring_30d_count=expiring_30d_count,
        safe_count=safe_count,
        all_count=all_count
    )


@expiry_bp.route('/export')
@login_required
def export_csv():
    today = date.today()
    status_filter = request.args.get('status', 'all')
    query = Product.query.filter(Product.expiry_date.isnot(None))

    if status_filter == 'expired':
        query = query.filter(Product.expiry_date < today)
    elif status_filter == 'expiring_7d':
        query = query.filter(Product.expiry_date >= today, Product.expiry_date <= today + timedelta(days=7))
    elif status_filter == 'expiring_30d':
        query = query.filter(Product.expiry_date > today + timedelta(days=7), Product.expiry_date <= today + timedelta(days=30))

    products = query.order_by(Product.expiry_date.asc()).all()

    headers = [
        'Product Code', 'Product Name', 'Category', 'Available Qty', 'Unit',
        'Expiry Date', 'Days Until Expiry', 'Expiry Status', 'Storage Location', 'Supplier'
    ]

    rows = []
    for p in products:
        diff = (p.expiry_date - today).days
        status_text = 'EXPIRED' if diff < 0 else ('CRITICAL (<7d)' if diff <= 7 else ('WARNING (<30d)' if diff <= 30 else 'SAFE'))
        rows.append([
            p.product_code,
            p.name,
            p.category.name,
            p.available_quantity,
            p.unit,
            p.expiry_date.strftime('%Y-%m-%d'),
            diff,
            status_text,
            p.storage_location.full_code,
            p.supplier.name
        ])

    filename = f"expiry_report_{status_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv_response(filename, headers, rows)
