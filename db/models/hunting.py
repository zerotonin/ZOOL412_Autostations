# db/models/hunting.py

from enum import Enum


class AnimalSpecies(str, Enum):
    U51 = "animals_51u6"
    U51_M = "animals_51u6_m"
    C248_S = "animals_c248_s"
    C248_B = "animals_c248_b"
