from flask import Blueprint, request, jsonify
from models import BinLocation
from db import db
from auth import role_required

bp = Blueprint('bins', __name__, url_prefix='/api/bins')


@bp.route('', methods=['GET'])
def list_bins():
    bins = BinLocation.query.all()
    return jsonify([{'id': b.id, 'code': b.code, 'capacity': b.capacity} for b in bins])


@bp.route('', methods=['POST'])
@role_required(['admin', 'manager'])
def create_bin():
    data = request.get_json() or {}
    code = data.get('code')
    capacity = data.get('capacity')
    if not code:
        return jsonify({'error': 'code required'}), 400
    if BinLocation.query.filter_by(code=code).first():
        return jsonify({'error': 'bin exists'}), 400
    b = BinLocation(code=code, capacity=capacity)
    db.session.add(b)
    db.session.commit()
    return jsonify({'id': b.id, 'code': b.code}), 201
