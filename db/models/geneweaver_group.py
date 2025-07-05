# db/models/geneweaver_group.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class GeneWeaverGroup(Base):
    """
    Linked table for experimental groups in GeneWeaver experiments.
    Handles both DGE and Viral modes.
    """

    __tablename__ = "geneweaver_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    geneweaver_experiment_id = Column(Integer, ForeignKey("geneweaver_experiments.id"), nullable=False)

    group_name = Column(String, nullable=False)
    subject_ids = Column(Text, nullable=False)  # Raw string of subject IDs
    sampling_instructions = Column(Text, nullable=True)  # DGE mode
    modification_type = Column(String, nullable=True)    # Viral mode only: Addition, Knockout, etc.

    geneweaver_experiment = relationship("GeneWeaverExperiment", backref="groups")
