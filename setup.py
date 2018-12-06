"""setup file."""
from os import path

from setuptools import find_packages, setup

__version__ = '0.2.3'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='iqdb_tagger',
    version=__version__,
    description='Get result from iqdb.org.',
    long_description=long_description,
    url='https://github.com/softashell/iqdb_tagger',
    download_url='https://github.com/softashell/iqdb_tagger'
    '/tarball/' + __version__,
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
    keywords='',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    author='softashell',
    author_email='foreturiga@gmail.com',
    maintainer='Rachmadani Haryono',
    maintainer_email='foreturiga@gmail.com',
    install_requires=[
        'appdirs>=1.4.3',
        'beautifulsoup4>=4.6.3',
        'cfscrape>=1.9.5',
        'click>=7.0',
        'Flask-Admin>=1.5.2',
        'flask-paginate>=0.5.1',
        'Flask-WTF>=0.14.2',
        'Flask>=1.0.2',
        'funclog>=0.3.0',
        'lxml>=3.8.0',
        'MechanicalSoup>=0.7.0',
        'peewee>=2.10.1',
        'Pillow>=4.2.1',
        'structlog>=17.2.0',
        'wtf-peewee>=3.0.0',
    ],
    extras_require={
        'doc': [
            'sphinx-autobuild>=0.7.1',
            'sphinx-rtd-theme>=0.2.4',
            'Sphinx>=1.6.3',
        ],
        'dev': [
            'flake8-docstrings>=1.1.0',
            'flake8-quotes>=0.11.0',
            'flake8>=3.3.0',
            'pylint>=1.7.2',
            'pytest>=3.1.2',
            'vcrpy>=1.11.1',
        ],
    },
    entry_points={
        'console_scripts': [
            'iqdb-tagger = iqdb_tagger.__main__:cli',
            'iqdb-tagger-server = iqdb_tagger.server:cli',
        ]
    }
)
