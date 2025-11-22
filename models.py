from datetime import datetime
from db import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default='employee')


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BinLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StockItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin_location.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    batch = db.Column(db.String(120), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)

    product = db.relationship('Product')
    bin = db.relationship('BinLocation')


class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    from_bin_id = db.Column(db.Integer, db.ForeignKey('bin_location.id'), nullable=True)
    to_bin_id = db.Column(db.Integer, db.ForeignKey('bin_location.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    from_bin = db.relationship('BinLocation', foreign_keys=[from_bin_id])
    to_bin = db.relationship('BinLocation', foreign_keys=[to_bin_id])


class StocktakeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    bin_id = db.Column(db.Integer, db.ForeignKey('bin_location.id'))
    counted_quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(255), nullable=True)

    product = db.relationship('Product')
    bin = db.relationship('BinLocation')
