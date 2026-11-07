from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, StorageLocation, Product, Category
from helpers import login_required

locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    warehouse_filter = request.args.get('warehouse', '').strip()

    # Get all warehouses available
    all_locations = StorageLocation.query.all()
    warehouses = sorted(list(set(loc.warehouse for loc in all_locations)))

    # Query products with their location information
    query = Product.query.join(StorageLocation)

    if search_query:
        query = query.filter(
            (Product.name.ilike(f'%{search_query}%')) |
            (Product.product_code.ilike(f'%{search_query}%')) |
            (StorageLocation.rack.ilike(f'%{search_query}%')) |
            (StorageLocation.shelf.ilike(f'%{search_query}%')) |
            (StorageLocation.section.ilike(f'%{search_query}%'))
        )

    if warehouse_filter:
        query = query.filter(StorageLocation.warehouse == warehouse_filter)

    products = query.order_by(StorageLocation.warehouse, StorageLocation.section, StorageLocation.rack, StorageLocation.shelf).all()

    # Visual map organization: Warehouse -> Section -> Racks
    warehouse_map = {}
    for loc in all_locations:
        if loc.warehouse not in warehouse_map:
            warehouse_map[loc.warehouse] = {}
        if loc.section not in warehouse_map[loc.warehouse]:
            warehouse_map[loc.warehouse][loc.section] = []
        warehouse_map[loc.warehouse][loc.section].append(loc)

    return render_template(
        'locations/index.html',
        products=products,
        warehouses=warehouses,
        warehouse_map=warehouse_map,
        all_locations=all_locations,
        search_query=search_query,
        warehouse_filter=warehouse_filter
    )


@locations_bp.route('/update-product-location', methods=['POST'])
@login_required
def update_product_location():
    product_id = request.form.get('product_id', type=int)
    new_location_id = request.form.get('location_id', type=int)

    if not product_id or not new_location_id:
        flash('Invalid product or location selection.', 'danger')
        return redirect(url_for('locations.index'))

    product = Product.query.get_or_404(product_id)
    new_location = StorageLocation.query.get_or_404(new_location_id)

    old_loc = product.storage_location.full_code
    product.storage_location_id = new_location.id
    db.session.commit()

    flash(f'Storage location for {product.name} relocated from [{old_loc}] to [{new_location.full_code}].', 'success')
    return redirect(request.referrer or url_for('locations.index'))


@locations_bp.route('/add', methods=['POST'])
@login_required
def add_location():
    warehouse = request.form.get('warehouse', '').strip()
    section = request.form.get('section', '').strip()
    rack = request.form.get('rack', '').strip()
    shelf = request.form.get('shelf', '').strip()
    capacity = request.form.get('capacity', 500, type=int)
    description = request.form.get('description', '').strip()

    if not warehouse or not section or not rack or not shelf:
        flash('Warehouse, Section, Rack, and Shelf are all required.', 'danger')
        return redirect(url_for('locations.index'))

    # Check if location already exists
    existing = StorageLocation.query.filter_by(
        warehouse=warehouse, section=section, rack=rack, shelf=shelf
    ).first()
    if existing:
        flash('This storage slot already exists in the system.', 'warning')
        return redirect(url_for('locations.index'))

    new_loc = StorageLocation(
        warehouse=warehouse,
        section=section,
        rack=rack,
        shelf=shelf,
        capacity=capacity,
        description=description
    )
    db.session.add(new_loc)
    db.session.commit()

    flash(f'New storage location [{new_loc.full_code}] added successfully.', 'success')
    return redirect(url_for('locations.index'))
