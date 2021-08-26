from .enums.distro import Distro

REPOS = {
    Distro.DEBIAN: "http://ftp.debian.org/debian/",
    Distro.RASPBIAN: "http://archive.raspbian.org/raspbian",
    Distro.ROBORIO: "http://download.ni.com/ni-linux-rt/feeds/2019/arm/cortexa9-vfpv3/",
    Distro.UBUNTU: {"port": "http://ports.ubuntu.com/ubuntu-ports/",
                    "archive": "http://archive.ubuntu.com/ubuntu/"}
}
