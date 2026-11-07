import os
from datetime import datetime, date, timedelta
from config import Config
from models import (
    db, User, Category, Supplier, StorageLocation,
    Product, IncomingGood, Transporter, DispatchOrder,
    StockTransaction, Notification
)

def seed_all():
    """Drops all tables, recreates them, and inserts rich realistic demo data."""
    db.drop_all()
    db.create_all()

    today = date.today()

    # 1. Admin & Demo Users
    admin = User(
        username='admin',
        email='admin@smartinventory.com',
        full_name='Arthur Pendelton (Lead Administrator)',
        role='Admin'
    )
    admin.set_password('admin123')

    manager = User(
        username='manager_sara',
        email='sara.vance@smartinventory.com',
        full_name='Sara Vance (Warehouse Manager)',
        role='Manager'
    )
    manager.set_password('manager123')

    db.session.add_all([admin, manager])
    db.session.commit()

    # 2. Categories
    categories = [
        Category(name='Electronics & Components', description='Circuits, sensors, controllers, and wiring', icon='fa-microchip'),
        Category(name='Pharmaceuticals & Health', description='Essential drugs, medical consumables, and antiseptics', icon='fa-pills'),
        Category(name='Food & Beverages', description='Packaged groceries, beverages, and dairy products', icon='fa-utensils'),
        Category(name='Industrial Chemicals', description='Cleaning agents, industrial lubricants, and solvents', icon='fa-flask'),
        Category(name='Hardware & Tools', description='Fasteners, mechanical tools, power equipment', icon='fa-wrench'),
        Category(name='Apparel & Safety Gear', description='Safety boots, high-vis vests, protective helmets', icon='fa-vest')
    ]
    db.session.add_all(categories)
    db.session.commit()

    # 3. Suppliers
    suppliers = [
        Supplier(
            supplier_code='SUP-2026-0001',
            name='Apex Global Electronics',
            company_name='Apex Semiconductor & Tech Corp',
            phone='+1 (555) 234-5678',
            email='orders@apextech.com',
            address='88 Innovation Parkway, Silicon District, CA 94016'
        ),
        Supplier(
            supplier_code='SUP-2026-0002',
            name='BioHealth Pharma Labs',
            company_name='BioHealth Laboratories International',
            phone='+1 (555) 890-1234',
            email='distribution@biohealthpharma.com',
            address='412 BioSciences Way, Medical Park, NJ 07001'
        ),
        Supplier(
            supplier_code='SUP-2026-0003',
            name='FreshField Foods Co.',
            company_name='FreshField Agro & FMCG Distributors',
            phone='+1 (555) 345-6789',
            email='supply@freshfieldfoods.com',
            address='120 Harvest Valley Road, Chicago, IL 60607'
        ),
        Supplier(
            supplier_code='SUP-2026-0004',
            name='ChemPro Solutions Ltd',
            company_name='ChemPro Specialty Chemicals LLC',
            phone='+1 (555) 901-2345',
            email='sales@chempro-solutions.com',
            address='74 Refinery Blvd, Houston, TX 77002'
        ),
        Supplier(
            supplier_code='SUP-2026-0005',
            name='Titan Industrial Tools',
            company_name='Titan Heavy Hardware Industries',
            phone='+1 (555) 456-7890',
            email='support@titanhardware.com',
            address='550 Ironworks Drive, Cleveland, OH 44101'
        )
    ]
    db.session.add_all(suppliers)
    db.session.commit()

    # 4. Storage Locations (Warehouse A and B, Sections, Racks, Shelves)
    locations = [
        StorageLocation(warehouse='Warehouse A', section='Section 1 - Cold Storage', rack='Rack A1', shelf='Shelf 01', capacity=300, description='Temperature-controlled pharmaceutical rack'),
        StorageLocation(warehouse='Warehouse A', section='Section 1 - Cold Storage', rack='Rack A1', shelf='Shelf 02', capacity=300, description='Perishable foods and dairy shelf'),
        StorageLocation(warehouse='Warehouse A', section='Section 2 - Ambient Goods', rack='Rack A2', shelf='Shelf 01', capacity=500, description='Standard dry grocery rack'),
        StorageLocation(warehouse='Warehouse A', section='Section 2 - Ambient Goods', rack='Rack A2', shelf='Shelf 02', capacity=500, description='Canned and packaged dry foods'),
        StorageLocation(warehouse='Warehouse A', section='Section 3 - Electronics Bin', rack='Rack A3', shelf='Shelf 01', capacity=400, description='Anti-static electronic microchip bins'),
        StorageLocation(warehouse='Warehouse A', section='Section 3 - Electronics Bin', rack='Rack A3', shelf='Shelf 02', capacity=400, description='Microcontrollers and sensor units'),
        StorageLocation(warehouse='Warehouse B', section='Section 1 - Chemical Vault', rack='Rack B1', shelf='Shelf 01', capacity=200, description='Ventilated chemical storage drums'),
        StorageLocation(warehouse='Warehouse B', section='Section 1 - Chemical Vault', rack='Rack B1', shelf='Shelf 02', capacity=250, description='Sealed solvent and sanitizer containers'),
        StorageLocation(warehouse='Warehouse B', section='Section 2 - Heavy Hardware', rack='Rack B2', shelf='Shelf 01', capacity=1000, description='Heavy mechanical bolts and brackets'),
        StorageLocation(warehouse='Warehouse B', section='Section 2 - Heavy Hardware', rack='Rack B2', shelf='Shelf 02', capacity=800, description='Industrial hand tools and drills'),
        StorageLocation(warehouse='Warehouse B', section='Section 3 - PPE & Safety', rack='Rack B3', shelf='Shelf 01', capacity=600, description='Safety apparel, helmets, and boots')
    ]
    db.session.add_all(locations)
    db.session.commit()

    # 5. Transporters (At least 5)
    transporters = [
        Transporter(
            transporter_code='TRP-2026-0001',
            name='FastFreight Logistics Co.',
            contact_number='+1 (555) 771-0021',
            email='dispatch@fastfreight.com',
            vehicle_number='US-TRK-9021',
            vehicle_type='Heavy 18-Wheeler Truck',
            driver_name='Marcus Higgins',
            driver_contact='+1 (555) 771-0022',
            address='12 Port Authority Road, Jersey City, NJ',
            status='Available'
        ),
        Transporter(
            transporter_code='TRP-2026-0002',
            name='ColdChain Express Refrigerated',
            contact_number='+1 (555) 882-1133',
            email='ops@coldchainexpress.com',
            vehicle_number='US-REF-4412',
            vehicle_type='Refrigerated Container Van',
            driver_name='Elena Rostova',
            driver_contact='+1 (555) 882-1134',
            address='74 Interstate Bypass, Columbus, OH',
            status='On Trip'
        ),
        Transporter(
            transporter_code='TRP-2026-0003',
            name='Metro Rapid Cargo Vans',
            contact_number='+1 (555) 993-2244',
            email='metro@rapidcargo.com',
            vehicle_number='US-VAN-7789',
            vehicle_type='High-Roof Sprinter Van',
            driver_name='David Kim',
            driver_contact='+1 (555) 993-2245',
            address='304 Industrial Parkway, Chicago, IL',
            status='Available'
        ),
        Transporter(
            transporter_code='TRP-2026-0004',
            name='SwiftHaul Intermodal',
            contact_number='+1 (555) 440-3355',
            email='hauling@swifthaul.net',
            vehicle_number='US-TRK-3301',
            vehicle_type='Flatbed Heavy Carrier',
            driver_name='Jamal Washington',
            driver_contact='+1 (555) 440-3356',
            address='818 Freight Hub Rd, Dallas, TX',
            status='Available'
        ),
        Transporter(
            transporter_code='TRP-2026-0005',
            name='BlueSky Urban Couriers',
            contact_number='+1 (555) 551-4466',
            email='routes@blueskyurban.com',
            vehicle_number='US-VAN-1120',
            vehicle_type='City Delivery Mini-Truck',
            driver_name='Carlos Mendez',
            driver_contact='+1 (555) 551-4467',
            address='50 Airport Cargo Way, Atlanta, GA',
            status='Available'
        )
    ]
    db.session.add_all(transporters)
    db.session.commit()

    # 6. At least 18 Products with various expiry states
    # Categories:
    # 0: Electronics, 1: Pharma, 2: Food, 3: Chemicals, 4: Hardware, 5: Apparel
    # Locations:
    # 0: A1-Shelf01 (Pharma cold), 1: A1-Shelf02 (Food cold)
    # 2: A2-Shelf01 (Food dry), 3: A2-Shelf02 (Food canned)
    # 4: A3-Shelf01 (Electronics), 5: A3-Shelf02 (Electronics)
    # 6: B1-Shelf01 (Chemicals), 7: B1-Shelf02 (Chemicals)
    # 8: B2-Shelf01 (Hardware), 9: B2-Shelf02 (Hardware)
    # 10: B3-Shelf01 (Apparel)

    sample_products = [
        # --- EXPIRED PRODUCTS (for testing expiry alerts and dispatch prevention) ---
        Product(
            product_code='PRD-2026-0001',
            name='Organic Full Cream Whole Milk (1L)',
            category_id=categories[2].id,
            supplier_id=suppliers[2].id,
            storage_location_id=locations[1].id,
            description='Pasteurized homogenised whole milk in tetra pack bottles.',
            quantity_received=120,
            available_quantity=24,
            dispatched_quantity=96,
            unit='Bottles',
            purchase_price=2.40,
            arrival_date=today - timedelta(days=25),
            expiry_date=today - timedelta(days=4), # EXPIRED 4 days ago
            low_stock_threshold=20
        ),
        Product(
            product_code='PRD-2026-0002',
            name='Amoxicillin Antibiotic Suspension 250mg',
            category_id=categories[1].id,
            supplier_id=suppliers[1].id,
            storage_location_id=locations[0].id,
            description='Pediatric oral antibiotic suspension powder for reconstitution.',
            quantity_received=80,
            available_quantity=15,
            dispatched_quantity=65,
            unit='Bottles',
            purchase_price=8.50,
            arrival_date=today - timedelta(days=60),
            expiry_date=today - timedelta(days=2), # EXPIRED 2 days ago
            low_stock_threshold=20
        ),

        # --- EXPIRING WITHIN 7 DAYS (Critical Warning) ---
        Product(
            product_code='PRD-2026-0003',
            name='Fresh Artisan Sliced Sourdough Bread',
            category_id=categories[2].id,
            supplier_id=suppliers[2].id,
            storage_location_id=locations[2].id,
            description='Naturally fermented sourdough bread loaves, preservative free.',
            quantity_received=60,
            available_quantity=32,
            dispatched_quantity=28,
            unit='Loaves',
            purchase_price=3.20,
            arrival_date=today - timedelta(days=4),
            expiry_date=today + timedelta(days=3), # 3 days remaining!
            low_stock_threshold=15
        ),
        Product(
            product_code='PRD-2026-0004',
            name='Saline Solution 0.9% IV Infusion (500ml)',
            category_id=categories[1].id,
            supplier_id=suppliers[1].id,
            storage_location_id=locations[0].id,
            description='Sterile isotonic sodium chloride intravenous infusion bags.',
            quantity_received=200,
            available_quantity=45,
            dispatched_quantity=155,
            unit='Bags',
            purchase_price=4.10,
            arrival_date=today - timedelta(days=120),
            expiry_date=today + timedelta(days=6), # 6 days remaining!
            low_stock_threshold=50
        ),

        # --- EXPIRING WITHIN 30 DAYS (Warning Soon) ---
        Product(
            product_code='PRD-2026-0005',
            name='Greek Style Strained Yogurt 500g',
            category_id=categories[2].id,
            supplier_id=suppliers[2].id,
            storage_location_id=locations[1].id,
            description='High-protein probiotic plain greek yogurt tubs.',
            quantity_received=150,
            available_quantity=40,
            dispatched_quantity=110,
            unit='Tubs',
            purchase_price=1.85,
            arrival_date=today - timedelta(days=15),
            expiry_date=today + timedelta(days=16), # 16 days left
            low_stock_threshold=30
        ),
        Product(
            product_code='PRD-2026-0006',
            name='Surgical Hand Antiseptic Scrub 1L',
            category_id=categories[1].id,
            supplier_id=suppliers[1].id,
            storage_location_id=locations[7].id,
            description='Chlorhexidine gluconate 4% medical preoperative scrub.',
            quantity_received=90,
            available_quantity=18,
            dispatched_quantity=72,
            unit='Bottles',
            purchase_price=11.50,
            arrival_date=today - timedelta(days=180),
            expiry_date=today + timedelta(days=22), # 22 days left
            low_stock_threshold=25 # Low stock! (18 <= 25)
        ),

        # --- SAFE / LONG EXPIRY PRODUCTS ---
        Product(
            product_code='PRD-2026-0007',
            name='Paracetamol Tablets 500mg (100 Tabs)',
            category_id=categories[1].id,
            supplier_id=suppliers[1].id,
            storage_location_id=locations[0].id,
            description='Antipyretic and pain reliever blister strips in boxed packs.',
            quantity_received=500,
            available_quantity=340,
            dispatched_quantity=160,
            unit='Boxes',
            purchase_price=3.75,
            arrival_date=today - timedelta(days=30),
            expiry_date=today + timedelta(days=365), # 1 year safe
            low_stock_threshold=50
        ),
        Product(
            product_code='PRD-2026-0008',
            name='Canned Premium Sweet Corn (400g)',
            category_id=categories[2].id,
            supplier_id=suppliers[2].id,
            storage_location_id=locations[3].id,
            description='Vacuum-sealed whole kernel sweet corn in brine.',
            quantity_received=400,
            available_quantity=280,
            dispatched_quantity=120,
            unit='Cans',
            purchase_price=1.10,
            arrival_date=today - timedelta(days=45),
            expiry_date=today + timedelta(days=500),
            low_stock_threshold=40
        ),
        Product(
            product_code='PRD-2026-0009',
            name='Industrial Floor Degreaser Concentrate (20L)',
            category_id=categories[3].id,
            supplier_id=suppliers[3].id,
            storage_location_id=locations[6].id,
            description='Heavy-duty alkaline workshop and warehouse floor cleaner drum.',
            quantity_received=50,
            available_quantity=8, # LOW STOCK (8 <= 12)
            dispatched_quantity=42,
            unit='Drums',
            purchase_price=45.00,
            arrival_date=today - timedelta(days=60),
            expiry_date=today + timedelta(days=280),
            low_stock_threshold=12
        ),

        # --- NON-PERISHABLE GOODS (No Expiry Date) ---
        Product(
            product_code='PRD-2026-0010',
            name='STM32 ARM Cortex-M4 Microcontroller IC',
            category_id=categories[0].id,
            supplier_id=suppliers[0].id,
            storage_location_id=locations[4].id,
            description='High-performance 32-bit MCU chips for embedded industrial automation.',
            quantity_received=1000,
            available_quantity=680,
            dispatched_quantity=320,
            unit='Pieces',
            purchase_price=6.20,
            arrival_date=today - timedelta(days=20),
            expiry_date=None, # Non-perishable
            low_stock_threshold=100
        ),
        Product(
            product_code='PRD-2026-0011',
            name='Digital Temperature & Humidity Sensor (DHT22)',
            category_id=categories[0].id,
            supplier_id=suppliers[0].id,
            storage_location_id=locations[5].id,
            description='Calibrated digital signal output multi-sensor modules.',
            quantity_received=450,
            available_quantity=310,
            dispatched_quantity=140,
            unit='Pieces',
            purchase_price=3.40,
            arrival_date=today - timedelta(days=15),
            expiry_date=None,
            low_stock_threshold=50
        ),
        Product(
            product_code='PRD-2026-0012',
            name='Arduino Uno R3 Development Boards',
            category_id=categories[0].id,
            supplier_id=suppliers[0].id,
            storage_location_id=locations[4].id,
            description='ATmega328P microcontroller prototyping development board.',
            quantity_received=250,
            available_quantity=12, # LOW STOCK (12 <= 25)
            dispatched_quantity=238,
            unit='Pieces',
            purchase_price=12.50,
            arrival_date=today - timedelta(days=40),
            expiry_date=None,
            low_stock_threshold=25
        ),
        Product(
            product_code='PRD-2026-0013',
            name='Stainless Steel Hex Bolts M8 x 40mm (Pack 50)',
            category_id=categories[4].id,
            supplier_id=suppliers[4].id,
            storage_location_id=locations[8].id,
            description='Marine grade 316 stainless high-tensile structural bolts.',
            quantity_received=300,
            available_quantity=195,
            dispatched_quantity=105,
            unit='Packs',
            purchase_price=9.80,
            arrival_date=today - timedelta(days=50),
            expiry_date=None,
            low_stock_threshold=30
        ),
        Product(
            product_code='PRD-2026-0014',
            name='Cordless Impact Drill 18V Brushless Kit',
            category_id=categories[4].id,
            supplier_id=suppliers[4].id,
            storage_location_id=locations[9].id,
            description='Heavy industrial cordless hammer drill kit with 2x 4.0Ah batteries.',
            quantity_received=40,
            available_quantity=5, # CRITICAL LOW STOCK (5 <= 10)
            dispatched_quantity=35,
            unit='Kits',
            purchase_price=110.00,
            arrival_date=today - timedelta(days=70),
            expiry_date=None,
            low_stock_threshold=10
        ),
        Product(
            product_code='PRD-2026-0015',
            name='Class 2 High-Visibility Reflective Safety Vests',
            category_id=categories[5].id,
            supplier_id=suppliers[4].id,
            storage_location_id=locations[10].id,
            description='Fluorescent yellow breathable polyester vest with zipper front.',
            quantity_received=200,
            available_quantity=140,
            dispatched_quantity=60,
            unit='Pieces',
            purchase_price=4.50,
            arrival_date=today - timedelta(days=35),
            expiry_date=None,
            low_stock_threshold=30
        ),
        Product(
            product_code='PRD-2026-0016',
            name='Steel-Toe Waterproof Industrial Safety Boots',
            category_id=categories[5].id,
            supplier_id=suppliers[4].id,
            storage_location_id=locations[10].id,
            description='ANSI Z41 certified slip-resistant warehouse protective footwear.',
            quantity_received=85,
            available_quantity=52,
            dispatched_quantity=33,
            unit='Pairs',
            purchase_price=42.00,
            arrival_date=today - timedelta(days=25),
            expiry_date=None,
            low_stock_threshold=15
        ),
        Product(
            product_code='PRD-2026-0017',
            name='Pure Acetone Chemical Solvent (5L)',
            category_id=categories[3].id,
            supplier_id=suppliers[3].id,
            storage_location_id=locations[7].id,
            description='High-purity laboratory and workshop degreasing solvent.',
            quantity_received=60,
            available_quantity=22,
            dispatched_quantity=38,
            unit='Bottles',
            purchase_price=18.00,
            arrival_date=today - timedelta(days=90),
            expiry_date=today + timedelta(days=700),
            low_stock_threshold=15
        ),
        Product(
            product_code='PRD-2026-0018',
            name='Medical Grade Nitrile Gloves (Box of 100)',
            category_id=categories[1].id,
            supplier_id=suppliers[1].id,
            storage_location_id=locations[0].id,
            description='Powder-free textured fingertip disposable exam gloves.',
            quantity_received=350,
            available_quantity=210,
            dispatched_quantity=140,
            unit='Boxes',
            purchase_price=7.20,
            arrival_date=today - timedelta(days=15),
            expiry_date=today + timedelta(days=600),
            low_stock_threshold=40
        )
    ]
    db.session.add_all(sample_products)
    db.session.commit()

    # 7. Incoming Goods Records (Multiple months historical data)
    incoming_data = [
        # Past 4 months data to power dynamic charts
        # Month -3
        IncomingGood(
            incoming_code='INC-2026-0001',
            product_id=sample_products[9].id, # Microcontrollers
            supplier_id=suppliers[0].id,
            quantity_received=500,
            date_of_arrival=today - timedelta(days=100),
            invoice_number='INV-APX-8801',
            purchase_price=6.20,
            month=(today - timedelta(days=100)).month,
            year=(today - timedelta(days=100)).year,
            notes='Quarterly bulk silicon delivery'
        ),
        IncomingGood(
            incoming_code='INC-2026-0002',
            product_id=sample_products[6].id, # Paracetamol
            supplier_id=suppliers[1].id,
            quantity_received=300,
            date_of_arrival=today - timedelta(days=95),
            invoice_number='INV-BIO-4402',
            purchase_price=3.75,
            month=(today - timedelta(days=95)).month,
            year=(today - timedelta(days=95)).year,
            notes='Hospital supply intake'
        ),
        # Month -2
        IncomingGood(
            incoming_code='INC-2026-0003',
            product_id=sample_products[13].id, # Impact drills
            supplier_id=suppliers[4].id,
            quantity_received=40,
            date_of_arrival=today - timedelta(days=70),
            invoice_number='INV-TTN-3101',
            purchase_price=110.00,
            month=(today - timedelta(days=70)).month,
            year=(today - timedelta(days=70)).year,
            notes='Titan hardware shipment'
        ),
        IncomingGood(
            incoming_code='INC-2026-0004',
            product_id=sample_products[7].id, # Sweet Corn
            supplier_id=suppliers[2].id,
            quantity_received=400,
            date_of_arrival=today - timedelta(days=65),
            invoice_number='INV-FF-9912',
            purchase_price=1.10,
            month=(today - timedelta(days=65)).month,
            year=(today - timedelta(days=65)).year,
            notes='Canned pantry batch'
        ),
        IncomingGood(
            incoming_code='INC-2026-0005',
            product_id=sample_products[8].id, # Degreaser
            supplier_id=suppliers[3].id,
            quantity_received=50,
            date_of_arrival=today - timedelta(days=60),
            invoice_number='INV-CHM-1205',
            purchase_price=45.00,
            month=(today - timedelta(days=60)).month,
            year=(today - timedelta(days=60)).year,
            notes='Hazardous chemical certified shipment'
        ),
        # Month -1
        IncomingGood(
            incoming_code='INC-2026-0006',
            product_id=sample_products[11].id, # Arduino Uno
            supplier_id=suppliers[0].id,
            quantity_received=250,
            date_of_arrival=today - timedelta(days=40),
            invoice_number='INV-APX-9120',
            purchase_price=12.50,
            month=(today - timedelta(days=40)).month,
            year=(today - timedelta(days=40)).year,
            notes='Educational robotics stock'
        ),
        IncomingGood(
            incoming_code='INC-2026-0007',
            product_id=sample_products[14].id, # Safety Vests
            supplier_id=suppliers[4].id,
            quantity_received=200,
            date_of_arrival=today - timedelta(days=35),
            invoice_number='INV-TTN-3509',
            purchase_price=4.50,
            month=(today - timedelta(days=35)).month,
            year=(today - timedelta(days=35)).year,
            notes='Annual PPE stock replenishment'
        ),
        # Current Month
        IncomingGood(
            incoming_code='INC-2026-0008',
            product_id=sample_products[9].id, # Microcontrollers
            supplier_id=suppliers[0].id,
            quantity_received=500,
            date_of_arrival=today - timedelta(days=20),
            invoice_number='INV-APX-9550',
            purchase_price=6.20,
            month=today.month,
            year=today.year,
            notes='Additional MCU batch'
        ),
        IncomingGood(
            incoming_code='INC-2026-0009',
            product_id=sample_products[17].id, # Nitrile gloves
            supplier_id=suppliers[1].id,
            quantity_received=350,
            date_of_arrival=today - timedelta(days=15),
            invoice_number='INV-BIO-5120',
            purchase_price=7.20,
            month=today.month,
            year=today.year,
            notes='Standard hospital gloves order'
        ),
        IncomingGood(
            incoming_code='INC-2026-0010',
            product_id=sample_products[4].id, # Greek yogurt
            supplier_id=suppliers[2].id,
            quantity_received=150,
            date_of_arrival=today - timedelta(days=10),
            invoice_number='INV-FF-0182',
            purchase_price=1.85,
            month=today.month,
            year=today.year,
            notes='Fresh chilled dairy transport'
        ),
        IncomingGood(
            incoming_code='INC-2026-0011',
            product_id=sample_products[2].id, # Sourdough bread
            supplier_id=suppliers[2].id,
            quantity_received=60,
            date_of_arrival=today - timedelta(days=4),
            invoice_number='INV-FF-0205',
            purchase_price=3.20,
            month=today.month,
            year=today.year,
            notes='Bakery daily fresh delivery'
        )
    ]
    db.session.add_all(incoming_data)
    db.session.commit()

    # 8. Dispatch Orders across multiple statuses
    # Statuses: Pending, Ready for Dispatch, In Transit, Delivered, Cancelled
    dispatch_orders = [
        # Delivered Orders
        DispatchOrder(
            dispatch_code='DSP-2026-0001',
            product_id=sample_products[9].id, # Microcontroller
            transporter_id=transporters[0].id,
            quantity_dispatched=200,
            dispatch_date=datetime.now() - timedelta(days=18),
            expected_delivery_date=today - timedelta(days=15),
            actual_delivery_date=today - timedelta(days=15),
            destination_address='450 Automation Blvd, Robotics Facility, Chicago, IL',
            receiver_name='Dr. Ronald Sterling',
            receiver_phone='+1 (555) 301-4490',
            vehicle_number=transporters[0].vehicle_number,
            driver_contact=f"{transporters[0].driver_name} ({transporters[0].driver_contact})",
            delivery_status='Delivered',
            notes='Delivered in full on schedule. Signed by gate security.'
        ),
        DispatchOrder(
            dispatch_code='DSP-2026-0002',
            product_id=sample_products[6].id, # Paracetamol
            transporter_id=transporters[2].id,
            quantity_dispatched=160,
            dispatch_date=datetime.now() - timedelta(days=12),
            expected_delivery_date=today - timedelta(days=10),
            actual_delivery_date=today - timedelta(days=10),
            destination_address='St. Jude Central Clinic, Pharmacy Dept, Columbus, OH',
            receiver_name='Nurse Clara Oswald',
            receiver_phone='+1 (555) 412-9900',
            vehicle_number=transporters[2].vehicle_number,
            driver_contact=f"{transporters[2].driver_name} ({transporters[2].driver_contact})",
            delivery_status='Delivered',
            notes='Received by Chief Pharmacist.'
        ),
        DispatchOrder(
            dispatch_code='DSP-2026-0003',
            product_id=sample_products[17].id, # Nitrile gloves
            transporter_id=transporters[4].id,
            quantity_dispatched=140,
            dispatch_date=datetime.now() - timedelta(days=8),
            expected_delivery_date=today - timedelta(days=6),
            actual_delivery_date=today - timedelta(days=6),
            destination_address='City Health Diagnostic Center, Suite 102, Atlanta, GA',
            receiver_name='Brian Patel',
            receiver_phone='+1 (555) 602-1188',
            vehicle_number=transporters[4].vehicle_number,
            driver_contact=f"{transporters[4].driver_name} ({transporters[4].driver_contact})",
            delivery_status='Delivered',
            notes='Direct door-to-door delivery confirmed.'
        ),

        # In Transit Orders
        DispatchOrder(
            dispatch_code='DSP-2026-0004',
            product_id=sample_products[4].id, # Greek yogurt
            transporter_id=transporters[1].id, # Cold chain
            quantity_dispatched=110,
            dispatch_date=datetime.now() - timedelta(days=1),
            expected_delivery_date=today + timedelta(days=1),
            actual_delivery_date=None,
            destination_address='Metro Hypermarket, Central Distribution Dock, Cincinnati, OH',
            receiver_name='Frank Morales',
            receiver_phone='+1 (555) 723-5511',
            vehicle_number=transporters[1].vehicle_number,
            driver_contact=f"{transporters[1].driver_name} ({transporters[1].driver_contact})",
            delivery_status='In Transit',
            notes='Temperature sensor logs verified at 3.5 deg C.'
        ),
        DispatchOrder(
            dispatch_code='DSP-2026-0005',
            product_id=sample_products[9].id, # Microcontroller
            transporter_id=transporters[3].id,
            quantity_dispatched=120,
            dispatch_date=datetime.now() - timedelta(hours=14),
            expected_delivery_date=today + timedelta(days=2),
            actual_delivery_date=None,
            destination_address='Tesla Giga-Suppliers Hub, Building 4, Austin, TX',
            receiver_name='Anita Sharma',
            receiver_phone='+1 (555) 834-6622',
            vehicle_number=transporters[3].vehicle_number,
            driver_contact=f"{transporters[3].driver_name} ({transporters[3].driver_contact})",
            delivery_status='In Transit',
            notes='En route on I-35 corridor.'
        ),

        # Ready for Dispatch
        DispatchOrder(
            dispatch_code='DSP-2026-0006',
            product_id=sample_products[14].id, # Safety Vests
            transporter_id=transporters[4].id,
            quantity_dispatched=60,
            dispatch_date=datetime.now() - timedelta(hours=4),
            expected_delivery_date=today + timedelta(days=1),
            actual_delivery_date=None,
            destination_address='Harbor Port Authority Infrastructure Site, Savannah, GA',
            receiver_name='Captain Douglas Ross',
            receiver_phone='+1 (555) 945-7733',
            vehicle_number=transporters[4].vehicle_number,
            driver_contact=f"{transporters[4].driver_name} ({transporters[4].driver_contact})",
            delivery_status='Ready for Dispatch',
            notes='Pallets packaged and staged on Loading Dock 3.'
        ),

        # Pending Order
        DispatchOrder(
            dispatch_code='DSP-2026-0007',
            product_id=sample_products[10].id, # Sensors
            transporter_id=transporters[2].id,
            quantity_dispatched=140,
            dispatch_date=datetime.now() - timedelta(hours=2),
            expected_delivery_date=today + timedelta(days=3),
            actual_delivery_date=None,
            destination_address='Midwest IoT Innovation Hub, Ann Arbor, MI',
            receiver_name='Kevin Zhou',
            receiver_phone='+1 (555) 234-8844',
            vehicle_number=transporters[2].vehicle_number,
            driver_contact=f"{transporters[2].driver_name} ({transporters[2].driver_contact})",
            delivery_status='Pending',
            notes='Order awaiting warehouse loading supervisor verification.'
        ),

        # Cancelled Order (Shows stock restoration handling)
        DispatchOrder(
            dispatch_code='DSP-2026-0008',
            product_id=sample_products[12].id, # Hex Bolts
            transporter_id=transporters[0].id,
            quantity_dispatched=50,
            dispatch_date=datetime.now() - timedelta(days=5),
            expected_delivery_date=today - timedelta(days=3),
            actual_delivery_date=None,
            destination_address='Cancelled Construction Site, Detroit, MI',
            receiver_name='George Vance',
            receiver_phone='+1 (555) 998-1122',
            vehicle_number=transporters[0].vehicle_number,
            driver_contact=f"{transporters[0].driver_name} ({transporters[0].driver_contact})",
            delivery_status='Cancelled',
            notes='Client halted project. Stock successfully restored to inventory.'
        )
    ]
    db.session.add_all(dispatch_orders)
    db.session.commit()

    # 9. Stock Transactions History
    transactions = [
        # Microcontrollers transactions
        StockTransaction(
            product_id=sample_products[9].id,
            transaction_type='Incoming (Restock)',
            quantity=500,
            balance_after=500,
            reference_id='INV-APX-8801',
            notes='Initial shipment'
        ),
        StockTransaction(
            product_id=sample_products[9].id,
            transaction_type='Incoming (Restock)',
            quantity=500,
            balance_after=1000,
            reference_id='INV-APX-9550',
            notes='Second shipment'
        ),
        StockTransaction(
            product_id=sample_products[9].id,
            transaction_type='Dispatched',
            quantity=-200,
            balance_after=800,
            reference_id='DSP-2026-0001',
            notes='Shipped to Chicago Robotics'
        ),
        StockTransaction(
            product_id=sample_products[9].id,
            transaction_type='Dispatched',
            quantity=-120,
            balance_after=680,
            reference_id='DSP-2026-0005',
            notes='Shipped to Tesla Giga Hub'
        ),

        # Paracetamol transactions
        StockTransaction(
            product_id=sample_products[6].id,
            transaction_type='Incoming (Restock)',
            quantity=500,
            balance_after=500,
            reference_id='INV-BIO-4402',
            notes='Batch arrival'
        ),
        StockTransaction(
            product_id=sample_products[6].id,
            transaction_type='Dispatched',
            quantity=-160,
            balance_after=340,
            reference_id='DSP-2026-0002',
            notes='Shipped to St. Jude Central Clinic'
        ),

        # Cancelled Order Restoration demonstration transaction
        StockTransaction(
            product_id=sample_products[12].id,
            transaction_type='Dispatched',
            quantity=-50,
            balance_after=145,
            reference_id='DSP-2026-0008',
            notes='Initial dispatch attempt'
        ),
        StockTransaction(
            product_id=sample_products[12].id,
            transaction_type='Restored (Cancelled Dispatch)',
            quantity=50,
            balance_after=195,
            reference_id='DSP-2026-0008',
            notes='Restored due to cancellation of dispatch #DSP-2026-0008'
        )
    ]
    db.session.add_all(transactions)
    db.session.commit()

    # 10. Initial Notifications
    notifications = [
        Notification(
            title='Expired Product Alert: Whole Milk',
            message='Organic Whole Milk (PRD-2026-0001) expired 4 days ago. 24 bottles remaining in Warehouse A Rack A1.',
            type='danger',
            link='/expiry?status=expired'
        ),
        Notification(
            title='Critical Expiry (3 Days): Sourdough Bread',
            message='Fresh Artisan Bread (PRD-2026-0003) expires in 3 days. Priority clearance recommended.',
            type='warning',
            link='/expiry?status=expiring_7d'
        ),
        Notification(
            title='Low Stock Warning: Cordless Impact Drill',
            message='Available quantity (5 Kits) is below the threshold of 10 Kits.',
            type='warning',
            link='/inventory?stock=low'
        ),
        Notification(
            title='Active Delivery: In Transit to Tesla Hub',
            message='Order DSP-2026-0005 (120 MCUs) is on route with transporter SwiftHaul Intermodal.',
            type='info',
            link='/dispatch/5'
        ),
        Notification(
            title='Delivery Completed: St. Jude Hospital',
            message='Order DSP-2026-0002 was marked Delivered on schedule.',
            type='success',
            link='/dispatch/2'
        )
    ]
    db.session.add_all(notifications)
    db.session.commit()

    print("[SUCCESS] Database successfully seeded with rich sample data!")

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        seed_all()
