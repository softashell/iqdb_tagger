"""setup file."""
from codecs import open
from os import path

from setuptools import find_packages, setup

__version__ = '0.0.1'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

install_requires = [
    'click>=6.7',
    'funclog>=0.3.0',
    'lxml>=3.8.0',
    'MechanicalSoup>=0.7.0',
    'peewee>=2.10.1',
    'structlog>=17.2.0',
]

setup(
    name='iqdb_tagger',
    version=__version__,
    description='Get result from iqdb.org.',
    long_description=long_description,
    url='https://github.com/rachmadaniHaryono/iqdb_tagger',
    download_url='https://github.com/rachmadaniHaryono/iqdb_tagger'
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
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'iqdb-tagger = iqdb_tagger.__main__:main',
        ]
    }

)
