from datetime import datetime, timedelta, timezone
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

    now = datetime.now(timezone.utc)
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

    # дополнительные задания для студентов
    # ----- задачи Алисы -----
    create_task(
        name="Составить план тестирования",
        description="Определить набор тестов и критерии приёмки",
        effort=2,
        deadline=now + timedelta(days=5),
        user_id=alice.id,
    )
    create_task(
        name="Обновить документацию",
        description="Актуализировать README и wiki проекта",
        effort=3,
        deadline=now + timedelta(days=8),
        user_id=alice.id,
    )
    create_task(
        name="Проверить отчёт о рисках",
        description="Проанализировать новые потенциальные риски",
        effort=1,
        deadline=now + timedelta(days=10),
        user_id=alice.id,
    )

    # ----- задачи Боба -----
    create_task(
        name="Настроить CI",
        description="Автоматическая сборка и тесты в GitHub Actions",
        effort=4,
        deadline=now + timedelta(days=4),
        user_id=bob.id,
    )
    create_task(
        name="Оптимизировать запросы",
        description="Ускорить работу API путём оптимизации SQL",
        effort=5,
        deadline=now + timedelta(days=9),
        user_id=bob.id,
    )
    create_task(
        name="Рефакторинг модуля авторизации",
        description="Упростить и улучшить безопасность логина",
        effort=3,
        deadline=now + timedelta(days=11),
        user_id=bob.id,
    )

    # ----- задачи Чарли -----
    create_task(
        name="Разработать прототип UI",
        description="Подготовить черновые макеты интерфейса",
        effort=5,
        deadline=now + timedelta(days=6),
        user_id=charlie.id,
    )
    create_task(
        name="Написать unit-тесты",
        description="Покрыть критические функции тестами",
        effort=4,
        deadline=now + timedelta(days=8),
        user_id=charlie.id,
    )
    create_task(
        name="Подготовить презентацию",
        description="Слайды для демонстрации проекта",
        effort=2,
        deadline=now + timedelta(days=12),
        user_id=charlie.id,
    )

    db.session.commit()
    print("Demo data loaded.")
