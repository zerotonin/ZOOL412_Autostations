# db/models/experiments.py

from sqlalchemy import Column, Integer, String, Date, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class Experiment(Base):
    """
    Base metadata table for all user-submitted experimental jobs.

    This is the top-level dispatcher table that links to autostation-specific detail tables.
    """

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.key"), nullable=False)
    autostation_name = Column(String, nullable=False)    # e.g. 'GeneWeaver', 'Virgo Reactor'
    experiment_type = Column(String, nullable=False)     # e.g. 'DGE Analysis', 'Synthesis'
    subject_species = Column(String, nullable=False)  # e.g., '51u6_m'

    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    wait_weeks = Column(Integer, default=0)

    is_complete = Column(Boolean, default=False)
    is_failed = Column(Boolean, default=False)
    result_summary = Column(String, nullable=True)

    user = relationship("User", backref="experiments")

    # We'll define relationships from each autostation-specific table pointing back here
