import unittest
from datetime import date, timedelta
from app import create_app
from models import db, User, Product, Category, Supplier, StorageLocation, Transporter, DispatchOrder, IncomingGood, StockTransaction

class SystemTestSuite(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def login_admin(self):
        return self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

    def test_01_authentication(self):
        print("\n--- Testing Authentication ---")
        # 1. Login with bad password
        res = self.client.post('/auth/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b'Invalid username or password', res.data)
        print("  [PASS] Invalid password correctly rejected")

        # 2. Login with valid demo credentials
        res = self.login_admin()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Arthur Pendelton', res.data)
        print("  [PASS] Demo admin successfully authenticated")

    def test_02_dashboard_and_chart_api(self):
        print("\n--- Testing Dashboard & Dynamic Chart Data ---")
        self.login_admin()
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Overview', res.data)
        self.assertIn(b'Products', res.data)

        # Dynamic charts JSON endpoint
        api_res = self.client.get('/api/dashboard-charts')
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertIn('monthly_labels', data)
        self.assertIn('incoming_monthly', data)
        self.assertIn('dispatched_monthly', data)
        self.assertIn('category_labels', data)
        self.assertIn('expiry_counts', data)
        self.assertEqual(len(data['monthly_labels']), 6)
        print("  [PASS] Dashboard metrics and Chart.js JSON feeds validated")

    def test_03_inventory_crud(self):
        print("\n--- Testing Product Inventory CRUD ---")
        self.login_admin()

        # 1. List catalog
        res = self.client.get('/inventory/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Inventory Catalog', res.data)

        # 2. Add product
        cat = Category.query.first()
        sup = Supplier.query.first()
        loc = StorageLocation.query.first()

        add_res = self.client.post('/inventory/add', data={
            'name': 'High-Precision Laser Distance Meter',
            'category_id': cat.id,
            'supplier_id': sup.id,
            'storage_location_id': loc.id,
            'description': 'Optical sensor 0.05 - 80m laser rangefinder tool',
            'initial_quantity': 45,
            'unit': 'Pieces',
            'purchase_price': 34.50,
            'arrival_date': date.today().strftime('%Y-%m-%d'),
            'expiry_date': '', # Non-perishable
            'low_stock_threshold': 10
        }, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)
        self.assertIn(b'High-Precision Laser Distance Meter', add_res.data)

        new_product = Product.query.filter_by(name='High-Precision Laser Distance Meter').first()
        self.assertIsNotNone(new_product)
        self.assertEqual(new_product.available_quantity, 45)
        print(f"  [PASS] Product created: {new_product.product_code} with 45 units")

        # 3. Product Details view
        detail_res = self.client.get(f'/inventory/{new_product.id}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b'Stock Transaction Ledger', detail_res.data)
        print("  [PASS] Product detail page and transaction ledger verified")

    def test_04_incoming_goods_and_stock_intake(self):
        print("\n--- Testing Incoming Goods Restock Flow ---")
        self.login_admin()
        product = Product.query.filter_by(name='High-Precision Laser Distance Meter').first()
        initial_stock = product.available_quantity
        sup = Supplier.query.first()

        res = self.client.post('/incoming/add', data={
            'product_id': product.id,
            'supplier_id': sup.id,
            'quantity_received': 30,
            'arrival_date': date.today().strftime('%Y-%m-%d'),
            'invoice_number': 'INV-TEST-9900',
            'purchase_price': 34.50,
            'notes': 'Unit test restock intake'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Refresh product
        db.session.refresh(product)
        self.assertEqual(product.available_quantity, initial_stock + 30)
        print(f"  [PASS] Restocked +30 units. Stock increased from {initial_stock} to {product.available_quantity}")

    def test_05_goods_dispatch_and_stock_restoration(self):
        print("\n--- Testing Dispatch Orders, Expired Prevention & Cancellation Restoration ---")
        self.login_admin()

        # 1. Attempt dispatching an EXPIRED product -> Must be rejected!
        expired_product = Product.query.filter(Product.expiry_date < date.today()).first()
        self.assertIsNotNone(expired_product)

        bad_res = self.client.post('/dispatch/create', data={
            'product_id': expired_product.id,
            'quantity_dispatched': 5,
            'expected_delivery_date': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'destination_address': 'Test Clinic',
            'receiver_name': 'Test Consignee',
            'receiver_phone': '555-1234',
            'delivery_status': 'In Transit'
        }, follow_redirects=True)
        self.assertIn(b'Expired goods cannot be distributed', bad_res.data)
        print(f"  [PASS] Expired product ({expired_product.name}) dispatch was safely BLOCKED")

        # 2. Attempt dispatching more than available stock -> Must be rejected!
        valid_product = Product.query.filter_by(name='High-Precision Laser Distance Meter').first()
        insufficient_res = self.client.post('/dispatch/create', data={
            'product_id': valid_product.id,
            'quantity_dispatched': 99999,
            'expected_delivery_date': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'destination_address': 'Test Clinic',
            'receiver_name': 'Test Consignee',
            'receiver_phone': '555-1234',
            'delivery_status': 'In Transit'
        }, follow_redirects=True)
        self.assertIn(b'Insufficient stock', insufficient_res.data)
        print("  [PASS] Excessive dispatch quantity request was correctly rejected")

        # 3. Create Valid Dispatch Order
        stock_before = valid_product.available_quantity
        dispatch_qty = 20
        transporter = Transporter.query.first()

        order_res = self.client.post('/dispatch/create', data={
            'product_id': valid_product.id,
            'transporter_id': transporter.id,
            'quantity_dispatched': dispatch_qty,
            'expected_delivery_date': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'destination_address': '909 Tech Boulevard, Boston, MA',
            'receiver_name': 'Dr. Alan Grant',
            'receiver_phone': '+1 (555) 789-0123',
            'delivery_status': 'In Transit',
            'notes': 'Urgent inspection tools shipment'
        }, follow_redirects=True)
        self.assertEqual(order_res.status_code, 200)

        db.session.refresh(valid_product)
        self.assertEqual(valid_product.available_quantity, stock_before - dispatch_qty)
        print(f"  [PASS] Valid dispatch processed. Stock reduced from {stock_before} to {valid_product.available_quantity}")

        # Retrieve order
        order = DispatchOrder.query.filter_by(receiver_name='Dr. Alan Grant').first()
        self.assertIsNotNone(order)

        # 4. Cancel the Dispatch Order -> Stock MUST be RESTORED!
        cancel_res = self.client.post(f'/dispatch/{order.id}/update-status', data={
            'delivery_status': 'Cancelled',
            'notes': 'Customer requested cancellation before transit completion'
        }, follow_redirects=True)
        self.assertEqual(cancel_res.status_code, 200)

        db.session.refresh(valid_product)
        self.assertEqual(valid_product.available_quantity, stock_before)
        self.assertIn(b'have been restored back to available stock', cancel_res.data)
        print(f"  [PASS] Order cancelled. Stock automatically restored back to {valid_product.available_quantity}!")

    def test_06_reports_and_csv(self):
        print("\n--- Testing Reports & CSV Downloads ---")
        self.login_admin()
        reports = ['stock', 'incoming', 'outgoing', 'low_stock', 'expired', 'suppliers', 'transporters']
        for r in reports:
            res = self.client.get(f'/reports/?type={r}')
            self.assertEqual(res.status_code, 200)

        # Test CSV generation
        csv_res = self.client.get('/reports/export?type=stock')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, 'text/csv')
        self.assertIn(b'Product Code,Product Name', csv_res.data)
        print("  [PASS] All 7 report categories and CSV export streamed successfully")

    def test_07_storage_locations_and_relocation(self):
        print("\n--- Testing Storage Location Tracking ---")
        self.login_admin()
        res = self.client.get('/locations/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Storage Locations', res.data)
        print("  [PASS] Storage location visual grid loaded successfully")

if __name__ == '__main__':
    unittest.main()
