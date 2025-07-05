# main.py

from db.base import Base, engine
from db.models.inventory import Inventory


def initialize_database():
    """Create tables in the SQLite database if they don't exist."""
    Base.metadata.create_all(engine)
    print("Database initialized with all tables.")


if __name__ == "__main__":
    initialize_database()
