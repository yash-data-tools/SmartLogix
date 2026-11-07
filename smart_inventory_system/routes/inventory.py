from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Product, Category, Supplier, StorageLocation, StockTransaction, IncomingGood, DispatchOrder
from helpers import login_required, generate_code

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
def index():
    # Filtering, Searching, Sorting, and Pagination parameters
    search_query = request.args.get('search', '').strip()
    category_id = request.args.get('category', '')
    expiry_filter = request.args.get('expiry', '')
    stock_filter = request.args.get('stock', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Product.query

    # Search filter (name or product_code)
    if search_query:
        query = query.filter(
            (Product.name.ilike(f'%{search_query}%')) |
            (Product.product_code.ilike(f'%{search_query}%'))
        )

    # Category filter
    if category_id and category_id.isdigit():
        query = query.filter(Product.category_id == int(category_id))

    # Expiry filter
    today = date.today()
    if expiry_filter == 'expired':
        query = query.filter(Product.expiry_date.isnot(None), Product.expiry_date < today)
    elif expiry_filter == 'expiring_7d':
        query = query.filter(Product.expiry_date.isnot(None), Product.expiry_date >= today, Product.expiry_date <= today + timedelta(days=7))
    elif expiry_filter == 'expiring_30d':
        query = query.filter(Product.expiry_date.isnot(None), Product.expiry_date > today + timedelta(days=7), Product.expiry_date <= today + timedelta(days=30))
    elif expiry_filter == 'safe':
        query = query.filter((Product.expiry_date.is_(None)) | (Product.expiry_date > today + timedelta(days=30)))

    # Stock filter
    if stock_filter == 'low':
        query = query.filter(Product.available_quantity <= Product.low_stock_threshold, Product.available_quantity > 0)
    elif stock_filter == 'out':
        query = query.filter(Product.available_quantity <= 0)
    elif stock_filter == 'in_stock':
        query = query.filter(Product.available_quantity > Product.low_stock_threshold)

    # Sorting
    sort_column = {
        'name': Product.name,
        'quantity': Product.available_quantity,
        'arrival_date': Product.arrival_date,
        'expiry_date': Product.expiry_date,
        'price': Product.purchase_price,
        'created_at': Product.created_at
    }.get(sort_by, Product.created_at)

    if sort_dir == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'inventory/index.html',
        products=products,
        pagination=pagination,
        categories=categories,
        search_query=search_query,
        category_id=category_id,
        expiry_filter=expiry_filter,
        stock_filter=stock_filter,
        sort_by=sort_by,
        sort_dir=sort_dir
    )


@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    categories = Category.query.order_by(Category.name.asc()).all()
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    locations = StorageLocation.query.order_by(StorageLocation.warehouse.asc(), StorageLocation.section.asc()).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int)
        storage_location_id = request.form.get('storage_location_id', type=int)
        description = request.form.get('description', '').strip()
        initial_quantity = request.form.get('initial_quantity', 0, type=int)
        unit = request.form.get('unit', 'Pieces').strip()
        purchase_price = request.form.get('purchase_price', 0.0, type=float)
        arrival_date_str = request.form.get('arrival_date')
        expiry_date_str = request.form.get('expiry_date')
        low_stock_threshold = request.form.get('low_stock_threshold', 15, type=int)

        if not name or not category_id or not supplier_id or not storage_location_id:
            flash('Product Name, Category, Supplier, and Storage Location are required.', 'danger')
            return render_template('inventory/add.html', categories=categories, suppliers=suppliers, locations=locations)

        try:
            arrival_date = datetime.strptime(arrival_date_str, '%Y-%m-%d').date() if arrival_date_str else date.today()
        except ValueError:
            arrival_date = date.today()

        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                expiry_date = None

        product_code = generate_code('PRD', Product, 'product_code')

        new_product = Product(
            product_code=product_code,
            name=name,
            category_id=category_id,
            supplier_id=supplier_id,
            storage_location_id=storage_location_id,
            description=description,
            quantity_received=initial_quantity,
            available_quantity=initial_quantity,
            dispatched_quantity=0,
            unit=unit,
            purchase_price=purchase_price,
            arrival_date=arrival_date,
            expiry_date=expiry_date,
            low_stock_threshold=low_stock_threshold
        )
        db.session.add(new_product)
        db.session.flush() # obtain new_product.id

        # Record Initial Stock Transaction
        if initial_quantity > 0:
            transaction = StockTransaction(
                product_id=new_product.id,
                transaction_type='Incoming (Initial Stock)',
                quantity=initial_quantity,
                balance_after=initial_quantity,
                reference_id='INIT-STOCK',
                notes=f'Initial batch stock added for {new_product.name}'
            )
            db.session.add(transaction)

            # Record Incoming Good
            incoming = IncomingGood(
                incoming_code=generate_code('INC', IncomingGood, 'incoming_code'),
                product_id=new_product.id,
                supplier_id=supplier_id,
                quantity_received=initial_quantity,
                date_of_arrival=arrival_date,
                invoice_number=f"INV-INIT-{product_code}",
                purchase_price=purchase_price,
                month=arrival_date.month,
                year=arrival_date.year,
                notes='Initial stock intake on product creation'
            )
            db.session.add(incoming)

        db.session.commit()
        flash(f'Product "{new_product.name}" ({new_product.product_code}) created successfully!', 'success')
        return redirect(url_for('inventory.detail', product_id=new_product.id))

    return render_template(
        'inventory/add.html',
        categories=categories,
        suppliers=suppliers,
        locations=locations,
        today=date.today().strftime('%Y-%m-%d')
    )


@inventory_bp.route('/<int:product_id>')
@login_required
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    transactions = StockTransaction.query.filter_by(product_id=product.id).order_by(StockTransaction.created_at.desc()).all()
    dispatch_orders = DispatchOrder.query.filter_by(product_id=product.id).order_by(DispatchOrder.dispatch_date.desc()).all()
    incoming_records = IncomingGood.query.filter_by(product_id=product.id).order_by(IncomingGood.date_of_arrival.desc()).all()
    locations = StorageLocation.query.order_by(StorageLocation.warehouse.asc()).all()

    return render_template(
        'inventory/detail.html',
        product=product,
        transactions=transactions,
        dispatch_orders=dispatch_orders,
        incoming_records=incoming_records,
        locations=locations
    )


@inventory_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name.asc()).all()
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    locations = StorageLocation.query.order_by(StorageLocation.warehouse.asc(), StorageLocation.section.asc()).all()

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.category_id = request.form.get('category_id', type=int)
        product.supplier_id = request.form.get('supplier_id', type=int)
        product.storage_location_id = request.form.get('storage_location_id', type=int)
        product.description = request.form.get('description', '').strip()
        product.unit = request.form.get('unit', 'Pieces').strip()
        product.purchase_price = request.form.get('purchase_price', 0.0, type=float)
        product.low_stock_threshold = request.form.get('low_stock_threshold', 15, type=int)

        expiry_date_str = request.form.get('expiry_date')
        if expiry_date_str:
            try:
                product.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            product.expiry_date = None

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully.', 'success')
        return redirect(url_for('inventory.detail', product_id=product.id))

    return render_template(
        'inventory/edit.html',
        product=product,
        categories=categories,
        suppliers=suppliers,
        locations=locations
    )


@inventory_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    code = product.product_code

    db.session.delete(product)
    db.session.commit()
    flash(f'Product {code} ({name}) was successfully deleted.', 'info')
    return redirect(url_for('inventory.index'))
