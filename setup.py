# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

__version__ = "0.2.2"

with open("requirements.txt", "r") as fd:
    requirements = fd.readlines()

setup(
    name="pathman",
    version=__version__,
    author="Blackfynn, Inc.",
    author_email="zach.duey@blackfynn.com",
    description=(
        "Utility for interacting with local and remote paths through a uniform"
        " interface"
    ),
    packages=find_packages(exclude=["tests"]),
    package_dir={"pathman": "pathman"},
    package_data={"pathman": ["py.typed"]},
    install_requires=requirements,
    license="",
    classifiers=["Development Status :: 3 - Alpha", "Topic :: Utilities"],
)
