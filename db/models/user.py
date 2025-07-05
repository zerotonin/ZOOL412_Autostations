# db/models/user.py

from sqlalchemy import Column, Integer, String
from db.base import Base


class User(Base):
    """
    Represents users who can place orders.

    NOTE: This table is a simplified toy model version intended only for use
    in development and testing of the ZOOL412_Autostations database backend.

    In actual production (i.e., the deployed homepage system), user management
    will likely be handled via a separate authentication and identity system.

    JavaScript developers should treat this table as a placeholder or mock,
    and refer to the final production user schema when integrating.
    """


    __tablename__ = "users"

    key = Column(Integer, primary_key=True, autoincrement=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    team = Column(String, nullable=True)
