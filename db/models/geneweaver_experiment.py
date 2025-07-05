# db/models/geneweaver_experiment.py

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class GeneWeaverExperiment(Base):
    """
    Mode-specific table for GeneWeaver autostation experiments.
    Supports both:
    - Differential Gene Expression Analysis (DGE)
    - Viral Vector Gene Modification
    """

    __tablename__ = "geneweaver_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)

    # General Metadata
    mode = Column(String, nullable=False)  # "DGE" or "Viral"

    # DGE-specific
    fold_change_threshold = Column(Integer, nullable=True)
    max_sequences = Column(Integer, nullable=True)
    cell_type_level = Column(String, nullable=True)        # e.g., "bulk", "category", "subtype"
    cell_type_description = Column(String, nullable=True)  # e.g., "neurons", "marker_X cells"

    # Viral Vector-specific
    gene_of_interest = Column(Text, nullable=True)         # up to 200 words
    promoter_sequence = Column(Text, nullable=True)        # up to 100 words
    transduction_level = Column(String, nullable=True)     # "bulk", "category", "subtype"
    transduction_description = Column(String, nullable=True)

    # Cartridge tracking
    cartridge_used = Column(String, nullable=True)


    experiment = relationship("Experiment", backref="geneweaver_details")
