# Smart Inventory, Goods Tracking & Transportation Management System

> **SmartLogix** — A modern, full-stack, enterprise-grade web application built for shopkeepers, warehouse supervisors, and logistics administrators to manage incoming goods, multi-warehouse storage racks, expiration dates, suppliers, transporters, and dispatched freight.

---

## 🌟 Key Highlights & Architecture

- **Clean Commercial UI**: Professional blue, slate, and light-grey theme built with **Bootstrap 5.3**, custom CSS variables, and **Font Awesome 6**.
- **Interactive Visualizations**: 4 dynamic **Chart.js** visualizers (Monthly Inflow vs Outflow, Category Stock Distribution, and Expiry Lifecycle Breakdown) connected to live database queries.
- **Strict Stock Integrity**:
  - Stock auto-increments upon incoming shipment arrival.
  - Stock auto-decrements upon goods dispatch.
  - **Strict Expiry Guard**: Expired goods are strictly prohibited from outbound dispatch.
  - **Automated Stock Restoration**: If an in-transit or pending dispatch is cancelled, stock is automatically credited back to available inventory with an audit trail entry.
- **Warehouse Storage Slot Locator**: 4-tier visual storage architecture (`Warehouse` &rarr; `Section` &rarr; `Rack` &rarr; `Shelf`) with 1-click slot relocation.
- **Reporting & Business Intelligence**: Filterable tables, printable audit reports, and 1-click CSV streaming downloads for all 7 major operational modules.
- **Role-Based Authentication**: Secure password hashing via `werkzeug.security` with session guards and pre-configured demo administrator profiles.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Backend Framework** | Python 3 &bull; Flask 3.x | Lightweight, modular WSGI application with Blueprints |
| **Database ORM** | Flask-SQLAlchemy 3.x &bull; SQLite | Relational database with cascade rules and audit ledgers |
| **Frontend Framework** | Bootstrap 5.3 &bull; HTML5 &bull; CSS3 | Fully responsive dashboard layout with mobile offcanvas navigation |
| **Charts & Graphs** | Chart.js 4.4 | Real-time interactive bar and doughnut visualizers |
| **Icons & Typography** | Font Awesome 6 &bull; Inter Font | High-contrast commercial iconography and typography |

---

## 📁 Project Directory Structure

```text
smart_inventory_system/
├── app.py                      # Flask Application Factory & Server Entrypoint
├── config.py                   # Configuration settings, SQLite URI, pagination
├── models.py                   # SQLAlchemy Database Models (10 tables with relationships)
├── helpers.py                  # Code generators, @login_required, notifications & CSV streamer
├── seed_data.py                # Database population script (18+ products, 5 carriers, 5 suppliers)
├── test_system.py              # Automated test suite verifying all 7 core modules
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation & viva presentation guide
├── instance/
│   └── inventory.db            # SQLite database instance
├── routes/
│   ├── auth.py                 # Login, Registration, Logout
│   ├── dashboard.py            # KPI metrics & dynamic Chart.js JSON API
│   ├── inventory.py            # Product CRUD, filters, sorting, stock ledgers
│   ├── incoming.py             # Monthly goods record management & CSV export
│   ├── locations.py            # Warehouse visual grid & slot relocation
│   ├── expiry.py               # Expiry date management & FIFO protection
│   ├── suppliers.py            # Vendor profiles & goods intake history
│   ├── transporters.py         # Carrier fleet, driver contacts, trip states
│   ├── dispatch.py             # Transportation management & stock restoration
│   ├── reports.py              # Business analytics, date filters, printable reports
│   ├── notifications.py        # System alert center
│   └── settings.py             # System info & 1-click sample data reset
├── static/
│   ├── css/
│   │   └── style.css           # Custom corporate styling, print stylesheet, warehouse map
│   └── js/
│       ├── main.js             # Bootstrap tooltips, modals, delete confirmation handler
│       └── dashboard_charts.js # Chart.js dynamic asynchronous initialization
└── templates/
    ├── base.html               # Main application shell with sidebar & topbar
    ├── auth/                   # Login & registration templates (with 1-click Demo Fill)
    ├── dashboard/              # 9 KPI cards, 4 charts, critical alerts, recent activity
    ├── inventory/              # Product directory, Add, Edit, and Detail ledger views
    ├── incoming/               # Monthly intake logs, date filters, CSV downloads
    ├── locations/              # Visual warehouse sections, rack/shelf maps
    ├── expiry/                 # Color-coded expiry audit (Red/Orange/Green)
    ├── suppliers/              # Supplier directory, profiles, supplied products
    ├── transporters/           # Logistics fleet, vehicle cards, driver contacts
    ├── dispatch/               # Dispatch orders, order tracking timeline, status updates
    ├── reports/                # Unified reports, date-range filters, print & CSV
    ├── notifications/          # Alert management center
    ├── settings/               # System information & demo reset button
    └── errors/                 # Custom 404 & 500 error pages
```

---

## 🚀 Step-by-Step Installation & Local Setup

### Step 1: Open the Project in VS Code
Open VS Code, navigate to `File` &rarr; `Open Folder...`, and select:
```text
C:\Users\user\.gemini\antigravity\scratch\smart_inventory_system
```

### Step 2: Install Python Dependencies
Open the integrated VS Code terminal (`Ctrl + ` `~`) and run:
```bash
pip install -r requirements.txt
```

### Step 3: Initialize Database & Sample Data
Run the sample data seeder to create `instance/inventory.db` with 18+ products, categories, locations, suppliers, transporters, incoming shipments, and dispatches:
```bash
python seed_data.py
```

### Step 4: Run the Application
Start the Flask web development server:
```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🔑 Demo Login Credentials

The system includes pre-configured administrative accounts. A 1-click **"Fill Demo"** button is also available on the login page:

| Role | Username | Email | Password | Access Privileges |
|---|---|---|---|---|
| **Lead Administrator** | `admin` | `admin@smartinventory.com` | `admin123` | Full system access, data reset, CRUD |
| **Warehouse Manager** | `manager_sara` | `sara.vance@smartinventory.com` | `manager123` | Operational access to stock & dispatch |

---

## 📦 Functional Modules Detailed Breakdown

### 1. Operations Command Center (Dashboard)
- **9 Real-time Metric Cards**: Total Products, Total Stock Quantity, Total Incoming Goods, Total Dispatched Goods, Low Stock Products, Expiring Soon Products (<30d), Expired Products, Total Transporters, and Active Deliveries.
- **Interactive Charts**:
  - *Monthly Inflow vs Outflow*: Comparative grouped bar chart of the last 6 months.
  - *Stock Distribution by Category*: Doughnut chart mapping categories to inventory.
  - *Expiry Breakdown*: Color-coded segment chart (Expired, <7 Days, <30 Days, Safe).

### 2. Goods & Inventory Management
- Automated sequential code generation: `PRD-2026-0001`.
- Live stock gauge with warning indicators when available quantity falls below `low_stock_threshold`.
- Multi-dimensional filters: Search by keyword/code, filter by category, filter by stock state (Low Stock, Out of Stock, Adequate), and sort by name, quantity, or arrival date.
- Complete transaction ledger tracking every historical adjustment on the product detail page.

### 3. Monthly Goods Record Management
- Records: Product, Supplier, Quantity Received, Arrival Date, Invoice Number, Month, and Year.
- Automated monthly organization with month/year/supplier dropdown filters.
- Immediate CSV report downloads and automatic stock replenishment upon recording new shipments.

### 4. Storage Location Tracking
- Visual warehouse representation (`Warehouse A`, `Warehouse B`, `Cold Storage`, `Chemical Vault`, `Electronics Bin`, `Heavy Hardware`).
- Identifies exact Rack (`Rack A1`, `Rack B2`) and Shelf levels (`Shelf 01`, `Shelf 02`).
- 1-Click **Relocate Slot** modal allowing instant reassignment of any product's storage position.

### 5. Expiry Date Tracking & Spoilage Prevention
- **Safety Indicators**:
  - 🔴 **Red**: Expired (past expiry date) &bull; **Outbound dispatch strictly disabled**.
  - 🟠 **Orange**: Critical (<7 days remaining) &bull; Urgent priority clearance.
  - 🟡 **Yellow**: Warning (<30 days remaining) &bull; FIFO scheduled dispatch.
  - 🟢 **Green**: Safe (>30 days) or Non-Perishable.

### 6. Transporter & Carrier Management
- Tracks logistics carriers, vehicle numbers (`US-TRK-9021`), vehicle types (Heavy 18-Wheeler, Refrigerated Van, Sprinter Van), driver names, mobile numbers, and live availability (`Available` vs `On Trip`).

### 7. Goods Dispatch & Stock Restoration
- Automated validation:
  1. Blocks dispatching if product has expired.
  2. Blocks dispatching if requested quantity exceeds available stock.
- Auto-populates vehicle and driver info when selecting a registered carrier.
- **Stock Restoration on Cancellation**:
  Cancelling a dispatch order automatically replenishes the product's available inventory and records an audit transaction of type `Restored (Cancelled Dispatch)`.

### 8. Reports, Analytics & Print-Friendly Views
- Unified reporting hub for Current Stock, Incoming Goods, Outgoing Dispatches, Low Stock, Expired Goods, Supplier Performance, and Transporter Deliveries.
- Custom `@media print` stylesheet for clean paper / PDF export without sidebar clutter.
- Instant streaming CSV downloads for all reports.

---

## 🧪 Automated Testing

A test suite verifying all 7 core modules is included in `test_system.py`:
```bash
python test_system.py
```
**Tests Verified:**
1. Authentication & password hashing rejection
2. Dashboard metrics and Chart.js JSON API feeds
3. Product inventory CRUD & sequential ID generation
4. Incoming goods intake & real-time stock increments
5. Goods dispatch validation, expired product blocking, and cancellation restoration
6. Reports filtering & CSV streaming responses
7. Storage location visual grid & slot relocation

---

## 🎓 College Viva / Project Demonstration Key Points

When demonstrating this project for academic or commercial review, highlight the following:

1. **Transactional Integrity**: Demonstrate that stock is never a static number. Creating a dispatch order (`/dispatch/create`) decreases inventory immediately, and changing its status to `Cancelled` (`/dispatch/<id>`) restores that stock with an audit record in `StockTransaction`.
2. **Business Rule Enforcement**: Try dispatching an expired product (e.g. `Organic Full Cream Whole Milk`). Show that the frontend displays a warning and disables the button, while the backend API also rejects any manual post.
3. **Dynamic Asynchronous Charts**: Open browser DevTools Network tab while visiting the dashboard to show `/api/dashboard-charts` fetching live SQLite aggregated data via SQLAlchemy functions (`func.coalesce`, `func.sum`).
4. **Relational Schema**: 10 interconnected tables with foreign keys and cascade rules preventing orphan records.
