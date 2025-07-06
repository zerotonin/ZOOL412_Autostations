# db/models/polykiln_experiment.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class PolykilnExperiment(Base):
    """
    Stores fabrication jobs submitted to the SF950-LM Polykiln Catalytic Volume Printer.
    """

    __tablename__ = "polykiln_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)

    object_name = Column(String, nullable=False, unique=True)
    functional_description = Column(Text, nullable=False)

    size_tier = Column(String, nullable=False)  # "S", "M", "L"
    mechanical_tier = Column(Integer, nullable=False)  # 0-3
    electronic_tier = Column(Integer, nullable=False)  # 0-3

    score = Column(Integer, nullable=False)  # size*2 + mech + elec
    filament_type_used = Column(String, nullable=False)  # S/M/L Cartridge
    cartridge_used = Column(String, nullable=False)  # Enum value from ArticleEnum

    shift_cost = Column(Integer, nullable=False)
    ocs_compute_cost = Column(Integer, nullable=False)

    experiment = relationship("Experiment", backref="polykiln_details")
