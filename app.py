from flask import Flask, jsonify, request, send_from_directory
from db import init_db
from flask_jwt_extended import JWTManager
import os

def create_app():
    app = Flask(__name__, static_folder='.', static_url_path='')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///wms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'change-me')

    db = init_db(app)
    JWTManager(app)

    # register blueprints
    from auth import bp as auth_bp
    from routes_products import bp as products_bp
    from routes_bins import bp as bins_bp
    from routes_stock import bp as stock_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(bins_bp)
    app.register_blueprint(stock_bp)

    @app.route('/')
    def index():
        return send_from_directory('.', 'stock.html')

    @app.route('/api/init-db', methods=['POST'])
    def init_db_route():
        from models import User, Product, BinLocation
        from werkzeug.security import generate_password_hash

        with app.app_context():
            db.create_all()
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', password_hash=generate_password_hash('adminpass'), role='admin')
                db.session.add(admin)
            # sample data
            if not Product.query.filter_by(part_number='BMG-12345').first():
                p = Product(part_number='BMG-12345', description='Ball Bearing 6305-2RS')
                db.session.add(p)
            if not BinLocation.query.filter_by(code='A-12-04').first():
                b = BinLocation(code='A-12-04', capacity=100)
                db.session.add(b)
            db.session.commit()
        return jsonify({'msg': 'db initialized'})

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
