from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def init_db(app):
    """
    Initialize database with Flask application.
    Creates tables automatically on startup if they do not exist.
    """
    db.init_app(app)
    with app.app_context():
        # Import models inside context to avoid circular dependencies
        import models  # noqa: F401
        db.create_all()
