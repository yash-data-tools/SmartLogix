from flask import Blueprint, render_template, redirect, url_for, flash, session
from models import db
from helpers import login_required
import seed_data

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    return render_template('settings/index.html')


@settings_bp.route('/reset-sample-data', methods=['POST'])
@login_required
def reset_sample_data():
    try:
        seed_data.seed_all()
        flash('Sample database has been completely re-initialized with fresh demo data!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting sample data: {str(e)}', 'danger')

    return redirect(url_for('dashboard.index'))
