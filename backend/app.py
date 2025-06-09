import datetime, functools, jwt, os
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Result, User
from auth import auth_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app)

with app.app_context():
    db.create_all()

app.register_blueprint(auth_bp, url_prefix='/api')
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret')

def require_auth(role=None):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            hdr = request.headers.get('Authorization', '').split()
            if len(hdr)!=2 or hdr[0].lower()!='bearer':
                return jsonify({'msg':'token missing'}), 401
            try:
                payload = jwt.decode(hdr[1], JWT_SECRET, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({'msg':'token expired'}), 401
            if role and payload['role'] not in role.split('|'):
                return jsonify({'msg':'forbidden'}), 403
            request.user = payload
            return fn(*a, **kw)
        return wrapper
    return deco

@app.route('/api/test-result', methods=['POST'])
@require_auth()
def save_result():
    d=request.json
    r=Result(user_id=request.user['uid'], slug=d['slug'],
             score=d['score'], total=d['total'],
             passed_at=datetime.datetime.utcnow())
    db.session.add(r); db.session.commit()
    return '',204

@app.route('/api/my-results')
@require_auth()
def my_results():
    rows=Result.query.filter_by(user_id=request.user['uid']).all()
    return jsonify([{'slug':r.slug,'score':r.score,'total':r.total,
                     'date':r.passed_at.isoformat()} for r in rows])

@app.route('/api/all-results')
@require_auth(role='teacher|admin')
def all_results():
    rows=(db.session.query(Result, User.username)
          .join(User, Result.user_id==User.id).all())
    return jsonify([{'user':u,'slug':r.slug,'score':r.score,
                     'total':r.total,'date':r.passed_at.isoformat()}
                     for r,u in rows])

if __name__ == '__main__':
    app.run(debug=True)
