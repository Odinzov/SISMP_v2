from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # bcrypt-хэш
    role     = db.Column(db.String(10), default='student')  # student|teacher|admin

class Result(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
    slug      = db.Column(db.String(40))   # intro|syntax|...
    score     = db.Column(db.Integer)
    total     = db.Column(db.Integer)
    passed_at = db.Column(db.DateTime)


class Task(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(120), nullable=False)
    effort   = db.Column(db.Integer)  # hours
    deadline = db.Column(db.DateTime)
    user_id  = db.Column(db.Integer, db.ForeignKey('user.id'))
    status   = db.Column(db.String(20), default='open')  # open|in_progress|done
