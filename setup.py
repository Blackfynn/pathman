#!/usr/bin/env/ python
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages

with open('pathman/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

with open('requirements.txt', 'r') as fd:
    requirements = fd.readlines()

setup(
    name="pathman",
    version=version,
    author="Blackfynn, Inc.",
    author_email="zach.duey@blackfynn.com",
    description="Utility for interacting with local and remote paths through a uniform interface",
    packages=find_packages(),
    package_dir={'pathman': 'pathman'},
    install_requires=requirements,
    license="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ]
)
