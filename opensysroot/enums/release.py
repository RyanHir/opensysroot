from enum import Enum


class Release(Enum):
    # Debian/Raspbian
    BUSTER = "buster"
    BULLSEYE = "bullseye"
    
    # Ubuntu
    BIONIC = "bionic"
    FOCAL = "focal"

    # Misc
    ROBORIO = "roborio"

    def __str__(self):
        return self.value
