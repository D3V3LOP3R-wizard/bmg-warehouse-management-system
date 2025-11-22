from flask import Blueprint, request, jsonify
from models import Product
from db import db
from auth import role_required

bp = Blueprint('products', __name__, url_prefix='/api/products')


@bp.route('', methods=['GET'])
def list_products():
    q = Product.query.all()
    return jsonify([{'id': p.id, 'part_number': p.part_number, 'description': p.description} for p in q])


@bp.route('', methods=['POST'])
@role_required(['admin', 'manager'])
def create_product():
    data = request.get_json() or {}
    part = data.get('part_number')
    desc = data.get('description')
    if not part:
        return jsonify({'error': 'part_number required'}), 400
    if Product.query.filter_by(part_number=part).first():
        return jsonify({'error': 'part exists'}), 400
    p = Product(part_number=part, description=desc)
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id, 'part_number': p.part_number}), 201
