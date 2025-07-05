# db/models/intraspectra_experiment.py

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class IntraspectraExperiment(Base):
    """
    Stores experimental jobs for the EOS D4 Intraspectra Iris Mark II autostation.

    Supports:
    - Visual Data Acquisition
    - Resonance Tomography
    """

    __tablename__ = "intraspectra_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)

    # Common
    mode = Column(String, nullable=False)  # "visual" or "rt"
    subject_count = Column(Integer, nullable=False)
    region_of_interest = Column(Text, nullable=False)

    # Visual Data Acquisition
    imaging_technique = Column(String, nullable=True)     # "Camera_Imaging", "LiDAR_Scan", "Microscopy"
    capture_type = Column(String, nullable=True)          # "Single_Frame", "Time_Series"
    spectral_filter = Column(String, nullable=True)       # "Visible_Light", "Infrared_Thermal", "Ultraviolet"
    frame_capture_rate = Column(Float, nullable=True)     # Hz
    microscopy_technique = Column(String, nullable=True)  # "BrightField", "PhaseContrast", "Fluorescence"
    magnification_level = Column(String, nullable=True)   # "10x", "40x", "100x"

    # Resonance Tomography
    target_substance = Column(String, nullable=True)      # "Water", "Lipids", etc.
    target_is_custom = Column(Boolean, default=False)
    volume_capture_type = Column(String, nullable=True)   # "Static_Volume", "Dynamic_Volume_Series"
    number_of_volumes = Column(Integer, nullable=True)
    volume_capture_rate = Column(Float, nullable=True)    # Hz

    cartridge_used = Column(String, nullable=True)        # e.g., "zeropoint_cartridge"

    experiment = relationship("Experiment", backref="intraspectra_details")
