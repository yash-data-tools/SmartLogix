from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Transporter, DispatchOrder
from helpers import login_required, generate_code

transporters_bp = Blueprint('transporters', __name__)

@transporters_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')

    query = Transporter.query

    if search_query:
        query = query.filter(
            (Transporter.name.ilike(f'%{search_query}%')) |
            (Transporter.transporter_code.ilike(f'%{search_query}%')) |
            (Transporter.vehicle_number.ilike(f'%{search_query}%')) |
            (Transporter.driver_name.ilike(f'%{search_query}%'))
        )

    if status_filter:
        query = query.filter(Transporter.status == status_filter)

    transporters = query.order_by(Transporter.name.asc()).all()

    return render_template(
        'transporters/index.html',
        transporters=transporters,
        search_query=search_query,
        status_filter=status_filter
    )


@transporters_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        email = request.form.get('email', '').strip()
        vehicle_number = request.form.get('vehicle_number', '').strip().upper()
        vehicle_type = request.form.get('vehicle_type', 'Medium Cargo Truck').strip()
        driver_name = request.form.get('driver_name', '').strip()
        driver_contact = request.form.get('driver_contact', '').strip()
        address = request.form.get('address', '').strip()
        status = request.form.get('status', 'Available')

        if not name or not contact_number or not vehicle_number or not driver_name or not driver_contact:
            flash('Company Name, Contact, Vehicle Number, Driver Name, and Driver Contact are required.', 'danger')
            return render_template('transporters/add.html')

        transporter_code = generate_code('TRP', Transporter, 'transporter_code')

        new_transporter = Transporter(
            transporter_code=transporter_code,
            name=name,
            contact_number=contact_number,
            email=email,
            vehicle_number=vehicle_number,
            vehicle_type=vehicle_type,
            driver_name=driver_name,
            driver_contact=driver_contact,
            address=address,
            status=status
        )
        db.session.add(new_transporter)
        db.session.commit()

        flash(f'Transporter "{name}" ({transporter_code}) registered successfully!', 'success')
        return redirect(url_for('transporters.index'))

    return render_template('transporters/add.html')


@transporters_bp.route('/<int:transporter_id>')
@login_required
def detail(transporter_id):
    transporter = Transporter.query.get_or_404(transporter_id)
    deliveries = DispatchOrder.query.filter_by(transporter_id=transporter.id).order_by(DispatchOrder.dispatch_date.desc()).all()

    completed_trips = sum(1 for d in deliveries if d.delivery_status == 'Delivered')
    active_trips = sum(1 for d in deliveries if d.delivery_status in ['In Transit', 'Ready for Dispatch'])

    return render_template(
        'transporters/detail.html',
        transporter=transporter,
        deliveries=deliveries,
        completed_trips=completed_trips,
        active_trips=active_trips
    )


@transporters_bp.route('/<int:transporter_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(transporter_id):
    transporter = Transporter.query.get_or_404(transporter_id)

    if request.method == 'POST':
        transporter.name = request.form.get('name', '').strip()
        transporter.contact_number = request.form.get('contact_number', '').strip()
        transporter.email = request.form.get('email', '').strip()
        transporter.vehicle_number = request.form.get('vehicle_number', '').strip().upper()
        transporter.vehicle_type = request.form.get('vehicle_type', 'Medium Cargo Truck').strip()
        transporter.driver_name = request.form.get('driver_name', '').strip()
        transporter.driver_contact = request.form.get('driver_contact', '').strip()
        transporter.address = request.form.get('address', '').strip()
        transporter.status = request.form.get('status', 'Available')

        db.session.commit()
        flash(f'Transporter {transporter.name} details updated.', 'success')
        return redirect(url_for('transporters.detail', transporter_id=transporter.id))

    return render_template('transporters/edit.html', transporter=transporter)


@transporters_bp.route('/<int:transporter_id>/delete', methods=['POST'])
@login_required
def delete(transporter_id):
    transporter = Transporter.query.get_or_404(transporter_id)

    # Check if there are active deliveries
    has_active = any(d.delivery_status in ['Pending', 'Ready for Dispatch', 'In Transit'] for d in transporter.dispatch_orders)
    if has_active:
        flash(f'Cannot delete transporter "{transporter.name}" because they have active deliveries in progress.', 'danger')
        return redirect(url_for('transporters.index'))

    name = transporter.name
    db.session.delete(transporter)
    db.session.commit()
    flash(f'Transporter {name} deleted.', 'info')
    return redirect(url_for('transporters.index'))
