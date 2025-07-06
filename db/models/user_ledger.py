
# db/models/user_ledger.py

from sqlalchemy import Column, Integer, String, Float, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class UserLedger(Base):
    """
    Records all actions that incur cost, use resources, or create inventory entries.
    Acts as a general ledger (Kassenbuch).
    """

    __tablename__ = "user_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.key"), nullable=False)
    action_type = Column(String, nullable=False)  # e.g. 'Order', 'Experiment', 'SupplyDrop'
    action_label = Column(String, nullable=True)  # optional: short name or ref

    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)

    cost_chuan = Column(Float, nullable=False, default=0.0)
    cartridge_used = Column(String, nullable=True)  # Enum name or string

    user = relationship("User", backref="ledger_entries")
