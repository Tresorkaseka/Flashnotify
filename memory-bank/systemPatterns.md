# System Patterns

## Architecture
- **Backend**: Flask (Python).
- **Database**: SQLAlchemy (SQLite dev, PostgreSQL prod).
- **Async**: Custom threading queue / Celery (optional).
- **Frontend**: Jinja2 Templates + Static assets.

## Key Decisions
- Use `gunicorn` for production serving.
- Use environment variables for configuration (`DATABASE_URL`, `SECRET_KEY`).
