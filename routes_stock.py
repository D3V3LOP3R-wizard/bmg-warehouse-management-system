from flask import Blueprint, request, jsonify
from models import Product, BinLocation, StockItem, StockMovement
from db import db
from auth import role_required
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('stock', __name__, url_prefix='/api/stock')


@bp.route('/receive', methods=['POST'])
@role_required(['admin', 'manager', 'employee'])
def receive_stock():
    data = request.get_json() or {}
    part = data.get('part_number')
    bin_code = data.get('bin_code')
    qty = int(data.get('quantity', 0))
    batch = data.get('batch')

    product = Product.query.filter_by(part_number=part).first()
    if not product:
        return jsonify({'error': 'product not found'}), 404
    binloc = BinLocation.query.filter_by(code=bin_code).first()
    if not binloc:
        return jsonify({'error': 'bin not found'}), 404

    item = StockItem.query.filter_by(product_id=product.id, bin_id=binloc.id, batch=batch).first()
    if not item:
        item = StockItem(product_id=product.id, bin_id=binloc.id, quantity=qty, batch=batch)
        db.session.add(item)
    else:
        item.quantity += qty

    movement = StockMovement(product_id=product.id, from_bin_id=None, to_bin_id=binloc.id, quantity=qty, user_id=get_jwt_identity().get('id'), reason='receive')
    db.session.add(movement)
    db.session.commit()
    return jsonify({'msg': 'received', 'product': product.part_number, 'bin': binloc.code, 'quantity': item.quantity})


@bp.route('/dispatch', methods=['POST'])
@role_required(['admin', 'manager', 'employee'])
def dispatch_stock():
    data = request.get_json() or {}
    part = data.get('part_number')
    bin_code = data.get('bin_code')
    qty = int(data.get('quantity', 0))

    product = Product.query.filter_by(part_number=part).first()
    if not product:
        return jsonify({'error': 'product not found'}), 404
    binloc = BinLocation.query.filter_by(code=bin_code).first()
    if not binloc:
        return jsonify({'error': 'bin not found'}), 404

    item = StockItem.query.filter_by(product_id=product.id, bin_id=binloc.id).first()
    if not item or item.quantity < qty:
        return jsonify({'error': 'insufficient stock'}), 400

    item.quantity -= qty
    movement = StockMovement(product_id=product.id, from_bin_id=binloc.id, to_bin_id=None, quantity=qty, user_id=get_jwt_identity().get('id'), reason='dispatch')
    db.session.add(movement)
    db.session.commit()
    return jsonify({'msg': 'dispatched', 'remaining': item.quantity})


@bp.route('/transfer', methods=['POST'])
@role_required(['admin', 'manager', 'employee'])
def transfer_stock():
    data = request.get_json() or {}
    part = data.get('part_number')
    from_bin_code = data.get('from_bin')
    to_bin_code = data.get('to_bin')
    qty = int(data.get('quantity', 0))

    product = Product.query.filter_by(part_number=part).first()
    if not product:
        return jsonify({'error': 'product not found'}), 404
    from_bin = BinLocation.query.filter_by(code=from_bin_code).first()
    to_bin = BinLocation.query.filter_by(code=to_bin_code).first()
    if not from_bin or not to_bin:
        return jsonify({'error': 'bin not found'}), 404

    item_from = StockItem.query.filter_by(product_id=product.id, bin_id=from_bin.id).first()
    if not item_from or item_from.quantity < qty:
        return jsonify({'error': 'insufficient stock in source bin'}), 400

    item_from.quantity -= qty
    item_to = StockItem.query.filter_by(product_id=product.id, bin_id=to_bin.id).first()
    if not item_to:
        item_to = StockItem(product_id=product.id, bin_id=to_bin.id, quantity=qty)
        db.session.add(item_to)
    else:
        item_to.quantity += qty

    movement = StockMovement(product_id=product.id, from_bin_id=from_bin.id, to_bin_id=to_bin.id, quantity=qty, user_id=get_jwt_identity().get('id'), reason='transfer')
    db.session.add(movement)
    db.session.commit()
    return jsonify({'msg': 'transferred', 'from_remaining': item_from.quantity, 'to_quantity': item_to.quantity})


@bp.route('/items', methods=['GET'])
def list_items():
    items = StockItem.query.all()
    out = []
    for it in items:
        out.append({'id': it.id, 'part_number': it.product.part_number, 'bin': it.bin.code, 'quantity': it.quantity, 'batch': it.batch})
    return jsonify(out)
