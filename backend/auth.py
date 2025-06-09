import datetime, jwt, os
from flask import Blueprint, request, jsonify
from passlib.hash import bcrypt
from models import db, User

auth_bp = Blueprint('auth', __name__)
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret')

def make_token(user):
    payload = {
        'uid':  user.id,
        'u':    user.username,
        'role': user.role,
        'exp':  datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return jsonify({'msg': 'user exists'}), 409
    user = User(
        username=data['username'],
        email=data['email'],
        password=bcrypt.hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(token=make_token(user))

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    ident = data.get('username')
    user = User.query.filter((User.username == ident) | (User.email == ident)).first()
    if not user or not bcrypt.verify(data['password'], user.password):
        return jsonify({'msg':'bad creds'}), 401
    return jsonify(token=make_token(user))
