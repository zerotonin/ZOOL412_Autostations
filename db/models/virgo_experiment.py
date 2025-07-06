# db/models/virgo_experiment.py

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class VirgoExperiment(Base):
    """
    Stores jobs submitted to the Virgo Flow Reactor autostation.
    Supports:
    - Compound Analysis (new sample or existing structure)
    - Synthesize Compound (known or novel)
    """

    __tablename__ = "virgo_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)

    mode = Column(String, nullable=False)  # "analysis" or "synthesis"

    # Compound Analysis fields
    sample_source_description = Column(Text, nullable=True)  # Only if new sample
    analysis_reference_name = Column(String, nullable=True)
    request_theta_analysis = Column(Boolean, default=False)

    # Synthesis fields
    target_compound_identifier = Column(String, nullable=True)  # Known ID or name
    desired_functional_effect = Column(Text, nullable=True)     # If designing novel compound

    # Resource tracking
    shifts_used = Column(Integer, nullable=False, default=0)
    compute_cost = Column(Integer, nullable=False, default=0)
    cartridge_used = Column(String, nullable=True)  # DuPont if synthesis

    experiment = relationship("Experiment", backref="virgo_details")
