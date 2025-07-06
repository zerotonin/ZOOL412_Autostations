# db/models/neurocartographer_experiment.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class NeuroCartographerExperiment(Base):
    """
    Stores Directed Circuit Trace jobs submitted to the PowerLab NeuroCartographer autostation.
    """

    __tablename__ = "neurocartographer_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)

    subject_count = Column(Integer, nullable=False)

    seed_neuron_locator = Column(Text, nullable=False)       # up to 100 words
    tracer_transport_type = Column(String, nullable=False)   # "Anterograde" or "Retrograde"
    max_neurons_to_map = Column(Integer, nullable=False)
    pathway_search_algorithm = Column(Text, nullable=False)  # up to 200 words

    cartridge_used = Column(String, nullable=True)           # e.g., "nc_pk1_cartridge"

    experiment = relationship("Experiment", backref="neurocartographer_details")
