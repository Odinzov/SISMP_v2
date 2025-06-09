import datetime
import functools
import os
import csv
import io
from pathlib import Path
from queue import Queue
import json

import jwt  # PyJWT
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from auth import auth_bp
from models import Task, Result, User, Comment, RiskEvent, db

# ── Flask set‑up ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(ROOT / "static"),  # all HTML/JS/CSS live here
    static_url_path="/"                  # make them available from /
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Extensions
CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# register auth blueprint (login, signup, token endpoints)
app.register_blueprint(auth_bp, url_prefix="/api")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")  # never keep this in code for prod!

# Subscribers for Server-Sent Events. Each connection adds a Queue to this list.
subscribers: list[Queue] = []

def publish_event(data: dict) -> None:
    """Send event to all subscribers."""
    for q in list(subscribers):
        q.put(data)

# ── Frontend entry ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the login page (or index.html, change if needed)."""
    return app.send_static_file("login.html")

# ── Helpers ─────────────────────────────────────────────────────────────────────

def require_auth(role: str | None = None):
    """Decorator to protect routes and optionally enforce a role list.

    Args:
        role: Pipe‑separated list of roles that may access the endpoint, e.g. "teacher|admin".
    """

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            header = request.headers.get("Authorization", "").split()
            if len(header) != 2 or header[0].lower() != "bearer":
                return jsonify({"msg": "token missing"}), 401
            try:
                payload = jwt.decode(header[1], JWT_SECRET, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify({"msg": "token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"msg": "token invalid"}), 401
            if role and payload["role"] not in role.split("|"):
                return jsonify({"msg": "forbidden"}), 403
            request.user = payload  # attach to request for handlers below
            return fn(*a, **kw)

        return wrapper

    return deco

# ── API: test results ───────────────────────────────────────────────────────────

@app.route("/api/test-result", methods=["POST"])
@require_auth()
def save_result():
    d = request.json
    r = Result(
        user_id=request.user["uid"],
        slug=d["slug"],
        score=d["score"],
        total=d["total"],
        passed_at=datetime.datetime.utcnow(),
    )
    db.session.add(r)
    db.session.commit()
    return "", 204


@app.route("/api/my-results")
@require_auth()
def my_results():
    rows = Result.query.filter_by(user_id=request.user["uid"]).all()
    return jsonify(
        [
            {
                "slug": r.slug,
                "score": r.score,
                "total": r.total,
                "date": r.passed_at.isoformat(),
            }
            for r in rows
        ]
    )


@app.route("/api/all-results")
@require_auth(role="teacher|admin")
def all_results():
    rows = db.session.query(Result, User.username).join(User, Result.user_id == User.id).all()
    return jsonify(
        [
            {
                "user": u,
                "slug": r.slug,
                "score": r.score,
                "total": r.total,
                "date": r.passed_at.isoformat(),
            }
            for r, u in rows
        ]
    )


@app.route("/api/profile", methods=["GET", "PATCH"])
@require_auth()
def profile():
    u = User.query.get_or_404(request.user["uid"])
    if request.method == "GET":
        return jsonify({"id": u.id, "username": u.username, "timezone": u.timezone})
    data = request.json
    if "timezone" in data:
        u.timezone = data["timezone"]
    if "username" in data:
        u.username = data["username"]
    db.session.commit()
    return "", 204


@app.route("/api/profile", methods=["GET", "PATCH"])
@require_auth()
def profile():
    u = User.query.get_or_404(request.user["uid"])
    if request.method == "GET":
        return jsonify({"id": u.id, "username": u.username, "timezone": u.timezone})
    data = request.json
    if "timezone" in data:
        u.timezone = data["timezone"]
    if "username" in data:
        u.username = data["username"]
    db.session.commit()
    return "", 204

# ── API: tasks ──────────────────────────────────────────────────────────────────

def task_dict(t: Task):
    return {
        "id": t.id,
        "name": t.name,
        "effort": t.effort,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "assignee": t.user_id,
        "status": t.status,
        "progress": t.progress,
        "priority": t.priority,
    }


@app.route("/api/tasks", methods=["GET", "POST"])
@require_auth(role="student|teacher|admin")
def tasks():
    if request.method == "POST":
        # only teacher or admin can create tasks
        if request.user["role"] not in ("teacher", "admin"):
            return jsonify({"msg": "forbidden"}), 403
        d = request.json
        t = Task(
            name=d["name"],
            effort=d.get("effort", 0),
            deadline=datetime.datetime.fromisoformat(d["deadline"]) if d.get("deadline") else None,
            status=d.get("status", "open"),
            priority=d.get("priority", "normal"),
        )
        db.session.add(t)
        db.session.commit()
        return jsonify(task_dict(t)), 201

    # GET: list tasks
    rows = Task.query.all()
    return jsonify([task_dict(t) for t in rows])


@app.route("/api/tasks/<int:tid>", methods=["GET", "PATCH"])
@require_auth(role="student|teacher|admin")
def task_detail(tid):
    t = Task.query.get_or_404(tid)
    if request.method == "GET":
        comments = Comment.query.filter_by(task_id=tid).all()
        return jsonify(
            {
                **task_dict(t),
                "comments": [
                    {
                        "user": c.user_id,
                        "text": c.text,
                        "date": c.created_at.isoformat(),
                    }
                    for c in comments
                ],
            }
        )

    # PATCH
    d = request.json
    if "progress" in d:
        if request.user["uid"] != t.user_id and request.user["role"] not in (
            "teacher",
            "admin",
        ):
            return jsonify({"msg": "forbidden"}), 403
        t.progress = int(d["progress"])
        if t.progress >= 100:
            t.status = "pending_review"
        now = datetime.datetime.utcnow()
        new_event = None
        if t.deadline and t.progress < 100 and t.deadline < now:
            new_event = RiskEvent(task_id=tid, message="Просрочка", created_at=now)
            db.session.add(new_event)
        elif t.deadline and t.progress < 50 and (t.deadline - now).days <= 2:
            new_event = RiskEvent(task_id=tid, message="Риск задержки", created_at=now)
            db.session.add(new_event)
    db.session.commit()
    if new_event:
        publish_event({
            "id": new_event.id,
            "task": new_event.task_id,
            "message": new_event.message,
            "date": new_event.created_at.isoformat(),
        })
    return "", 204


@app.route("/api/tasks/export")
@require_auth(role="student|teacher|admin")
def export_tasks():
    """Return all tasks as a CSV file."""
    rows = Task.query.all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "effort", "deadline", "assignee", "status", "priority"])
    for t in rows:
        writer.writerow(
            [
                t.id,
                t.name,
                t.effort,
                t.deadline.isoformat() if t.deadline else "",
                t.user_id or "",
                t.status,
                t.priority,
            ]
        )
    return Response(
        buf.getvalue(),
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=tasks.csv",
        },
    )


@app.route("/api/risk-events")
@require_auth(role="teacher|admin")
def risk_events():
    rows = RiskEvent.query.order_by(RiskEvent.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": r.id,
                "task": r.task_id,
                "message": r.message,
                "date": r.created_at.isoformat(),
            }
            for r in rows
        ]
    )


@app.route("/api/risk-stream")
def risk_stream():
    """Server-Sent Events endpoint broadcasting new risk events."""
    token = request.args.get("token")
    if not token:
        return "token required", 401
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return "invalid token", 401
    if payload.get("role") not in ("teacher", "admin"):
        return "forbidden", 403

    q: Queue = Queue()
    subscribers.append(q)

    def gen():
        try:
            while True:
                data = q.get()
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            subscribers.remove(q)

    return Response(gen(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/reports")
@require_auth(role="teacher|admin")
def reports():
    q = Task.query
    if "from" in request.args:
        q = q.filter(Task.deadline >= datetime.datetime.fromisoformat(request.args["from"]))
    if "to" in request.args:
        q = q.filter(Task.deadline <= datetime.datetime.fromisoformat(request.args["to"]))
    rows = q.all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "effort", "deadline", "assignee", "status", "priority"])
    for t in rows:
        writer.writerow(
            [
                t.id,
                t.name,
                t.effort,
                t.deadline.isoformat() if t.deadline else "",
                t.user_id or "",
                t.status,
                t.priority,
            ]
        )
    return Response(
        buf.getvalue(),
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=report.csv",
        },
    )


@app.route("/api/tasks/<int:tid>", methods=["GET", "PATCH"])
@require_auth(role="student|teacher|admin")
def task_detail(tid):
    t = Task.query.get_or_404(tid)
    if request.method == "GET":
        comments = Comment.query.filter_by(task_id=tid).all()
        return jsonify(
            {
                **task_dict(t),
                "comments": [
                    {
                        "user": c.user_id,
                        "text": c.text,
                        "date": c.created_at.isoformat(),
                    }
                    for c in comments
                ],
            }
        )

    # PATCH
    d = request.json
    if "progress" in d:
        if request.user["uid"] != t.user_id and request.user["role"] not in (
            "teacher",
            "admin",
        ):
            return jsonify({"msg": "forbidden"}), 403
        t.progress = int(d["progress"])
        if t.progress >= 100:
            t.status = "pending_review"
        now = datetime.datetime.utcnow()
        new_event = None
        if t.deadline and t.progress < 100 and t.deadline < now:
            new_event = RiskEvent(task_id=tid, message="Просрочка", created_at=now)
            db.session.add(new_event)
        elif t.deadline and t.progress < 50 and (t.deadline - now).days <= 2:
            new_event = RiskEvent(task_id=tid, message="Риск задержки", created_at=now)
            db.session.add(new_event)
    db.session.commit()
    if new_event:
        publish_event({
            "id": new_event.id,
            "task": new_event.task_id,
            "message": new_event.message,
            "date": new_event.created_at.isoformat(),
        })
    return "", 204


@app.route("/api/tasks/export")
@require_auth(role="student|teacher|admin")
def export_tasks():
    """Return all tasks as a CSV file."""
    rows = Task.query.all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "effort", "deadline", "assignee", "status"])
    for t in rows:
        writer.writerow(
            [
                t.id,
                t.name,
                t.effort,
                t.deadline.isoformat() if t.deadline else "",
                t.user_id or "",
                t.status,
            ]
        )
    return Response(
        buf.getvalue(),
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=tasks.csv",
        },
    )


@app.route("/api/tasks/<int:tid>", methods=["PUT"])
@require_auth(role="student|teacher|admin")
def update_task(tid):
    if request.user["role"] not in ("teacher", "admin"):
        return jsonify({"msg": "forbidden"}), 403
    t = Task.query.get_or_404(tid)
    d = request.json
    for k in ("name", "effort", "status", "priority"):
        if k in d:
            setattr(t, k, d[k])
    if "deadline" in d:
        t.deadline = (
            datetime.datetime.fromisoformat(d["deadline"]) if d["deadline"] else None
        )
    db.session.commit()
    return "", 204


@app.route("/api/tasks/<int:tid>/claim", methods=["POST"])
@require_auth()
def claim_task(tid):
    t = Task.query.get_or_404(tid)
    if t.user_id:
        return jsonify({"msg": "taken"}), 409
    t.user_id = request.user["uid"]
    t.status = "in_progress"
    db.session.commit()
    return "", 204


@app.route("/api/tasks/<int:tid>/release", methods=["POST"])
@require_auth()
def release_task(tid):
    t = Task.query.get_or_404(tid)
    if t.user_id != request.user["uid"]:
        return jsonify({"msg": "not yours"}), 403
    t.user_id = None
    t.status = "open"
    db.session.commit()
    return "", 204


@app.route("/api/tasks/<int:tid>/comment", methods=["POST"])
@require_auth(role="student|teacher|admin")
def add_comment(tid):
    t = Task.query.get_or_404(tid)
    d = request.json
    c = Comment(
        task_id=tid,
        user_id=request.user["uid"],
        text=d.get("text", ""),
        created_at=datetime.datetime.utcnow(),
    )
    db.session.add(c)
    db.session.commit()
    return "", 201


@app.route("/api/tasks/<int:tid>/comment", methods=["POST"])
@require_auth(role="student|teacher|admin")
def add_comment(tid):
    t = Task.query.get_or_404(tid)
    d = request.json
    c = Comment(
        task_id=tid,
        user_id=request.user["uid"],
        text=d.get("text", ""),
        created_at=datetime.datetime.utcnow(),
    )
    db.session.add(c)
    db.session.commit()
    return "", 201

# ── Main entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # debug=True is fine for local dev; use Gunicorn/Uvicorn + Nginx for prod
    app.run(debug=True)
