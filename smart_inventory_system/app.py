import os
from datetime import datetime, date
from flask import Flask, render_template, session
from config import Config
from models import db, User, Notification

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance directory exists
    instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.inventory import inventory_bp
    from routes.incoming import incoming_bp
    from routes.locations import locations_bp
    from routes.expiry import expiry_bp
    from routes.suppliers import suppliers_bp
    from routes.transporters import transporters_bp
    from routes.dispatch import dispatch_bp
    from routes.reports import reports_bp
    from routes.notifications import notifications_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(incoming_bp, url_prefix='/incoming')
    app.register_blueprint(locations_bp, url_prefix='/locations')
    app.register_blueprint(expiry_bp, url_prefix='/expiry')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(transporters_bp, url_prefix='/transporters')
    app.register_blueprint(dispatch_bp, url_prefix='/dispatch')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    # Global Template Context
    @app.context_processor
    def inject_globals():
        unread_notifications = 0
        current_user = None
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
            unread_notifications = Notification.query.filter_by(is_read=False).count()

        return {
            'now': datetime.now(),
            'today': date.today(),
            'current_user': current_user,
            'unread_notifications_count': unread_notifications,
            'app_name': 'SmartLogix'
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Auto-initialize and seed DB if first run
    with app.app_context():
        db_path = os.path.join(instance_dir, 'inventory.db')
        if not os.path.exists(db_path):
            import seed_data
            print("[INFO] First run detected. Creating database and inserting sample data...")
            seed_data.seed_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
