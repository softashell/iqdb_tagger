"""setup file."""
from distutils.util import convert_path  # NOQA; pylint: disable=import-error,E0611
from os import path
from typing import Dict  # NOQA

from setuptools import find_packages, setup

# get version from package
#  https://stackoverflow.com/a/24517154/1766261
main_ns = {}  # type: Dict
ver_path = convert_path("iqdb_tagger/__init__.py")
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)  # NOQA; pylint: disable=w0122
__version__ = main_ns["__version__"]

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst")) as f:
    long_description = f.read()


setup(
    name="iqdb_tagger",
    version=__version__,
    description="Get result from iqdb.org.",
    long_description=long_description,
    url="https://github.com/softashell/iqdb_tagger",
    download_url="https://github.com/softashell/iqdb_tagger" "/tarball/" + __version__,
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
    ],
    keywords="",
    packages=find_packages(exclude=["docs", "tests*"]),
    include_package_data=True,
    author="softashell",
    maintainer="Rachmadani Haryono",
    maintainer_email="foreturiga@gmail.com",
    install_requires=[
        "appdirs>=1.4.4",
        "beautifulsoup4>=4.9.3",
        "cfscrape>=2.1.1",
        "click>=7.1.2",
        "Flask-Admin>=1.5.8",
        "flask-paginate>=0.8.1",
        "Flask-RESTful>=0.3.8",
        "Flask-WTF>=0.14.3",
        "Flask>=1.1.2",
        "funclog>=0.3.0",
        "hydrus-api>=2.14.3",
        "lxml>=4.6.3",
        "MechanicalSoup>=1.0.0",
        "peewee>=3.14.4",
        "Pillow>=8.2.0",
        "structlog>=21.1.0",
        "wtf-peewee>=3.0.2",
    ],
    extras_require={
        "doc": [
            "sphinx-autobuild>=0.7.1",
            "sphinx-rtd-theme>=0.2.4",
            "Sphinx>=1.6.3",
        ],
        "dev": [
            "black",
            "flake8-docstrings>=1.1.0",
            "flake8-quotes>=0.11.0",
            "flake8>=3.9.1",
            "isort",
            "mypy>=0.812",
            "pydocstyle<4.0.0",
            "pylint>=2.8.2",
            "pytest-flake8",
            "pytest-mypy",
            "pytest>=6.2.4",
            "twine>=3.4.1",
            "vcrpy>=4.1.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "iqdb-tagger = iqdb_tagger.__main__:cli",
        ]
    },
)
