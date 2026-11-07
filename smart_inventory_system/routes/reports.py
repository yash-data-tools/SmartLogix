from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request
from models import db, Product, Category, Supplier, Transporter, DispatchOrder, IncomingGood, StockTransaction
from helpers import login_required, export_csv_response
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    report_type = request.args.get('type', 'stock')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    today = date.today()
    default_start = today - timedelta(days=30)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else default_start
    except ValueError:
        start_date = default_start

    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
    except ValueError:
        end_date = today

    data = []
    summary = {}

    if report_type == 'stock':
        # Current Stock Report
        products = Product.query.order_by(Product.category_id, Product.name).all()
        data = products
        summary['total_items'] = len(products)
        summary['total_stock'] = sum(p.available_quantity for p in products)
        summary['total_value'] = sum(p.available_quantity * p.purchase_price for p in products)
        summary['low_stock_count'] = sum(1 for p in products if p.is_low_stock)

    elif report_type == 'incoming':
        # Incoming Goods Report
        records = IncomingGood.query.filter(
            IncomingGood.date_of_arrival >= start_date,
            IncomingGood.date_of_arrival <= end_date
        ).order_by(IncomingGood.date_of_arrival.desc()).all()
        data = records
        summary['total_shipments'] = len(records)
        summary['total_qty'] = sum(r.quantity_received for r in records)
        summary['total_spend'] = sum(r.quantity_received * r.purchase_price for r in records)

    elif report_type == 'outgoing':
        # Outgoing Dispatches Report
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        orders = DispatchOrder.query.filter(
            DispatchOrder.dispatch_date >= start_dt,
            DispatchOrder.dispatch_date <= end_dt
        ).order_by(DispatchOrder.dispatch_date.desc()).all()
        data = orders
        summary['total_orders'] = len(orders)
        summary['total_dispatched_qty'] = sum(o.quantity_dispatched for o in orders if o.delivery_status != 'Cancelled')
        summary['delivered_count'] = sum(1 for o in orders if o.delivery_status == 'Delivered')
        summary['cancelled_count'] = sum(1 for o in orders if o.delivery_status == 'Cancelled')

    elif report_type == 'low_stock':
        # Low Stock Report
        products = Product.query.filter(Product.available_quantity <= Product.low_stock_threshold).order_by(Product.available_quantity.asc()).all()
        data = products
        summary['low_stock_count'] = len(products)
        summary['out_of_stock_count'] = sum(1 for p in products if p.available_quantity <= 0)

    elif report_type == 'expired':
        # Expired & Expiring Report
        products = Product.query.filter(Product.expiry_date.isnot(None), Product.expiry_date <= end_date).order_by(Product.expiry_date.asc()).all()
        data = products
        summary['expired_count'] = sum(1 for p in products if p.is_expired)
        summary['expiring_30d'] = sum(1 for p in products if not p.is_expired and p.expiry_date <= today + timedelta(days=30))

    elif report_type == 'suppliers':
        # Supplier performance / supply breakdown
        suppliers = Supplier.query.all()
        supplier_data = []
        for s in suppliers:
            total_qty = db.session.query(func.coalesce(func.sum(IncomingGood.quantity_received), 0)).filter(IncomingGood.supplier_id == s.id).scalar()
            total_spent = db.session.query(func.coalesce(func.sum(IncomingGood.quantity_received * IncomingGood.purchase_price), 0)).filter(IncomingGood.supplier_id == s.id).scalar()
            active_products = Product.query.filter_by(supplier_id=s.id).count()
            supplier_data.append({
                'supplier': s,
                'total_qty': total_qty,
                'total_spent': total_spent,
                'active_products': active_products
            })
        data = supplier_data
        summary['total_suppliers'] = len(suppliers)

    elif report_type == 'transporters':
        # Transporters and delivery performance
        transporters = Transporter.query.all()
        trans_data = []
        for t in transporters:
            deliveries = DispatchOrder.query.filter_by(transporter_id=t.id).all()
            completed = sum(1 for d in deliveries if d.delivery_status == 'Delivered')
            active = sum(1 for d in deliveries if d.delivery_status in ['In Transit', 'Ready for Dispatch'])
            cancelled = sum(1 for d in deliveries if d.delivery_status == 'Cancelled')
            trans_data.append({
                'transporter': t,
                'total_deliveries': len(deliveries),
                'completed': completed,
                'active': active,
                'cancelled': cancelled
            })
        data = trans_data
        summary['total_transporters'] = len(transporters)

    return render_template(
        'reports/index.html',
        report_type=report_type,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        data=data,
        summary=summary,
        today=today
    )


@reports_bp.route('/export')
@login_required
def export_csv():
    report_type = request.args.get('type', 'stock')
    today = date.today()

    if report_type == 'stock':
        products = Product.query.order_by(Product.name.asc()).all()
        headers = ['Product Code', 'Product Name', 'Category', 'Available Stock', 'Unit', 'Price (₹)', 'Total Value (₹)', 'Storage Location', 'Low Stock Alert']
        rows = [[
            p.product_code, p.name, p.category.name, p.available_quantity, p.unit,
            f"{p.purchase_price:.2f}", f"{(p.available_quantity * p.purchase_price):.2f}",
            p.storage_location.full_code, 'YES' if p.is_low_stock else 'NO'
        ] for p in products]

    elif report_type == 'low_stock':
        products = Product.query.filter(Product.available_quantity <= Product.low_stock_threshold).order_by(Product.available_quantity.asc()).all()
        headers = ['Product Code', 'Product Name', 'Category', 'Current Stock', 'Threshold', 'Unit', 'Supplier', 'Storage Location']
        rows = [[
            p.product_code, p.name, p.category.name, p.available_quantity, p.low_stock_threshold, p.unit, p.supplier.name, p.storage_location.full_code
        ] for p in products]

    elif report_type == 'expired':
        products = Product.query.filter(Product.expiry_date.isnot(None), Product.expiry_date < today).all()
        headers = ['Product Code', 'Product Name', 'Category', 'Remaining Quantity', 'Unit', 'Expiry Date', 'Location', 'Supplier']
        rows = [[
            p.product_code, p.name, p.category.name, p.available_quantity, p.unit, p.expiry_date.strftime('%Y-%m-%d'), p.storage_location.full_code, p.supplier.name
        ] for p in products]

    elif report_type == 'suppliers':
        suppliers = Supplier.query.all()
        headers = ['Supplier Code', 'Company Name', 'Contact Person', 'Phone', 'Email', 'Active Products', 'Total Units Supplied', 'Total Invoiced (₹)']
        rows = []
        for s in suppliers:
            total_qty = db.session.query(func.coalesce(func.sum(IncomingGood.quantity_received), 0)).filter(IncomingGood.supplier_id == s.id).scalar()
            total_spent = db.session.query(func.coalesce(func.sum(IncomingGood.quantity_received * IncomingGood.purchase_price), 0)).filter(IncomingGood.supplier_id == s.id).scalar()
            rows.append([
                s.supplier_code, s.company_name, s.name, s.phone, s.email,
                len(s.products), total_qty, f"{total_spent:.2f}"
            ])

    else:
        # Default fallback
        products = Product.query.all()
        headers = ['Product Code', 'Name', 'Available Stock']
        rows = [[p.product_code, p.name, p.available_quantity] for p in products]

    filename = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv_response(filename, headers, rows)
