# db/models/acquisition.py

from enum import Enum


class AcquisitionType(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    SMART = "smart"
