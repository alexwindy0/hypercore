"""
Database Configuration and Initialization
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db():
    """Create all database tables"""
    db.create_all()
    print("Database tables initialized successfully")

# Enable SQLite foreign key support (for development/testing)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite"""
    if 'sqlite' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
