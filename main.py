# main.py
from sqlalchemy.orm import Session
from db.base import Base, engine
from db.models.inventory import Inventory
from db.models.user import User
from db.models.order import Order
from db.models.item_catalog import ItemCatalog
from db.admin_actions import AdminActions
from db.models.order import ArticleEnum
from db.models.acquisition import AcquisitionType
from db.user_actions import UserActions


def initialize_database():
    """Create tables in the SQLite database if they don't exist."""
    Base.metadata.create_all(engine)
    print("Database initialized with all tables.")

def re_initialize_database():
    """Create tables in the SQLite database if they don't exist."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database initialized with all tables.")
    
def seed_initial_inventory():
    with Session(engine) as session:
        AdminActions.initialize_inventory(session)

def seed_test_users():
    with Session(engine) as session:
        AdminActions.create_test_users(session)

def seed_prices():
    with Session(engine) as session:
        AdminActions.initialize_item_catalog(session)

def test_order():
    with Session(engine) as session:
        order = UserActions.place_order(
            session=session,
            user_id=1,
            article=ArticleEnum.XATTY_CARTRIDGE,
            acquisition_type=AcquisitionType.STANDARD,
        )
        print(f"Order placed: {order.article} for {order.value:.2f} chuan")


if __name__ == "__main__":
    re_initialize_database()
    seed_initial_inventory() 
    seed_test_users()
    seed_prices()
    test_order()