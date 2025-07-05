# db/admin_actions.py

from sqlalchemy.orm import Session
from db.models.inventory import Inventory
from db.models.user import User
from db.models.order import Order
from db.models.item_catalog import ItemCatalog
from db.models.order import ArticleEnum


class AdminActions:
    """
    Admin-level actions for database setup and control in the ZOOL412_Autostations project.
    """

    @staticmethod
    def initialize_inventory(session: Session) -> Inventory:
        """
        Create the starting inventory entry in the database.

        The game starts with:
        - 2,000,000 credits
        - 120 shifts for each TA
        - 3 juices
        - 40 of 51U6 animals available and max
        - All other animals at -1 (unavailable)
        - 1 of each cartridge

        Parameters
        ----------
        session : Session
            Active SQLAlchemy session.

        Returns
        -------
        Inventory
            The created inventory record.
        """
        inventory = Inventory(
            credits                    = 2_000_000.0,
            ta_saltos_shifts           = 30,
            ta_nitro_shifts            = 30,
            ta_helene_shifts           = 30,
            ta_carnival_shifts         = 30,
            ta_saltos_shifts_max       = 30,
            ta_nitro_shifts_max        = 30,
            ta_helene_shifts_max       = 30,
            ta_carnival_shifts_max     = 30,
            ta_saltos_risk             = 0,
            ta_nitro_risk              = 0,
            ta_helene_risk             = 0,
            ta_carnival_risk           = 0,
            juice                      = 3,
            animals_51u6_max           = 40,
            animals_51u6_available     = 40,
            animals_51u6_m_max         = -1,
            animals_51u6_m_available   = -1,
            animals_c248_s_max         = -1,
            animals_c248_s_available   = -1,
            animals_c248_b_max         = -1,
            animals_c248_b_available   = -1,
            xatty_cartridge            = 1,
            zeropoint_cartridge        = 1,
            nc_pk1_cartridge           = 1,
            smart_filament_s_cartridge = 1,
            smart_filament_m_cartridge = 1,
            smart_filament_l_cartridge = 1,
            mamr_reel_cartrdige        = 1,
            dupont_cartridge           = 1,
        )
        session.add(inventory)
        session.commit()
        return inventory

    @staticmethod
    def create_test_users(session: Session) -> list[User]:
        """
        Add four test users to the database for testing purposes.

        All users are assigned to the team 'Psi-Nestor' and include 
        a mix of English and Māori names for diversity.

        Parameters
        ----------
        session : Session
            Active SQLAlchemy session.

        Returns
        -------
        list[User]
            List of created user records.
        """
        users = [
            User(first_name="Aroha", last_name="Ngata", team="Psi-Nestor"),
            User(first_name="James", last_name="Wellington", team="Psi-Nestor"),
            User(first_name="Mereana", last_name="Te Rangi", team="Psi-Nestor"),
            User(first_name="Thomas", last_name="Whakataka", team="Psi-Nestor"),
        ]
        session.add_all(users)
        session.commit()
        return users



    @staticmethod
    def initialize_item_catalog(session: Session) -> None:
        """
        Populate the ItemCatalog with known cartridges and consumables.
        Will not duplicate existing entries.
        """
        existing_keys = {
            item.item_key
            for item in session.query(ItemCatalog.item_key).all()
        }

        catalog_items = [
            ItemCatalog(item_key=ArticleEnum.XATTY_CARTRIDGE, display_name="XATTY Cartridge", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.ZEROPOINT_CARTRIDGE, display_name="ZeroPoint Cartridge", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.NC_PK1_CARTRIDGE, display_name="NC-PK1 Cartridge", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.SMART_FILAMENT_S_CARTRIDGE, display_name="Smart Filament S", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.SMART_FILAMENT_M_CARTRIDGE, display_name="Smart Filament M", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.SMART_FILAMENT_L_CARTRIDGE, display_name="Smart Filament L", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.MAMR_REEL_CARTRDIGE, display_name="MAMR Reel Cartridge", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.DUPONT_CARTRIDGE, display_name="DuPont Cartridge", chuan_cost=70000, wait_weeks=1),
            ItemCatalog(item_key=ArticleEnum.JUICE, display_name="Juice Pack", chuan_cost=10000, wait_weeks=0),

        ]

        # Add only if item_key is not already present
        new_items = [item for item in catalog_items if item.item_key not in existing_keys]

        if new_items:
            session.add_all(new_items)
            session.commit()

    @staticmethod
    def advance_one_week(session: Session) -> None:
        """
        Advance simulation one week.
        - Resets TA shifts to 30.
        - Resets animal availability to current max.
        - Decrements wait times.
        - Applies orders and events.
        - Updates TA max shifts (if juiced).
        - Updates animal max to match new availability.
        """
        print("[⏳] Advancing simulation...")

        inventory = session.query(Inventory).first()
        if not inventory:
            raise RuntimeError("Inventory not initialized.")

        # STEP 1: Reset TA shifts to 30 (regardless of previous max)
        for field in [
            "ta_saltos_shifts",
            "ta_nitro_shifts",
            "ta_helene_shifts",
            "ta_carnival_shifts",
        ]:
            setattr(inventory, field, 30)

        # STEP 2: Reset animal availability to current max
        for species in [
            "animals_51u6",
            "animals_51u6_m",
            "animals_c248_s",
            "animals_c248_b",
        ]:
            max_val = getattr(inventory, f"{species}_max")
            setattr(inventory, f"{species}_available", max_val)

        # STEP 3: Fetch and apply scheduled events
        orders = session.query(Order).filter(Order.wait_weeks >= 0).all()

        for order in orders:
            order.wait_weeks -= 1

            if order.wait_weeks == 0:
                if order.is_effect:
                    AdminActions._apply_event_effect(order, inventory)
                else:
                    AdminActions._apply_order_effect(order, inventory)

        # STEP 4: After events, update TA max shifts to match actual values
        for ta in ["ta_saltos", "ta_nitro", "ta_helene", "ta_carnival"]:
            shifts = getattr(inventory, f"{ta}_shifts")
            setattr(inventory, f"{ta}_shifts_max", shifts)

        # STEP 5: After events, update animal max counts to reflect post-event availability
        for species in [
            "animals_51u6",
            "animals_51u6_m",
            "animals_c248_s",
            "animals_c248_b",
        ]:
            available = getattr(inventory, f"{species}_available")
            setattr(inventory, f"{species}_max", available)

        session.commit()
        print("[✔] Week advanced.\n")

    @staticmethod
    def _apply_order_effect(order: Order, inventory: Inventory) -> None:
        """Handles completed resource acquisitions."""
        field = order.article
        if hasattr(inventory, field):
            current = getattr(inventory, field)
            setattr(inventory, field, current + 1)
            print(f"[Inventory] +1 {field} → {current + 1}")
        else:
            print(f"[Warning] Inventory field '{field}' not found.")

    @staticmethod
    def _apply_event_effect(order: Order, inventory: Inventory) -> None:
        """
        Dispatches to the correct handler based on event type.
        """
        if order.event_type == "juiz":
            AdminActions._handle_juiz_event(order, inventory)
        elif order.event_type == "hunt":
            AdminActions._handle_hunting_event(order, inventory)
        else:
            print(f"[Warning] Unknown event type: {order.event_type}")
            
    @staticmethod
    def _handle_juiz_event(order: Order, inventory: Inventory) -> None:
        """
        Reduces TA shift capacity due to post-Juiz fatigue.
        """
        field = order.inventory_field
        if not field or not hasattr(inventory, field):
            print(f"[Warning] Invalid TA field for Juiz effect: {field}")
            return

        max_field = field.replace("_shifts", "_shifts_max")
        current_max = getattr(inventory, max_field, 30)
        new_shifts = round(current_max * 0.3)

        setattr(inventory, field, new_shifts)
        print(f"[Juiz Effect] {field} reduced to {new_shifts} (from max {current_max})")

    @staticmethod
    def _handle_hunting_event(order: Order, inventory: Inventory) -> None:
        """
        Adds collected animals to inventory at delivery time.
        """
        field = order.inventory_field
        current = getattr(inventory, field, 0)
        setattr(inventory, field, current + int(order.value))
        print(f"[HUNT DELIVERY] +{int(order.value)} → {field}")
