from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, IncomingGood, Product, Supplier, StockTransaction, Notification
from helpers import login_required, generate_code, export_csv_response
from sqlalchemy import func

incoming_bp = Blueprint('incoming', __name__)

@incoming_bp.route('/')
@login_required
def index():
    # Filters
    selected_year = request.args.get('year', type=int)
    selected_month = request.args.get('month', type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = IncomingGood.query.join(Product).join(Supplier)

    if selected_year:
        query = query.filter(IncomingGood.year == selected_year)
    if selected_month:
        query = query.filter(IncomingGood.month == selected_month)
    if supplier_id:
        query = query.filter(IncomingGood.supplier_id == supplier_id)
    if search_query:
        query = query.filter(
            (Product.name.ilike(f'%{search_query}%')) |
            (Product.product_code.ilike(f'%{search_query}%')) |
            (IncomingGood.invoice_number.ilike(f'%{search_query}%')) |
            (IncomingGood.incoming_code.ilike(f'%{search_query}%'))
        )

    # Sort descending by arrival date
    query = query.order_by(IncomingGood.date_of_arrival.desc(), IncomingGood.id.desc())

    # Get Monthly Summary Stats
    total_records = query.count()
    total_qty = db.session.query(func.coalesce(func.sum(IncomingGood.quantity_received), 0)).scalar()
    
    # Calculate total value of incoming goods
    total_value = db.session.query(
        func.coalesce(func.sum(IncomingGood.quantity_received * IncomingGood.purchase_price), 0)
    ).scalar()

    # Dropdown lists
    years_available = db.session.query(IncomingGood.year).distinct().order_by(IncomingGood.year.desc()).all()
    years = [y[0] for y in years_available] if years_available else [datetime.now().year]
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = pagination.items

    month_names = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    return render_template(
        'incoming/index.html',
        records=records,
        pagination=pagination,
        years=years,
        suppliers=suppliers,
        month_names=month_names,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_supplier_id=supplier_id,
        search_query=search_query,
        total_records=total_records,
        total_qty=total_qty,
        total_value=total_value
    )


@incoming_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    products = Product.query.order_by(Product.name.asc()).all()
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int)
        quantity_received = request.form.get('quantity_received', type=int)
        arrival_date_str = request.form.get('arrival_date')
        invoice_number = request.form.get('invoice_number', '').strip()
        purchase_price = request.form.get('purchase_price', 0.0, type=float)
        notes = request.form.get('notes', '').strip()

        if not product_id or not supplier_id or not quantity_received or quantity_received <= 0 or not invoice_number:
            flash('Please fill in all mandatory fields with a valid quantity (>0).', 'danger')
            return render_template('incoming/add.html', products=products, suppliers=suppliers, today=date.today().strftime('%Y-%m-%d'))

        try:
            arrival_date = datetime.strptime(arrival_date_str, '%Y-%m-%d').date() if arrival_date_str else date.today()
        except ValueError:
            arrival_date = date.today()

        product = Product.query.get_or_404(product_id)

        # 1. Generate Incoming Code
        incoming_code = generate_code('INC', IncomingGood, 'incoming_code')

        # 2. Create Incoming Good Record
        incoming = IncomingGood(
            incoming_code=incoming_code,
            product_id=product.id,
            supplier_id=supplier_id,
            quantity_received=quantity_received,
            date_of_arrival=arrival_date,
            invoice_number=invoice_number,
            purchase_price=purchase_price if purchase_price > 0 else product.purchase_price,
            month=arrival_date.month,
            year=arrival_date.year,
            notes=notes
        )
        db.session.add(incoming)

        # 3. Update Product Stock
        product.available_quantity += quantity_received
        product.quantity_received += quantity_received
        if purchase_price > 0:
            product.purchase_price = purchase_price

        # 4. Record Stock Transaction
        transaction = StockTransaction(
            product_id=product.id,
            transaction_type='Incoming (Restock)',
            quantity=quantity_received,
            balance_after=product.available_quantity,
            reference_id=invoice_number,
            notes=f'Received shipment under invoice #{invoice_number} ({incoming_code})'
        )
        db.session.add(transaction)

        # 5. Create Notification
        notif = Notification(
            title=f"New Incoming Goods: {product.name}",
            message=f"Received {quantity_received} {product.unit} of {product.name} (Invoice: {invoice_number}). Available stock: {product.available_quantity}.",
            type="success",
            link=f"/inventory/{product.id}"
        )
        db.session.add(notif)

        db.session.commit()
        flash(f'Successfully recorded incoming shipment {incoming_code} for {product.name} (+{quantity_received} {product.unit})!', 'success')
        return redirect(url_for('incoming.index'))

    preselected_product_id = request.args.get('product_id', type=int)

    return render_template(
        'incoming/add.html',
        products=products,
        suppliers=suppliers,
        preselected_product_id=preselected_product_id,
        today=date.today().strftime('%Y-%m-%d')
    )


@incoming_bp.route('/export')
@login_required
def export_csv():
    selected_year = request.args.get('year', type=int)
    selected_month = request.args.get('month', type=int)
    supplier_id = request.args.get('supplier_id', type=int)

    query = IncomingGood.query.join(Product).join(Supplier)
    if selected_year:
        query = query.filter(IncomingGood.year == selected_year)
    if selected_month:
        query = query.filter(IncomingGood.month == selected_month)
    if supplier_id:
        query = query.filter(IncomingGood.supplier_id == supplier_id)

    records = query.order_by(IncomingGood.date_of_arrival.desc()).all()

    headers = [
        'Incoming Code', 'Invoice Number', 'Date of Arrival', 'Month', 'Year',
        'Product Code', 'Product Name', 'Supplier Name', 'Quantity Received', 'Unit', 'Unit Price (₹)', 'Total Value (₹)', 'Notes'
    ]

    rows = []
    for r in records:
        rows.append([
            r.incoming_code,
            r.invoice_number,
            r.date_of_arrival.strftime('%Y-%m-%d'),
            r.month,
            r.year,
            r.product.product_code,
            r.product.name,
            r.supplier.name,
            r.quantity_received,
            r.product.unit,
            f"{r.purchase_price:.2f}",
            f"{(r.quantity_received * r.purchase_price):.2f}",
            r.notes or ''
        ])

    filename = f"incoming_goods_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv_response(filename, headers, rows)
