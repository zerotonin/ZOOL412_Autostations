# db/models/item_catalog.py

from sqlalchemy import Column, Integer, String, Float
from db.base import Base


class ItemCatalog(Base):
    """
    Catalog of items that can be ordered.

    Includes cost (in chuan) and delivery wait time (in weeks).
    """

    __tablename__ = "item_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_key = Column(String, unique=True, nullable=False)  # Match ArticleEnum names
    display_name = Column(String, nullable=False)  # For UI
    chuan_cost = Column(Float, nullable=False)
    wait_weeks = Column(Integer, default=0)
