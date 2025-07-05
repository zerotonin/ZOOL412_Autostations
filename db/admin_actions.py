# db/admin_actions.py

from sqlalchemy.orm import Session
from db.models.inventory import Inventory
from db.models.user import User


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
            credits=2_000_000.0,
            ta_saltos_shifts=120,
            ta_nitro_shifts=120,
            ta_helene_shifts=120,
            ta_carnival_shifts=120,
            juice=3,
            animals_51u6_max=40,
            animals_51u6_available=40,
            animals_51u6_m_max=-1,
            animals_51u6_m_available=-1,
            animals_c248_s_max=-1,
            animals_c248_s_available=-1,
            animals_c248_l_max=-1,
            animals_c248_l_available=-1,
            xatty_cartridge=1,
            zeropoint_cartridge=1,
            nc_pk1_cartridge=1,
            smart_filament_s_cartridge=1,
            smart_filament_m_cartridge=1,
            smart_filament_l_cartridge=1,
            mamr_reel_cartrdige=1,
            dupont_cartridge=1,
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