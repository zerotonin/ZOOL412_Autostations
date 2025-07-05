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

    # Technical assistance shifts available
    ta_saltos_shifts = Column(Integer,default=30)
    ta_nitro_shifts = Column(Integer,default=30)
    ta_helene_shifts = Column(Integer,default=30)
    ta_carnival_shifts = Column(Integer,default=30)
    # Technical assistance shifts available
    ta_saltos_shifts_max = Column(Integer,default=30)
    ta_nitro_shifts_max = Column(Integer,default=30)
    ta_helene_shifts_max = Column(Integer,default=30)
    ta_carnival_shifts_max = Column(Integer,default=30)
    # Technical assistance death risk
    ta_saltos_risk = Column(Float, default=0.0)
    ta_nitro_risk = Column(Float, default=0.0)
    ta_helene_risk = Column(Float, default=0.0)
    ta_carnival_risk = Column(Float, default=0.0)
    # Technical assistance shifts booster
    juice = Column(Integer)

    # Animals Maximal
    animals_51u6_max = Column(Integer)
    animals_51u6_m_max = Column(Integer)
    animals_c248_s_max = Column(Integer)
    animals_c248_b_max = Column(Integer)
    # Animals that are currently available
    animals_51u6_available = Column(Integer)
    animals_51u6_m_available = Column(Integer)
    animals_c248_s_available = Column(Integer)
    animals_c248_b_available = Column(Integer)

    # Equipment
    xatty_cartridge = Column(Integer)
    zeropoint_cartridge = Column(Integer)
    nc_pk1_cartridge = Column(Integer)
    smart_filament_s_cartridge = Column(Integer)
    smart_filament_m_cartridge = Column(Integer)
    smart_filament_l_cartridge = Column(Integer)
    mamr_reel_cartrdige = Column(Integer)
    dupont_cartridge = Column(Integer)
