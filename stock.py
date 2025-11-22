from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import uuid
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bmg_warehouse_secret_key_2023'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bmg_warehouse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, manager, employee
    department = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    part_number = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    unit_price = db.Column(db.Float, default=0.0)
    min_stock_level = db.Column(db.Integer, default=0)
    max_stock_level = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BinLocation(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bin_code = db.Column(db.String(20), unique=True, nullable=False)
    zone = db.Column(db.String(10), nullable=False)
    aisle = db.Column(db.String(10))
    shelf = db.Column(db.String(10))
    capacity = db.Column(db.Integer, default=100)
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance

class StockItem(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    bin_location_id = db.Column(db.String(36), db.ForeignKey('bin_location.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    batch_number = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    date_received = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = db.relationship('Product', backref=db.backref('stock_items', lazy=True))
    bin_location = db.relationship('BinLocation', backref=db.backref('stock_items', lazy=True))

class StockMovement(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    from_bin_id = db.Column(db.String(36), db.ForeignKey('bin_location.id'))
    to_bin_id = db.Column(db.String(36), db.ForeignKey('bin_location.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # receive, dispatch, transfer, adjustment
    reference_number = db.Column(db.String(100))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    movement_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    product = db.relationship('Product', backref=db.backref('movements', lazy=True))
    user = db.relationship('User', backref=db.backref('movements', lazy=True))

class Stocktake(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    bin_location_id = db.Column(db.String(36), db.ForeignKey('bin_location.id'), nullable=False)
    expected_quantity = db.Column(db.Integer, nullable=False)
    counted_quantity = db.Column(db.Integer, nullable=False)
    variance = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    stocktake_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved

# Authentication Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            token = token.split(' ')[1]  # Remove Bearer prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
        
    return decorated

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists!'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists!'}), 400
        
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        role=data.get('role', 'employee'),
        department=data.get('department', 'warehouse')
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully!'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'department': user.department
            }
        })
    
    return jsonify({'message': 'Invalid credentials!'}), 401

# Product Management
@app.route('/api/products', methods=['GET'])
@token_required
def get_products(current_user):
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'part_number': p.part_number,
        'description': p.description,
        'category': p.category,
        'manufacturer': p.manufacturer,
        'unit_price': p.unit_price,
        'min_stock_level': p.min_stock_level,
        'max_stock_level': p.max_stock_level,
        'current_stock': sum(si.quantity for si in p.stock_items)
    } for p in products])

@app.route('/api/products', methods=['POST'])
@token_required
def create_product(current_user):
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'message': 'Insufficient permissions!'}), 403
        
    data = request.get_json()
    
    if Product.query.filter_by(part_number=data['part_number']).first():
        return jsonify({'message': 'Part number already exists!'}), 400
        
    product = Product(
        part_number=data['part_number'],
        description=data['description'],
        category=data.get('category'),
        manufacturer=data.get('manufacturer'),
        unit_price=data.get('unit_price', 0.0),
        min_stock_level=data.get('min_stock_level', 0),
        max_stock_level=data.get('max_stock_level', 1000)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'message': 'Product created successfully!'}), 201

# Stock Management
@app.route('/api/stock/check', methods=['POST'])
@token_required
def check_stock(current_user):
    data = request.get_json()
    search_term = data.get('search_term', '').upper()
    
    # Search by part number or description
    products = Product.query.filter(
        (Product.part_number.contains(search_term)) | 
        (Product.description.contains(search_term))
    ).all()
    
    results = []
    for product in products:
        stock_items = StockItem.query.filter_by(product_id=product.id).all()
        
        for stock_item in stock_items:
            results.append({
                'part_number': product.part_number,
                'description': product.description,
                'current_bin': stock_item.bin_location.bin_code,
                'correct_bin': stock_item.bin_location.bin_code,  # In real system, this might be different
                'quantity': stock_item.quantity,
                'status': 'correct',  # This would be determined by business logic
                'batch_number': stock_item.batch_number,
                'zone': stock_item.bin_location.zone
            })
    
    return jsonify(results)

@app.route('/api/stock/receive', methods=['POST'])
@token_required
def receive_stock(current_user):
    data = request.get_json()
    
    product = Product.query.filter_by(part_number=data['part_number']).first()
    if not product:
        return jsonify({'message': 'Product not found!'}), 404
        
    bin_location = BinLocation.query.filter_by(bin_code=data['bin_code']).first()
    if not bin_location:
        return jsonify({'message': 'Bin location not found!'}), 404
    
    # Check if stock item already exists in this bin
    stock_item = StockItem.query.filter_by(
        product_id=product.id, 
        bin_location_id=bin_location.id
    ).first()
    
    if stock_item:
        stock_item.quantity += data['quantity']
    else:
        stock_item = StockItem(
            product_id=product.id,
            bin_location_id=bin_location.id,
            quantity=data['quantity'],
            batch_number=data.get('batch_number'),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d') if data.get('expiry_date') else None
        )
        db.session.add(stock_item)
    
    # Record movement
    movement = StockMovement(
        product_id=product.id,
        to_bin_id=bin_location.id,
        quantity=data['quantity'],
        movement_type='receive',
        reference_number=data.get('reference_number'),
        user_id=current_user.id,
        notes=data.get('notes')
    )
    db.session.add(movement)
    
    db.session.commit()
    
    return jsonify({'message': 'Stock received successfully!'}), 201

@app.route('/api/stock/dispatch', methods=['POST'])
@token_required
def dispatch_stock(current_user):
    data = request.get_json()
    
    product = Product.query.filter_by(part_number=data['part_number']).first()
    if not product:
        return jsonify({'message': 'Product not found!'}), 404
        
    bin_location = BinLocation.query.filter_by(bin_code=data['bin_code']).first()
    if not bin_location:
        return jsonify({'message': 'Bin location not found!'}), 404
    
    stock_item = StockItem.query.filter_by(
        product_id=product.id, 
        bin_location_id=bin_location.id
    ).first()
    
    if not stock_item or stock_item.quantity < data['quantity']:
        return jsonify({'message': 'Insufficient stock available!'}), 400
    
    stock_item.quantity -= data['quantity']
    
    # Record movement
    movement = StockMovement(
        product_id=product.id,
        from_bin_id=bin_location.id,
        quantity=data['quantity'],
        movement_type='dispatch',
        reference_number=data.get('reference_number'),
        user_id=current_user.id,
        notes=data.get('notes')
    )
    db.session.add(movement)
    
    db.session.commit()
    
    return jsonify({'message': 'Stock dispatched successfully!'}), 200

# Bin Location Management
@app.route('/api/bins', methods=['GET'])
@token_required
def get_bins(current_user):
    bins = BinLocation.query.all()
    return jsonify([{
        'id': b.id,
        'bin_code': b.bin_code,
        'zone': b.zone,
        'aisle': b.aisle,
        'shelf': b.shelf,
        'capacity': b.capacity,
        'status': b.status,
        'current_usage': sum(si.quantity for si in b.stock_items)
    } for b in bins])

@app.route('/api/stock/transfer', methods=['POST'])
@token_required
def transfer_stock(current_user):
    data = request.get_json()
    
    product = Product.query.filter_by(part_number=data['part_number']).first()
    if not product:
        return jsonify({'message': 'Product not found!'}), 404
        
    from_bin = BinLocation.query.filter_by(bin_code=data['from_bin']).first()
    to_bin = BinLocation.query.filter_by(bin_code=data['to_bin']).first()
    
    if not from_bin or not to_bin:
        return jsonify({'message': 'Bin location not found!'}), 404
    
    # Check stock in source bin
    stock_item = StockItem.query.filter_by(
        product_id=product.id, 
        bin_location_id=from_bin.id
    ).first()
    
    if not stock_item or stock_item.quantity < data['quantity']:
        return jsonify({'message': 'Insufficient stock in source bin!'}), 400
    
    # Remove from source bin
    stock_item.quantity -= data['quantity']
    
    # Add to destination bin
    dest_stock_item = StockItem.query.filter_by(
        product_id=product.id, 
        bin_location_id=to_bin.id
    ).first()
    
    if dest_stock_item:
        dest_stock_item.quantity += data['quantity']
    else:
        dest_stock_item = StockItem(
            product_id=product.id,
            bin_location_id=to_bin.id,
            quantity=data['quantity'],
            batch_number=stock_item.batch_number,
            expiry_date=stock_item.expiry_date
        )
        db.session.add(dest_stock_item)
    
    # Record movement
    movement = StockMovement(
        product_id=product.id,
        from_bin_id=from_bin.id,
        to_bin_id=to_bin.id,
        quantity=data['quantity'],
        movement_type='transfer',
        user_id=current_user.id,
        notes=data.get('notes')
    )
    db.session.add(movement)
    
    db.session.commit()
    
    return jsonify({'message': 'Stock transferred successfully!'}), 200

# Stocktake Management
@app.route('/api/stocktake', methods=['POST'])
@token_required
def perform_stocktake(current_user):
    data = request.get_json()
    
    product = Product.query.filter_by(part_number=data['part_number']).first()
    if not product:
        return jsonify({'message': 'Product not found!'}), 404
        
    bin_location = BinLocation.query.filter_by(bin_code=data['bin_code']).first()
    if not bin_location:
        return jsonify({'message': 'Bin location not found!'}), 404
    
    stock_item = StockItem.query.filter_by(
        product_id=product.id, 
        bin_location_id=bin_location.id
    ).first()
    
    expected_quantity = stock_item.quantity if stock_item else 0
    counted_quantity = data['counted_quantity']
    variance = counted_quantity - expected_quantity
    
    stocktake = Stocktake(
        product_id=product.id,
        bin_location_id=bin_location.id,
        expected_quantity=expected_quantity,
        counted_quantity=counted_quantity,
        variance=variance,
        user_id=current_user.id,
        status='pending'
    )
    db.session.add(stocktake)
    
    # If variance is found, create adjustment movement
    if variance != 0:
        movement_type = 'adjustment_positive' if variance > 0 else 'adjustment_negative'
        
        movement = StockMovement(
            product_id=product.id,
            to_bin_id=bin_location.id if variance > 0 else None,
            from_bin_id=bin_location.id if variance < 0 else None,
            quantity=abs(variance),
            movement_type='adjustment',
            user_id=current_user.id,
            notes=f'Stocktake adjustment: {variance}'
        )
        db.session.add(movement)
        
        # Update stock quantity
        if stock_item:
            stock_item.quantity = counted_quantity
        else:
            stock_item = StockItem(
                product_id=product.id,
                bin_location_id=bin_location.id,
                quantity=counted_quantity
            )
            db.session.add(stock_item)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Stocktake recorded successfully!',
        'variance': variance
    }), 201

# Reports and Analytics
@app.route('/api/reports/stock-levels', methods=['GET'])
@token_required
def stock_level_report(current_user):
    products = Product.query.all()
    
    report_data = []
    for product in products:
        total_stock = sum(si.quantity for si in product.stock_items)
        status = 'normal'
        
        if total_stock <= product.min_stock_level:
            status = 'low'
        elif total_stock >= product.max_stock_level:
            status = 'high'
        
        report_data.append({
            'part_number': product.part_number,
            'description': product.description,
            'current_stock': total_stock,
            'min_stock_level': product.min_stock_level,
            'max_stock_level': product.max_stock_level,
            'status': status
        })
    
    return jsonify(report_data)

@app.route('/api/reports/movements', methods=['GET'])
@token_required
def movement_report(current_user):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = StockMovement.query
    
    if start_date:
        query = query.filter(StockMovement.movement_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(StockMovement.movement_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    movements = query.order_by(StockMovement.movement_date.desc()).all()
    
    return jsonify([{
        'id': m.id,
        'part_number': m.product.part_number,
        'description': m.product.description,
        'movement_type': m.movement_type,
        'quantity': m.quantity,
        'from_bin': m.from_bin.bin_code if m.from_bin else None,
        'to_bin': m.to_bin.bin_code if m.to_bin else None,
        'user': m.user.username,
        'movement_date': m.movement_date.isoformat(),
        'reference_number': m.reference_number,
        'notes': m.notes
    } for m in movements])

# Dashboard Data
@app.route('/api/dashboard', methods=['GET'])
@token_required
def dashboard_data(current_user):
    total_products = Product.query.count()
    total_bins = BinLocation.query.count()
    
    # Calculate stock accuracy (simplified)
    total_stocktakes = Stocktake.query.count()
    accurate_stocktakes = Stocktake.query.filter_by(variance=0).count()
    accuracy_rate = (accurate_stocktakes / total_stocktakes * 100) if total_stocktakes > 0 else 100
    
    # Recent discrepancies
    recent_discrepancies = Stocktake.query.filter(Stocktake.variance != 0)\
        .order_by(Stocktake.stocktake_date.desc())\
        .limit(10).all()
    
    # Low stock alerts
    products = Product.query.all()
    low_stock_alerts = []
    for product in products:
        total_stock = sum(si.quantity for si in product.stock_items)
        if total_stock <= product.min_stock_level:
            low_stock_alerts.append({
                'part_number': product.part_number,
                'description': product.description,
                'current_stock': total_stock,
                'min_stock_level': product.min_stock_level
            })
    
    return jsonify({
        'total_products': total_products,
        'total_bins': total_bins,
        'stock_accuracy': round(accuracy_rate, 2),
        'total_discrepancies': Stocktake.query.filter(Stocktake.variance != 0).count(),
        'recent_discrepancies': [{
            'part_number': rd.product.part_number,
            'bin_location': rd.bin_location.bin_code,
            'variance': rd.variance,
            'date': rd.stocktake_date.isoformat()
        } for rd in recent_discrepancies],
        'low_stock_alerts': low_stock_alerts
    })

# Initialize Database
@app.route('/api/init-db', methods=['POST'])
def init_db():
    db.create_all()
    
    # Create default admin user
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@bmgworld.net',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin',
            department='management'
        )
        db.session.add(admin_user)
    
    # Create sample bin locations
    if BinLocation.query.count() == 0:
        zones = ['A', 'B', 'C', 'D']
        for zone in zones:
            for aisle in range(1, 6):
                for shelf in range(1, 11):
                    bin_location = BinLocation(
                        bin_code=f"{zone}-{aisle:02d}-{shelf:02d}",
                        zone=zone,
                        aisle=str(aisle),
                        shelf=str(shelf)
                    )
                    db.session.add(bin_location)
    
    # Create sample products
    if Product.query.count() == 0:
        sample_products = [
            {
                'part_number': 'BMG-12345',
                'description': 'Ball Bearing 6305-2RS',
                'category': 'Bearings',
                'manufacturer': 'BMG',
                'min_stock_level': 10,
                'max_stock_level': 100
            },
            {
                'part_number': 'BMG-67890',
                'description': 'Taper Roller Bearing 30206',
                'category': 'Bearings',
                'manufacturer': 'BMG',
                'min_stock_level': 5,
                'max_stock_level': 50
            }
        ]
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)
    
    db.session.commit()
    
    return jsonify({'message': 'Database initialized successfully!'})

if __name__ == '__main__':
    app.run(debug=True)