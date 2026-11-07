from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Supplier, Product, IncomingGood
from helpers import login_required, generate_code
from sqlalchemy import func

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    query = Supplier.query

    if search_query:
        query = query.filter(
            (Supplier.name.ilike(f'%{search_query}%')) |
            (Supplier.company_name.ilike(f'%{search_query}%')) |
            (Supplier.supplier_code.ilike(f'%{search_query}%')) |
            (Supplier.email.ilike(f'%{search_query}%'))
        )

    suppliers = query.order_by(Supplier.name.asc()).all()
    return render_template('suppliers/index.html', suppliers=suppliers, search_query=search_query)


@suppliers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        if not name or not company_name or not phone or not email or not address:
            flash('All supplier fields are required.', 'danger')
            return render_template('suppliers/add.html')

        supplier_code = generate_code('SUP', Supplier, 'supplier_code')

        new_supplier = Supplier(
            supplier_code=supplier_code,
            name=name,
            company_name=company_name,
            phone=phone,
            email=email,
            address=address
        )
        db.session.add(new_supplier)
        db.session.commit()

        flash(f'Supplier "{company_name}" ({supplier_code}) added successfully!', 'success')
        return redirect(url_for('suppliers.index'))

    return render_template('suppliers/add.html')


@suppliers_bp.route('/<int:supplier_id>')
@login_required
def detail(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    products = Product.query.filter_by(supplier_id=supplier.id).all()
    incoming_records = IncomingGood.query.filter_by(supplier_id=supplier.id).order_by(IncomingGood.date_of_arrival.desc()).all()

    total_units_received = sum(rec.quantity_received for rec in incoming_records)
    total_spend = sum(rec.quantity_received * rec.purchase_price for rec in incoming_records)

    return render_template(
        'suppliers/detail.html',
        supplier=supplier,
        products=products,
        incoming_records=incoming_records,
        total_units_received=total_units_received,
        total_spend=total_spend
    )


@suppliers_bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    if request.method == 'POST':
        supplier.name = request.form.get('name', '').strip()
        supplier.company_name = request.form.get('company_name', '').strip()
        supplier.phone = request.form.get('phone', '').strip()
        supplier.email = request.form.get('email', '').strip()
        supplier.address = request.form.get('address', '').strip()

        db.session.commit()
        flash(f'Supplier {supplier.company_name} updated successfully.', 'success')
        return redirect(url_for('suppliers.detail', supplier_id=supplier.id))

    return render_template('suppliers/edit.html', supplier=supplier)


@suppliers_bp.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    # Check if products or incoming records are linked
    if supplier.products or supplier.incoming_records:
        flash(f'Cannot delete supplier "{supplier.company_name}" because they have active products or historical goods intake records linked.', 'warning')
        return redirect(url_for('suppliers.index'))

    name = supplier.company_name
    db.session.delete(supplier)
    db.session.commit()
    flash(f'Supplier {name} deleted successfully.', 'info')
    return redirect(url_for('suppliers.index'))
