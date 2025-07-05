# db/user_actions.py

from datetime import date, datetime
from sqlalchemy.orm import Session
from db.models.user import User
from db.models.order import Order, ArticleEnum
from db.models.item_catalog import ItemCatalog
from db.models.inventory import Inventory
from db.models.acquisition import AcquisitionType


ACQUISITION_RULES = {
    AcquisitionType.QUICK: {"cooldown": 1, "price_factor": 2.00},
    AcquisitionType.STANDARD: {"cooldown": 2, "price_factor": 1.00},
    AcquisitionType.SMART: {"cooldown": 3, "price_factor": 0.80},
}


class UserActions:
    """
    Functions for standard users to interact with the system
    (e.g. placing orders, running experiments).
    """

    @staticmethod
    def place_order(
        session: Session,
        user_id: int,
        article: ArticleEnum,
        acquisition_type: AcquisitionType,
    ) -> Order:
        """
        Allows a user to place an order for a cartridge or resource.

        This applies a cooldown and cost multiplier depending on acquisition type.

        Parameters
        ----------
        session : Session
            Active SQLAlchemy session.
        user_id : int
            The ID of the user placing the order.
        article : ArticleEnum
            The article to order (must match inventory field).
        acquisition_type : AcquisitionType
            Priority of acquisition (quick, standard, smart).

        Returns
        -------
        Order
            The created order record.
        """
        # Lookup user
        user = session.get(User, user_id)
        if not user:
            raise ValueError(f"User ID {user_id} not found.")

        # Lookup item catalog
        catalog_item = (
            session.query(ItemCatalog)
            .filter(ItemCatalog.item_key == article.value)
            .first()
        )
        if not catalog_item:
            raise ValueError(f"Article '{article.value}' not found in catalog.")

        # Apply acquisition rules
        rules = ACQUISITION_RULES[acquisition_type]
        cost = catalog_item.chuan_cost * rules["price_factor"]
        wait_weeks = rules["cooldown"]

        # Deduct credits from inventory (assuming single inventory row)
        inventory = session.query(Inventory).first()
        if not inventory:
            raise RuntimeError("Inventory not initialized.")

        if inventory.credits < cost:
            raise ValueError(
                f"Insufficient credits: {inventory.credits:.2f} available, need {cost:.2f}"
            )

        inventory.credits -= cost

        # Create order record
        order = Order(
            user_id=user_id,
            date=date.today(),
            time=datetime.now().time(),
            article=article,
            value=cost,
            wait_weeks=wait_weeks,
        )
        session.add(order)
        session.commit()
        return order
