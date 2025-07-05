# db/models/geneweaver_group.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class GeneWeaverGroup(Base):
    """
    A group of subjects for a GeneWeaver experiment, including name, size,
    and optionally instructions or modification type depending on the mode.
    """

    __tablename__ = "geneweaver_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    geneweaver_experiment_id = Column(Integer, ForeignKey("geneweaver_experiments.id"), nullable=False)

    group_name = Column(String, nullable=False)
    subject_count = Column(Integer, nullable=False)
    sampling_instructions = Column(Text, nullable=True)  # for DGE
    modification_type = Column(String, nullable=True)    # for Viral mode only

    geneweaver_experiment = relationship("GeneWeaverExperiment", backref="groups")
