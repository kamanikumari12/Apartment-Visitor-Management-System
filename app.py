from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import pytz  # Import pytz for timezone handling

# Set IST Timezone
IST = pytz.timezone('Asia/Kolkata')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visitors.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    apartment = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    entry_time = db.Column(db.DateTime, default=lambda: datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(IST))
    exit_time = db.Column(db.DateTime, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Initialize tables manually
def create_tables():
    db.create_all()
    if Admin.query.filter_by(username='admin').first() is None:
        admin = Admin(username='admin', password=generate_password_hash('kamani'))  # Updated Password
        db.session.add(admin)
        db.session.commit()

# Root route – redirect based on login status
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Admin Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Admin.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# Dashboard – shows visitor summary and quick actions
@app.route('/dashboard')
@login_required
def dashboard():
    total_visitors = Visitor.query.count()
    today_count = Visitor.query.filter(db.func.date(Visitor.entry_time) == date.today()).count()
    
    # Fetch the 5 latest visitors to display in the dashboard table
    visitors = Visitor.query.order_by(Visitor.entry_time.desc()).limit(5).all()
    
    return render_template('dashboard.html', total_visitors=total_visitors, today_count=today_count, visitors=visitors)

# Visitor Management Routes

# Add a new visitor
@app.route('/visitor/add', methods=['GET', 'POST'])
@login_required
def add_visitor():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        apartment = request.form.get('apartment')
        purpose = request.form.get('purpose')
        if name and phone and apartment and purpose:
            new_visitor = Visitor(name=name, phone=phone, apartment=apartment, purpose=purpose)
            db.session.add(new_visitor)
            db.session.commit()
            flash('Visitor added successfully.', 'success')
            return redirect(url_for('visitors'))
        else:
            flash('All fields are required.', 'danger')
    return render_template('add_visitor.html')

# List all visitor records
@app.route('/visitors')
@login_required
def visitors():
    visitor_list = Visitor.query.order_by(Visitor.entry_time.desc()).all()
    return render_template('visitors.html', visitors=visitor_list)

# Check out a visitor (record exit time)
@app.route('/visitor/checkout/<int:visitor_id>', methods=['POST'])
@login_required
def checkout(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    if not visitor.exit_time:
        visitor.exit_time = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(IST)
        db.session.commit()
        flash('Visitor checked out successfully.', 'success')
    else:
        flash('Visitor already checked out.', 'warning')
    return redirect(url_for('visitors'))

# Analytics & Reporting

# Render analytics page with chart placeholder
@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

# Data endpoint for analytics (e.g., visitors per apartment)
@app.route('/analytics/data')
@login_required
def analytics_data():
    results = db.session.query(Visitor.apartment, db.func.count(Visitor.id)).group_by(Visitor.apartment).all()
    data = {
        'apartments': [apartment for apartment, count in results],
        'counts': [count for apartment, count in results]
    }
    return jsonify(data)

if __name__ == '__main__':
    # Manually initialize tables and create default admin if not exists
    with app.app_context():
        create_tables()
    app.run(debug=True)
