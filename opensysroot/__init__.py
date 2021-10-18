import argparse
from pathlib import Path

from . import repo
from .database import Database
from .workenvironment import WorkEnvironment
from .enums.arch import Arch
from .enums.distro import Distro
from .enums.release import Release


def arg_info():
    parser = argparse.ArgumentParser(prog="opensysroot",
                                     description="Sysroot construction for compiling")
    parser.add_argument("distro", type=Distro, choices=list(Distro),
                        help="Distro Name of OS that sysroot is based on")
    parser.add_argument("arch", type=Arch, choices=list(Arch),
                        help="Architecture OS that sysroot is based on")
    parser.add_argument("release", type=Release, choices=list(Release),
                        help="Release name of OS")
    parser.add_argument("output", type=Path, default=Path("build"))
    parser.add_argument("--rename-tuple", type=str,
                        help="new name for sysroot tuple")
    parser.add_argument("--print-dest-sysroot",
                        default=False, action='store_true')
    return parser.parse_args()


def main():
    args = arg_info()

    repo_url = repo.get_repo_url(args.distro, args.arch)
    repo_packages_url = repo.get_repo_packages_url(
        args.distro, args.arch, args.release)

    env = WorkEnvironment(args.distro, args.arch, args.release,
                          args.output, args.print_dest_sysroot)

    db = Database(repo_packages_url)
    if args.distro == Distro.ROBORIO:
        assert args.arch is Arch.CORTEXA9
        db.add_package("gcc-dev")
        db.add_package("libc6-dev")
        db.add_package("libstdc++-dev")
        db.add_package("libatomic-dev")
        db.add_package("linux-libc-headers-dev")
    else:
        assert args.arch is not Arch.CORTEXA9
        db.add_package("build-essential")
        db.add_package("linux-libc-dev")
        db.add_package("libatomic1")

    db.post_resolve()
    db.download(repo_url, env.downloads)
    env.extract()
    env.clean()

    if args.rename_tuple is not None:
        env.rename_target(args.rename_tuple)