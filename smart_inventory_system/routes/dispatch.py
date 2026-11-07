from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, DispatchOrder, Product, Transporter, StockTransaction, Notification
from helpers import login_required, generate_code, export_csv_response

dispatch_bp = Blueprint('dispatch', __name__)

@dispatch_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', '')
    transporter_id = request.args.get('transporter_id', type=int)
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = DispatchOrder.query.join(Product)

    if status_filter:
        query = query.filter(DispatchOrder.delivery_status == status_filter)

    if transporter_id:
        query = query.filter(DispatchOrder.transporter_id == transporter_id)

    if search_query:
        query = query.filter(
            (DispatchOrder.dispatch_code.ilike(f'%{search_query}%')) |
            (Product.name.ilike(f'%{search_query}%')) |
            (DispatchOrder.destination_address.ilike(f'%{search_query}%')) |
            (DispatchOrder.receiver_name.ilike(f'%{search_query}%')) |
            (DispatchOrder.vehicle_number.ilike(f'%{search_query}%'))
        )

    query = query.order_by(DispatchOrder.dispatch_date.desc(), DispatchOrder.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    transporters = Transporter.query.order_by(Transporter.name.asc()).all()

    # Status counts for filter pills
    counts = {
        'all': DispatchOrder.query.count(),
        'Pending': DispatchOrder.query.filter_by(delivery_status='Pending').count(),
        'Ready for Dispatch': DispatchOrder.query.filter_by(delivery_status='Ready for Dispatch').count(),
        'In Transit': DispatchOrder.query.filter_by(delivery_status='In Transit').count(),
        'Delivered': DispatchOrder.query.filter_by(delivery_status='Delivered').count(),
        'Cancelled': DispatchOrder.query.filter_by(delivery_status='Cancelled').count(),
    }

    return render_template(
        'dispatch/index.html',
        orders=orders,
        pagination=pagination,
        transporters=transporters,
        status_filter=status_filter,
        transporter_id=transporter_id,
        search_query=search_query,
        counts=counts
    )


@dispatch_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    products = Product.query.order_by(Product.name.asc()).all()
    transporters = Transporter.query.filter(Transporter.status != 'Inactive').order_by(Transporter.name.asc()).all()

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        transporter_id = request.form.get('transporter_id', type=int)
        quantity_dispatched = request.form.get('quantity_dispatched', 0, type=int)
        expected_delivery_date_str = request.form.get('expected_delivery_date')
        destination_address = request.form.get('destination_address', '').strip()
        receiver_name = request.form.get('receiver_name', '').strip()
        receiver_phone = request.form.get('receiver_phone', '').strip()
        vehicle_number = request.form.get('vehicle_number', '').strip()
        driver_contact = request.form.get('driver_contact', '').strip()
        delivery_status = request.form.get('delivery_status', 'Pending')
        notes = request.form.get('notes', '').strip()

        # Validation
        if not product_id or not quantity_dispatched or quantity_dispatched <= 0 or not destination_address or not receiver_name or not receiver_phone or not expected_delivery_date_str:
            flash('Please complete all required fields and enter a valid quantity greater than zero.', 'danger')
            return render_template('dispatch/create.html', products=products, transporters=transporters, today=date.today().strftime('%Y-%m-%d'))

        product = Product.query.get_or_404(product_id)

        # 1. Check if product is expired!
        if product.is_expired:
            flash(f'Cannot dispatch product "{product.name}": This stock expired on {product.expiry_date.strftime("%d-%b-%Y")}. Expired goods cannot be distributed!', 'danger')
            return render_template('dispatch/create.html', products=products, transporters=transporters, today=date.today().strftime('%Y-%m-%d'))

        # 2. Check stock sufficiency
        if product.available_quantity < quantity_dispatched:
            flash(f'Insufficient stock for "{product.name}". Available: {product.available_quantity} {product.unit}, Requested: {quantity_dispatched} {product.unit}.', 'danger')
            return render_template('dispatch/create.html', products=products, transporters=transporters, today=date.today().strftime('%Y-%m-%d'))

        try:
            expected_date = datetime.strptime(expected_delivery_date_str, '%Y-%m-%d').date()
        except ValueError:
            expected_date = date.today()

        # Auto-fill transporter details if chosen and not manually overwritten
        transporter = db.session.get(Transporter, transporter_id) if transporter_id else None
        if transporter:
            if not vehicle_number:
                vehicle_number = transporter.vehicle_number
            if not driver_contact:
                driver_contact = f"{transporter.driver_name} ({transporter.driver_contact})"

        dispatch_code = generate_code('DSP', DispatchOrder, 'dispatch_code')

        order = DispatchOrder(
            dispatch_code=dispatch_code,
            product_id=product.id,
            transporter_id=transporter_id if transporter_id else None,
            quantity_dispatched=quantity_dispatched,
            dispatch_date=datetime.now(),
            expected_delivery_date=expected_date,
            destination_address=destination_address,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            vehicle_number=vehicle_number,
            driver_contact=driver_contact,
            delivery_status=delivery_status,
            notes=notes
        )
        db.session.add(order)

        # If order is created in any non-cancelled state, deduct stock immediately
        if delivery_status != 'Cancelled':
            product.available_quantity -= quantity_dispatched
            product.dispatched_quantity += quantity_dispatched

            # Record Stock Transaction
            tx = StockTransaction(
                product_id=product.id,
                transaction_type='Dispatched',
                quantity=-quantity_dispatched,
                balance_after=product.available_quantity,
                reference_id=dispatch_code,
                notes=f'Dispatched to {receiver_name} via {vehicle_number or "Courier"}'
            )
            db.session.add(tx)

            # Update transporter status if on trip
            if transporter and delivery_status in ['In Transit', 'Ready for Dispatch']:
                transporter.status = 'On Trip'

        # Notification
        notif = Notification(
            title=f"Dispatch Created: {dispatch_code}",
            message=f"Dispatched {quantity_dispatched} {product.unit} of {product.name} to {receiver_name}. Status: {delivery_status}.",
            type="info",
            link=f"/dispatch/{order.id}"
        )
        db.session.add(notif)

        db.session.commit()
        flash(f'Dispatch order {dispatch_code} successfully created and stock deducted.', 'success')
        return redirect(url_for('dispatch.detail', order_id=order.id))

    preselected_product_id = request.args.get('product_id', type=int)
    return render_template(
        'dispatch/create.html',
        products=products,
        transporters=transporters,
        preselected_product_id=preselected_product_id,
        today=date.today().strftime('%Y-%m-%d')
    )


@dispatch_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    order = DispatchOrder.query.get_or_404(order_id)
    transporters = Transporter.query.filter(Transporter.status != 'Inactive').all()
    return render_template('dispatch/detail.html', order=order, transporters=transporters)


@dispatch_bp.route('/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_status(order_id):
    order = DispatchOrder.query.get_or_404(order_id)
    new_status = request.form.get('delivery_status')
    notes = request.form.get('notes', '').strip()

    valid_statuses = ['Pending', 'Ready for Dispatch', 'In Transit', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        flash('Invalid status value provided.', 'danger')
        return redirect(url_for('dispatch.detail', order_id=order.id))

    old_status = order.delivery_status
    product = order.product

    # Handle Stock Restoration on Cancellation
    if new_status == 'Cancelled' and old_status != 'Cancelled':
        # Restore stock back to product
        product.available_quantity += order.quantity_dispatched
        product.dispatched_quantity = max(0, product.dispatched_quantity - order.quantity_dispatched)

        # Log restoration transaction
        tx = StockTransaction(
            product_id=product.id,
            transaction_type='Restored (Cancelled Dispatch)',
            quantity=order.quantity_dispatched,
            balance_after=product.available_quantity,
            reference_id=order.dispatch_code,
            notes=f'Restored due to cancellation of dispatch #{order.dispatch_code}'
        )
        db.session.add(tx)

        if order.transporter:
            order.transporter.status = 'Available'

        flash(f'Dispatch {order.dispatch_code} has been CANCELLED. {order.quantity_dispatched} {product.unit} have been restored back to available stock.', 'warning')

    # Handle Reopening a Cancelled order
    elif old_status == 'Cancelled' and new_status != 'Cancelled':
        # Re-check stock
        if product.is_expired:
            flash(f'Cannot reactivate dispatch {order.dispatch_code}: Product "{product.name}" has expired!', 'danger')
            return redirect(url_for('dispatch.detail', order_id=order.id))
        if product.available_quantity < order.quantity_dispatched:
            flash(f'Cannot reactivate dispatch: Insufficient stock. Available: {product.available_quantity}, Needed: {order.quantity_dispatched}.', 'danger')
            return redirect(url_for('dispatch.detail', order_id=order.id))

        product.available_quantity -= order.quantity_dispatched
        product.dispatched_quantity += order.quantity_dispatched

        tx = StockTransaction(
            product_id=product.id,
            transaction_type='Dispatched',
            quantity=-order.quantity_dispatched,
            balance_after=product.available_quantity,
            reference_id=order.dispatch_code,
            notes=f'Re-deducted upon reactivating dispatch #{order.dispatch_code}'
        )
        db.session.add(tx)
        flash(f'Dispatch {order.dispatch_code} reactivated and stock re-allocated.', 'info')

    # Status is Delivered
    if new_status == 'Delivered':
        order.actual_delivery_date = date.today()
        if order.transporter:
            order.transporter.status = 'Available'

        notif = Notification(
            title=f"Delivery Completed: {order.dispatch_code}",
            message=f"Order {order.dispatch_code} ({product.name}) has been safely delivered to {order.receiver_name} on {order.actual_delivery_date.strftime('%d-%b-%Y')}.",
            type="success",
            link=f"/dispatch/{order.id}"
        )
        db.session.add(notif)
        flash(f'Order {order.dispatch_code} marked as DELIVERED.', 'success')

    # Status is In Transit
    elif new_status == 'In Transit':
        if order.transporter:
            order.transporter.status = 'On Trip'
        flash(f'Order {order.dispatch_code} is now IN TRANSIT.', 'info')

    order.delivery_status = new_status
    if notes:
        order.notes = (order.notes or '') + f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Status changed from {old_status} to {new_status}: {notes}"

    db.session.commit()
    return redirect(url_for('dispatch.detail', order_id=order.id))


@dispatch_bp.route('/export')
@login_required
def export_csv():
    status_filter = request.args.get('status', '')
    transporter_id = request.args.get('transporter_id', type=int)

    query = DispatchOrder.query.join(Product)
    if status_filter:
        query = query.filter(DispatchOrder.delivery_status == status_filter)
    if transporter_id:
        query = query.filter(DispatchOrder.transporter_id == transporter_id)

    orders = query.order_by(DispatchOrder.dispatch_date.desc()).all()

    headers = [
        'Dispatch ID', 'Product Code', 'Product Name', 'Quantity Dispatched', 'Unit',
        'Dispatch Date', 'Expected Delivery', 'Actual Delivery', 'Status',
        'Transporter', 'Vehicle Number', 'Driver Contact', 'Receiver Name', 'Receiver Phone', 'Destination'
    ]

    rows = []
    for o in orders:
        rows.append([
            o.dispatch_code,
            o.product.product_code,
            o.product.name,
            o.quantity_dispatched,
            o.product.unit,
            o.dispatch_date.strftime('%Y-%m-%d %H:%M'),
            o.expected_delivery_date.strftime('%Y-%m-%d'),
            o.actual_delivery_date.strftime('%Y-%m-%d') if o.actual_delivery_date else 'N/A',
            o.delivery_status,
            o.transporter.name if o.transporter else 'N/A',
            o.vehicle_number or 'N/A',
            o.driver_contact or 'N/A',
            o.receiver_name,
            o.receiver_phone,
            o.destination_address.replace('\n', ' ')
        ])

    filename = f"dispatch_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv_response(filename, headers, rows)
