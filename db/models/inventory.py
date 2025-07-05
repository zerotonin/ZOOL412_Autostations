# db/models/inventory.py

from sqlalchemy import Column, Integer, Float
from db.base import Base


class Inventory(Base):
    """
    SQLAlchemy model for the 'inventory' table in the ZOOL412_Autostations project.

    This table tracks money, equipment, animals, shifts, and consumables.
    """

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)

    #Money in Chuan
    credits = Column(Float)

    # Technical assistance shifts
    ta_saltos_shifts = Column(Integer)
    ta_nitro_shifts = Column(Integer)
    ta_helene_shifts = Column(Integer)
    ta_carnival_shifts = Column(Integer)
    # Technical assistance shifts booster
    juice = Column(Integer)

    # Animals Maximal
    animals_51u6_max = Column(Integer)
    animals_51u6_m_max = Column(Integer)
    animals_c248_s_max = Column(Integer)
    animals_c248_l_max = Column(Integer)
    # Animals that are currently available
    animals_51u6_available = Column(Integer)
    animals_51u6_m_available = Column(Integer)
    animals_c248_s_available = Column(Integer)
    animals_c248_l_available = Column(Integer)

    # Equipment
    xatty_cartridge = Column(Integer)
    zeropoint_cartridge = Column(Integer)
    nc_pk1_cartridge = Column(Integer)
    smart_filament_s_cartridge = Column(Integer)
    smart_filament_m_cartridge = Column(Integer)
    smart_filament_l_cartridge = Column(Integer)
    mamr_reel_cartrdige = Column(Integer)
    dupont_cartridge = Column(Integer)
