import io
from pathlib import Path
import re
import gzip
import sqlite3
import requests

PACKAGE_VERSION_REGEX = re.compile(r'(\S+) \((\S+) (\S+)\)')


class Database:
    con: sqlite3.Connection
    cur: sqlite3.Cursor
    PACKAGES_TO_INSTALL: dict
    DEPENDENCIES_TO_RESOLVE: list

    def __init__(self, package_url) -> None:
        self.PACKAGES_TO_INSTALL = dict()
        self.DEPENDENCIES_TO_RESOLVE = list()
        self.con = sqlite3.connect(":memory:")
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE Packages(ID integer primary key autoincrement, "
                         "Name, Version, Filename, Dependencies)")
        data = requests.get(package_url)
        assert data.status_code == 200, package_url
        data = gzip.decompress(data.content)
        data = io.StringIO(data.strip().decode("utf8"))
        line = data.readline().strip()
        while line:
            if line.startswith("Package:"):
                pkg_name = line[9:].strip()

                # predefine as it is optional
                pkg_dep = None
                while line:
                    if line.startswith('Version:'):
                        pkg_ver = line[9:].strip()
                    elif line.startswith('Depends:'):
                        pkg_dep = line[9:].strip()
                    elif line.startswith('Filename:'):
                        pkg_path = line[10:].strip()
                    line = data.readline().strip()
                cmd = "INSERT INTO Packages " \
                    "(Name, Version, Filename, Dependencies) VALUES "\
                    "(?,?,?,?)"
                self.cur.execute(cmd, (pkg_name, pkg_ver, pkg_path, pkg_dep))
                if line is None:
                    break
            line = data.readline().strip()
        self.con.commit()

    def find_similar(self, name):
        self.cur.execute(
            f"SELECT Name FROM Packages WHERE Name LIKE '%%{name}%%'")
        rows = self.cur.fetchall()
        return rows

    def add_dependency(self, data: str):
        data = data.split(',')
        for dependency in data:
            if '|' in dependency:
                self.DEPENDENCIES_TO_RESOLVE.append(dependency)
            else:
                self.add_package_approx(dependency)

    def add_package_approx(self, data: str):
        data = data.strip()
        version = PACKAGE_VERSION_REGEX.findall(data)

        if version:
            # In case there is a version
            package_name = version[0][0]
            version_type = version[0][1]
            version = version[0][2]
            self.add_package(package_name, version, version_type)
        else:
            # Case there is no version
            self.add_package(data)

    def add_package(self, name: str, version=None, version_type=None):
        name = name.replace(':any', '')
        if name in self.PACKAGES_TO_INSTALL:
            return
        self.cur.execute(
            f"SELECT Filename, Dependencies FROM Packages WHERE Name='{name}'")
        info = self.cur.fetchone()
        if not info:
            raise RuntimeError(f"Cannot find exact package {name}")
        self.PACKAGES_TO_INSTALL[name] = {"name": name, "filename": info[0]}

        if version:
            self.PACKAGES_TO_INSTALL[name]['version'] = version
            self.PACKAGES_TO_INSTALL[name]['version_type'] = version_type
        dependencies = info[1]
        if dependencies:
            self.add_dependency(dependencies)

    def post_resolve(self):
        for dependency in self.DEPENDENCIES_TO_RESOLVE:
            if '|' not in dependency:
                raise RuntimeError("An Unexpected dependency found")
            unresolved_dependencies = dependency.split('|')
            for unresolved_dependency in unresolved_dependencies:
                try:
                    self.add_package_approx(unresolved_dependency)
                    return
                except:
                    pass
            raise RuntimeError("Cannot find dependency")
        self.DEPENDENCIES_TO_RESOLVE.clear()

    def download(self, repo_url: str, downloads: Path):
        assert downloads.is_dir()
        for pkg in self.PACKAGES_TO_INSTALL.values():
            pkg_file = pkg["filename"].split("/")[-1]
            print(f"Downloading {pkg_file}")
            pkg_file = Path(downloads, pkg_file)
            if pkg_file.exists():
                continue
            pkg_data = requests.get(f"{repo_url}/{pkg['filename']}")
            assert pkg_data.status_code == 200
            with pkg_file.open("wb") as fd:
                fd.write(pkg_data.content)
