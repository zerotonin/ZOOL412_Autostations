# db/models/order.py

from sqlalchemy import Column, Integer, Float, Date, Time, ForeignKey, String, Boolean
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import relationship
from db.base import Base
from enum import Enum


class ArticleEnum(str, Enum):
    XATTY_CARTRIDGE = "xatty_cartridge"
    ZEROPOINT_CARTRIDGE = "zeropoint_cartridge"
    NC_PK1_CARTRIDGE = "nc_pk1_cartridge"
    SMART_FILAMENT_S_CARTRIDGE = "smart_filament_s_cartridge"
    SMART_FILAMENT_M_CARTRIDGE = "smart_filament_m_cartridge"
    SMART_FILAMENT_L_CARTRIDGE = "smart_filament_l_cartridge"
    MAMR_REEL_CARTRDIGE = "mamr_reel_cartrdige"
    DUPONT_CARTRIDGE = "dupont_cartridge"
    JUICE = "juice"

class Order(Base):
    """Stores order records linked to a user and affecting inventory."""

    __tablename__ = "orders"

    key = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.key"), nullable=False)

    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    article = Column(SqlEnum(ArticleEnum), nullable=False)  # Will refer to a known inventory field name
    value = Column(Float, nullable=False)
    wait_weeks = Column(Integer, default=0)

    is_effect = Column(Boolean, default=False) 

    # Optional target inventory field name (e.g. 'ta_saltos_shifts')
    inventory_field = Column(String, nullable=True)
    event_type = Column(String, nullable=True) 

    user = relationship("User", backref="orders")
