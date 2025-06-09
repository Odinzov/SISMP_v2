from datetime import datetime, timedelta
from passlib.hash import bcrypt

from app import app, db
from models import User, Task


def create_user(username: str, email: str, password: str, role: str = "student") -> User:
    """Create user if absent and return the instance."""
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=email,
            password=bcrypt.hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
    return user


def create_task(**kwargs) -> None:
    """Create task if one with the same name does not exist."""
    if Task.query.filter_by(name=kwargs["name"]).first():
        return
    t = Task(**kwargs)
    db.session.add(t)


with app.app_context():
    db.create_all()

    tl = create_user("teamlead", "tl@example.com", "tlpass", role="teacher")
    alice = create_user("alice", "alice@example.com", "alicepass")
    bob = create_user("bob", "bob@example.com", "bobpass")
    charlie = create_user("charlie", "charlie@example.com", "charliepass")

    now = datetime.utcnow()
    create_task(
        name="Подготовить отчёт",
        description="Сформировать итоговый отчёт проекта",
        effort=5,
        deadline=now + timedelta(days=3),
        user_id=alice.id,
    )
    create_task(
        name="Обновить календарь",
        description="Заполнить календарь событий",
        effort=3,
        deadline=now + timedelta(days=5),
        user_id=bob.id,
        status="in_progress",
        progress=50,
    )
    create_task(
        name="Исправить ошибки",
        description="Закрыть баги из трекера",
        effort=4,
        deadline=now + timedelta(days=7),
        user_id=None,
    )

    db.session.commit()
    print("Demo data loaded.")
