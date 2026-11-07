from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def get_current_time():
    return datetime.now()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='Admin') # Admin, Manager, Shopkeeper, Warehouse Staff
    created_at = db.Column(db.DateTime, default=get_current_time)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), default='fa-box')

    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time)

    products = db.relationship('Product', backref='supplier', lazy=True)
    incoming_records = db.relationship('IncomingGood', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.name} - {self.company_name}>'


class StorageLocation(db.Model):
    __tablename__ = 'storage_locations'

    id = db.Column(db.Integer, primary_key=True)
    warehouse = db.Column(db.String(50), nullable=False) # e.g. "Warehouse A"
    section = db.Column(db.String(50), nullable=False)   # e.g. "Section 2"
    rack = db.Column(db.String(50), nullable=False)      # e.g. "Rack 05"
    shelf = db.Column(db.String(50), nullable=False)     # e.g. "Shelf 03"
    capacity = db.Column(db.Integer, default=500)
    description = db.Column(db.String(200), nullable=True)

    products = db.relationship('Product', backref='storage_location', lazy=True)

    @property
    def full_code(self):
        return f"{self.warehouse} | {self.section} | {self.rack} | {self.shelf}"

    @property
    def short_code(self):
        return f"{self.warehouse.replace('Warehouse ', 'WH-')}:{self.rack}:{self.shelf}"

    def __repr__(self):
        return f'<StorageLocation {self.full_code}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    storage_location_id = db.Column(db.Integer, db.ForeignKey('storage_locations.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)

    quantity_received = db.Column(db.Integer, default=0, nullable=False)
    available_quantity = db.Column(db.Integer, default=0, nullable=False)
    dispatched_quantity = db.Column(db.Integer, default=0, nullable=False)
    unit = db.Column(db.String(30), default='Pieces', nullable=False) # Pieces, Boxes, Kg, Litres, Cartons
    purchase_price = db.Column(db.Float, default=0.0)
    arrival_date = db.Column(db.Date, default=date.today, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    low_stock_threshold = db.Column(db.Integer, default=15, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)

    incoming_records = db.relationship('IncomingGood', backref='product', lazy=True, cascade='all, delete-orphan')
    dispatch_orders = db.relationship('DispatchOrder', backref='product', lazy=True, cascade='all, delete-orphan')
    stock_transactions = db.relationship('StockTransaction', backref='product', lazy=True, cascade='all, delete-orphan', order_by='desc(StockTransaction.created_at)')

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @property
    def is_expiring_soon_7d(self):
        if not self.expiry_date:
            return False
        today = date.today()
        return today <= self.expiry_date <= today + timedelta(days=7)

    @property
    def is_expiring_soon_30d(self):
        if not self.expiry_date:
            return False
        today = date.today()
        return today + timedelta(days=7) < self.expiry_date <= today + timedelta(days=30)

    @property
    def is_low_stock(self):
        return self.available_quantity <= self.low_stock_threshold

    @property
    def expiry_status_info(self):
        if not self.expiry_date:
            return {'status': 'Safe (No Expiry)', 'class': 'badge-safe', 'badge': 'bg-success', 'code': 'safe'}
        today = date.today()
        diff = (self.expiry_date - today).days
        if diff < 0:
            return {'status': f'Expired ({abs(diff)}d ago)', 'class': 'badge-expired', 'badge': 'bg-danger', 'code': 'expired'}
        elif diff <= 7:
            return {'status': f'Critical ({diff}d left)', 'class': 'badge-expiring-soon', 'badge': 'bg-danger', 'code': 'expiring_7d'}
        elif diff <= 30:
            return {'status': f'Warning ({diff}d left)', 'class': 'badge-expiring-soon', 'badge': 'bg-warning text-dark', 'code': 'expiring_30d'}
        else:
            return {'status': f'Safe ({diff}d left)', 'class': 'badge-safe', 'badge': 'bg-success', 'code': 'safe'}

    def __repr__(self):
        return f'<Product {self.product_code} - {self.name}>'


class IncomingGood(db.Model):
    __tablename__ = 'incoming_goods'

    id = db.Column(db.Integer, primary_key=True)
    incoming_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    quantity_received = db.Column(db.Integer, nullable=False)
    date_of_arrival = db.Column(db.Date, default=date.today, nullable=False)
    invoice_number = db.Column(db.String(60), nullable=False)
    purchase_price = db.Column(db.Float, default=0.0)
    month = db.Column(db.Integer, nullable=False) # 1-12
    year = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_current_time)

    def __repr__(self):
        return f'<IncomingGood {self.incoming_code} - {self.quantity_received} units>'


class Transporter(db.Model):
    __tablename__ = 'transporters'

    id = db.Column(db.Integer, primary_key=True)
    transporter_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    contact_number = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    vehicle_number = db.Column(db.String(40), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False) # e.g. Heavy Truck, Cargo Van, Refrigerated Truck, Container
    driver_name = db.Column(db.String(100), nullable=False)
    driver_contact = db.Column(db.String(30), nullable=False)
    address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='Available') # Available, On Trip, Maintenance, Inactive
    created_at = db.Column(db.DateTime, default=get_current_time)

    dispatch_orders = db.relationship('DispatchOrder', backref='transporter', lazy=True)

    def __repr__(self):
        return f'<Transporter {self.name} - {self.vehicle_number}>'


class DispatchOrder(db.Model):
    __tablename__ = 'dispatch_orders'

    id = db.Column(db.Integer, primary_key=True)
    dispatch_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    transporter_id = db.Column(db.Integer, db.ForeignKey('transporters.id'), nullable=True)
    quantity_dispatched = db.Column(db.Integer, nullable=False)
    dispatch_date = db.Column(db.DateTime, default=get_current_time, nullable=False)
    expected_delivery_date = db.Column(db.Date, nullable=False)
    actual_delivery_date = db.Column(db.Date, nullable=True)
    destination_address = db.Column(db.Text, nullable=False)
    receiver_name = db.Column(db.String(100), nullable=False)
    receiver_phone = db.Column(db.String(30), nullable=False)
    vehicle_number = db.Column(db.String(40), nullable=True)
    driver_contact = db.Column(db.String(30), nullable=True)
    delivery_status = db.Column(db.String(30), default='Pending', nullable=False)
    # Statuses: Pending, Ready for Dispatch, In Transit, Delivered, Cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_current_time)

    @property
    def status_badge(self):
        status_map = {
            'Pending': 'bg-secondary',
            'Ready for Dispatch': 'bg-info text-dark',
            'In Transit': 'bg-primary',
            'Delivered': 'bg-success',
            'Cancelled': 'bg-danger'
        }
        return status_map.get(self.delivery_status, 'bg-secondary')

    def __repr__(self):
        return f'<DispatchOrder {self.dispatch_code} - {self.delivery_status}>'


class StockTransaction(db.Model):
    __tablename__ = 'stock_transactions'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    transaction_type = db.Column(db.String(40), nullable=False) # 'Incoming', 'Dispatched', 'Restored (Cancelled)', 'Adjustment'
    quantity = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    reference_id = db.Column(db.String(60), nullable=True) # Invoice number or Dispatch Code
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=get_current_time)

    def __repr__(self):
        return f'<StockTransaction {self.transaction_type}: {self.quantity} units>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default='info') # info, warning, danger, success
    link = db.Column(db.String(200), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_current_time)

    def __repr__(self):
        return f'<Notification {self.title}>'
