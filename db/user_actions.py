# db/user_actions.py
import random
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
            is_effect=False,
        )
        session.add(order)
        session.commit()
        return order

    
    @staticmethod
    def administer_juiz(session: Session, ta_field: str, user_id: int) -> Order:
        """
        Administer Busy Bee Juiz™ to a TA.

        Ensures inventory juice is available, applies boost or death logic,
        updates persistent death risk, and logs the order.

        Parameters
        ----------
        session : Session
            SQLAlchemy session.
        ta_field : str
            Field name in Inventory for the TA's shifts (e.g. 'ta_saltos_shifts').
        user_id : int
            ID of user applying the juice.

        Returns
        -------
        Order
            Log entry for the juicing action.
        """
        inventory = session.query(Inventory).first()
        if inventory is None:
            raise RuntimeError("Inventory not initialized.")

        # STEP 1: Check juice availability
        if inventory.juice < 1:
            raise ValueError("No Juice available in inventory.")

        # STEP 2: Check TA eligibility (must be juicable)
        current_shifts = getattr(inventory, ta_field)
        if not (0 < current_shifts <=30):
            raise ValueError(f"TA '{ta_field}' cannot be juiced at {current_shifts:.2f} shifts.")

        # STEP 3: Determine death risk field and value
        risk_field = ta_field.replace("_shifts", "_risk")
        current_risk = getattr(inventory, risk_field, 0.0)

        # STEP 4: Roll the 100-sided dice
        dice = random.randint(1, 100)
        print(f"[Juice Attempt] {ta_field} | Risk: {current_risk:.0f}% | Roll: {dice}")

        if current_risk == 0.0 or dice > current_risk:
            # Survives: Boost output and raise risk
            boosted_shifts = round(current_shifts * 1.8)
            setattr(inventory, ta_field, boosted_shifts)
            setattr(inventory, risk_field, min(current_risk + 10.0, 100.0))
            print(f"[Boost] TA '{ta_field}' now has {boosted_shifts} shifts. Risk increased.")
        else:
            # Fatality
            setattr(inventory, ta_field, 0)
            print(f"[Fatality] TA '{ta_field}' has died. Shifts set to 0.")

        # STEP 5: Deduct juice
        inventory.juice -= 1

        # STEP 6: Log juice action (not purchase)
        article_name = f"juiced_{ta_field}"

        order = Order(
            user_id=user_id,
            date=date.today(),
            time=datetime.now().time(),
            article="JUICE",
            inventory_field=ta_field,  # new field added here
            value=0.0,              # not a purchase
            wait_weeks=1,
            is_effect=True,
        )
        session.add(order)
        session.commit()
        return order

