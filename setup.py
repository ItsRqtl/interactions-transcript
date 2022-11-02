import os

from setuptools import setup

# set the values below
github_repository_url: str = "https://github.com/ItsRqtl/interactions-transcript"
project_version: str = "0.0.3"
author_name: str = "ItsRqtl"
author_email: str = "itsrqtl@gmail.com"
short_project_description: str = "An extension library for interactions.py to create transcripts."

# don't touch anything after this comment

_flag: bool = False
_package_name: str = None
_project_name: str = None

if (
    not github_repository_url
    or not project_version
    or not author_name
    or not short_project_description
    or not author_email
):
    _flag = True
    raise ValueError("You need to fill in the emtpy (None) variables in setup.py!")

_project_path = "interactions/ext"

if "project (rename this!)" in os.listdir(_project_path):
    _flag = True
    raise ValueError("Your package (folder) must have a name!")

_dirs: int = 0
for element in os.listdir(_project_path):
    if os.path.isdir(f"{_project_path}/{element}"):
        _dirs += 1
        _package_name = element

    if _dirs > 1:
        _flag = True
        raise ValueError("You must only have one directory in interactions/ext")

if not _package_name:
    _flag = True
    raise ValueError("Could not find a package in interactions/ext!")

with open("README.md", "r", encoding="utf-8") as ld:
    long_description = ld.read()

    _project_name = long_description.splitlines()[0].removeprefix("# ")

    if _project_name == "interactions-XXXXX":
        _flag = True
        raise ValueError("You need to specify a valid name for your project!")

if _flag:
    # just to ensure the program terminates if gh somehow does not stop after an exc
    exit(-1)


with open("requirements.txt", "r", encoding="utf-8") as _requirements:
    requirements = _requirements.read().strip().splitlines()

setup(
    name=_project_name,
    version=project_version,
    description=short_project_description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=github_repository_url,
    author=author_name,
    author_email=author_email,
    license="MIT",
    packages=[f"interactions.ext.{_package_name}"],
    include_package_data=True,
    python_requires=">=3.8.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
)
