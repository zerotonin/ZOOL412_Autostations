# db/models/panopticam_experiment.py

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class PanopticamExperiment(Base):
    """
    Master experiment table for KPI Panopticam behavioral monitoring sessions.

    
    Experiment
    └── PanopticamExperiment
        ├── PanopticamGroup
        ├── PanopticamEvent
        ├── PanopticamPhase
            └── PanopticamContingency

    """

    __tablename__ = "panopticam_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)

    experiment_run_id = Column(String, nullable=False)  # unique ID per session
    probe_type_used = Column(String, default="None")     # Temp, Pressure, pH, etc.

    base_shift_cost = Column(Float, nullable=False)
    total_subjects = Column(Integer, nullable=False)
    total_monitoring_hours = Column(Float, nullable=False)

    cartridge_used = Column(String, nullable=True)

    experiment = relationship("Experiment", backref="panopticam_details")


class PanopticamGroup(Base):
    __tablename__ = "panopticam_groups"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("panopticam_experiments.id"), nullable=False)

    group_name = Column(String, nullable=False)
    subject_count = Column(Integer, nullable=False)

    experiment = relationship("PanopticamExperiment", backref="groups")


class PanopticamEvent(Base):
    __tablename__ = "panopticam_events"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("panopticam_experiments.id"), nullable=False)

    event_name = Column(String, nullable=False)
    definition_type = Column(String, nullable=False)  # Natural, ResponseCharacterization
    quantification_method = Column(String, nullable=False)  # Duration, Frequency, etc.
    operational_definition = Column(Text, nullable=False)

    experiment = relationship("PanopticamExperiment", backref="events")


class PanopticamPhase(Base):
    __tablename__ = "panopticam_phases"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("panopticam_experiments.id"), nullable=False)

    phase_name = Column(String, nullable=False)
    phase_duration = Column(String, nullable=False)  # store as string: "60 minutes", "100 trials"
    monitor_events_active = Column(Text, nullable=True)  # comma-separated list of event names

    experiment = relationship("PanopticamExperiment", backref="phases")


class PanopticamContingency(Base):
    __tablename__ = "panopticam_contingencies"

    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey("panopticam_phases.id"), nullable=False)

    trigger_event_name = Column(String, nullable=False)
    applicable_groups = Column(Text, nullable=True)  # comma-separated
    action_command = Column(Text, nullable=False)

    phase = relationship("PanopticamPhase", backref="contingencies")
