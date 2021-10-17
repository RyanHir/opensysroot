import os
import re
import shutil
import subprocess
from pathlib import Path
from .enums.arch import Arch
from .enums.distro import Distro
from .enums.release import Release

TO_DELETE = [
    "etc",
    "sbin",
    "usr/bin",
    "usr/share",
    "usr/lib/bfd-plugins",
    "usr/lib/gcc",
]

class WorkEnvironment:
    base: Path
    sysroot: Path
    downloads: Path

    def __init__(self, distro: Distro, arch: Arch, release: Release, workdir: Path, print_dest_sysroot: bool):
        self.arch = arch
        self.distro = distro
        self.base = Path(workdir, str(distro), str(release), str(arch))
        self.sysroot = Path(self.base, "sysroot")
        self.downloads = Path(self.base, "downloads")

        if print_dest_sysroot:
            print(self.sysroot.resolve())
            exit(0)

        if self.sysroot.exists():
            shutil.rmtree(self.sysroot)

        self.sysroot.mkdir(parents=True, exist_ok=True)
        self.downloads.mkdir(parents=True, exist_ok=True)

    def extract(self):
        for file in self.downloads.iterdir():
            subprocess.call(["dpkg", "-x", str(file), str(self.sysroot)])

    def clean(self):
        self._symlink()
        self._delete()

    def _delete(self):
        _tuple = self.get_orig_tuple()
        for subpath in TO_DELETE:
            xdir = Path(self.sysroot, subpath.format(tuple=_tuple))
            if xdir.exists():
                shutil.rmtree(xdir)

    def _symlink(self):
        for file in self.sysroot.glob("**/*"):
            if not file.is_symlink():
                continue
            resolved = Path(os.readlink(file))
            if resolved.is_absolute():
                resolved = Path("{}/{}".format(self.sysroot, resolved))
            elif file.is_file():
                resolved = Path(
                    "{}/{}".format(file.parent.absolute(), resolved))
            resolved = resolved.resolve()
            file.unlink()
            if resolved.exists():
                shutil.copy2(resolved, file)

    def get_orig_tuple(self):
        if self.distro is Distro.ROBORIO:
            assert self.arch is Arch.CORTEXA9
            return "arm-nilrt-linux-gnueabi"
        else:
            if self.arch is Arch.ARMHF:
                return "arm-linux-gnueabihf"
            if self.arch is Arch.ARM64:
                return "aarch64-linux-gnu"
            if self.arch is Arch.AMD64:
                return "x86_64-linux-gnu"
            raise RuntimeError("Unknown System")

    def rename_target(self, newname: str):
        oldname = self.get_orig_tuple()
        for file in self.sysroot.glob("**/*"):
            if not file.is_file():
                continue
            msg = subprocess.Popen(
                ["file", str(file.resolve())], stdout=subprocess.PIPE).communicate()[0]
            if re.search("text", msg.decode("utf8")) == None:
                continue
            with file.open("r+") as fd:
                data = fd.read()
                data = data.replace(oldname, newname)
                fd.write(data)
        for subpath in self.sysroot.glob("**/*"):
            if not subpath.is_dir():
                continue
            if subpath.stem != oldname:
                continue
            new = Path(subpath.parent, newname)
            if subpath.exists():
                shutil.move(subpath, new)
