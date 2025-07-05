# db/user_actions.py
import random
from datetime import date, datetime
from sqlalchemy.orm import Session
from db.models.user import User
from db.models.order import Order, ArticleEnum
from db.models.item_catalog import ItemCatalog
from db.models.inventory import Inventory
from db.models.acquisition import AcquisitionType
from db.models.hunting import AnimalSpecies


ACQUISITION_RULES = {
    AcquisitionType.QUICK: {"cooldown": 1, "price_factor": 2.00},
    AcquisitionType.STANDARD: {"cooldown": 2, "price_factor": 1.00},
    AcquisitionType.SMART: {"cooldown": 3, "price_factor": 0.80},
}

# Inside user_actions.py or hunting.py
HUNTING_RULES = {
    AnimalSpecies.U51: {"cooldown": 0, "method": "gaussian"},
    AnimalSpecies.U51_M: {"cooldown": 1, "method": "gaussian"},
    AnimalSpecies.C248_S: {"cooldown": 1, "method": "colony"},
    AnimalSpecies.C248_B: {"cooldown": 0, "method": "uniform"},
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
        # Get TA field info
        shifts_field = ta_field
        max_field = ta_field.replace("_shifts", "_shifts_max")
        risk_field = ta_field.replace("_shifts", "_risk")

        current_shifts = getattr(inventory, shifts_field)
        current_max = getattr(inventory, max_field)
        current_risk = getattr(inventory, risk_field)
        if not (0 < current_max <=30):
            raise ValueError(f"TA '{ta_field}' cannot be juiced at {current_shifts:.2f} shifts.")

        # STEP 3: Determine death risk field and value
        current_risk = getattr(inventory, risk_field, 0.0)

        # STEP 4: Roll the 100-sided dice
        dice = random.randint(1, 100)
        print(f"[Juice Attempt] {ta_field} | Risk: {current_risk:.0f}% | Roll: {dice}")

        if current_risk == 0.0 or dice > current_risk:
            # Survives: Boost output and raise risk
            # Calculate new max shifts and offset
            new_max = round(current_max * 1.8)
            offset = new_max - current_max
            
            # Apply to max and available
            setattr(inventory, max_field, new_max)
            setattr(inventory, shifts_field, current_shifts + offset)
            setattr(inventory, risk_field, min(current_risk + 10.0, 100.0))

            print(
                f"[Boost] {ta_field} max increased to {new_max}, "
                f"shifts += {offset} → {current_shifts + offset}, "
                f"risk is now {current_risk + 10:.0f}%"
            )
        else:
            # Fatality
            setattr(inventory, max_field, 0)
            setattr(inventory, shifts_field, 0)
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
            inventory_field=ta_field,  # effect field
            event_type = "juiz", # event type for tracking
            value=0.0,              # not a purchase
            wait_weeks=1,
            is_effect=True,
        )
        session.add(order)
        session.commit()
        return order

    @staticmethod
    def collect_animals(user_id: int, species: AnimalSpecies, session: Session) -> None:
        """
        Attempts to collect animals if enough TA shifts are available.
        Deducts 12 shifts, calculates success, and either adds animals to inventory
        or schedules a future delivery.
        """
        inventory = session.query(Inventory).first()
        if not inventory:
            raise RuntimeError("Inventory not initialized.")

        # Total available shifts
        ta_fields = [
            "ta_saltos_shifts",
            "ta_nitro_shifts",
            "ta_helene_shifts",
            "ta_carnival_shifts",
        ]
        total_shifts = sum(getattr(inventory, f) for f in ta_fields)

        if total_shifts < 12:
            print(f"[ERROR] Not enough TA shifts available (have {total_shifts}, need 12)")
            return

        # Deduct 12 shifts (greedy)
        shifts_to_deduct = 12
        for f in ta_fields:
            current = getattr(inventory, f)
            used = min(current, shifts_to_deduct)
            setattr(inventory, f, current - used)
            shifts_to_deduct -= used
            if shifts_to_deduct == 0:
                break

        # Determine collection success
        rule = HUNTING_RULES[species]
        method = rule["method"]
        cooldown = rule["cooldown"]

        if method == "gaussian":
            amount = round(random.gauss(mu=12, sigma=5))
            amount = max(3, min(amount, 30))
        elif method == "colony":
            amount = 12 if random.random() < 0.33 else 0
        elif method == "uniform":
            amount = random.randint(0, 3)
        else:
            raise ValueError(f"Unknown collection method for {species}")

        if amount == 0:
            print(f"[HUNT] Attempted {species.value}, but collected nothing.")
            return

        if cooldown == 0:
            current_count = getattr(inventory, f"{species.value}_available", 0)
            current_max = getattr(inventory, f"{species.value}_max", 0)
            setattr(inventory, f"{species.value}_available", current_count + amount)
            setattr(inventory, f"{species.value}_max", current_max + amount)
            print(f"[HUNT] Collected {amount} {species.name}, added directly to inventory.")
        else:
            # Create scheduled order to deliver later
            order = Order(
                user_id=user_id,
                date=date.today(),
                time=datetime.now().time(),
                article=species.value,
                value=amount,
                wait_weeks=cooldown,
                is_effect=True,
                event_type="hunt",
                inventory_field=f"{species.value}_available",
            )
            session.add(order)
            print(f"[HUNT] Scheduled {amount} {species.name} in {cooldown} week(s).")

        session.commit()