# main.py
from sqlalchemy.orm import Session
from db.base import Base, engine
from db.models.inventory import Inventory
from db.models.user import User
from db.models.order import Order
from db.admin_actions import AdminActions


def initialize_database():
    """Create tables in the SQLite database if they don't exist."""
    Base.metadata.create_all(engine)
    print("Database initialized with all tables.")
    
def seed_initial_inventory():
    with Session(engine) as session:
        AdminActions.initialize_inventory(session)

def seed_test_users():
    with Session(engine) as session:
        AdminActions.create_test_users(session)


if __name__ == "__main__":
    initialize_database()
    seed_initial_inventory()
    seed_test_users()
