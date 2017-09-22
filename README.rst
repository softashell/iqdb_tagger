IQDB TAGGER
===========

.. image:: https://travis-ci.org/jarun/Buku.svg?branch=master
    :target: https://travis-ci.org/jarun/Buku

.. image:: https://img.shields.io/badge/python-3-brightgreen.svg

Overview
--------

Get result from iqdb.org from CLI using python3.

Feature::

 - Written for python3
 - iqdb and danbooru.iqdb parser
 - Hydrus integration


Usage
-----

Use as Hydrus iqdb script server
````````````````````````````````
1. Run :code:`iqdb-tagger-server init` when you run the server for first time.
2. Run :code:`iqdb-tagger-server start` and note the server address.
3. Import parsing script below to Hydrus parsing scripts.
4. Check the server address and edit it as needed.

.. code:: json

    [32, "local iqdb danbooru", 1, ["http://127.0.0.1:5000/?place=danbooru&resize", 1, 0, 0, "file", {}, [[29, 1, ["link to danbooru", [27, 2, [[["a", {"data-status": "best-match", "data-netloc": "danbooru-donmai"}, 0]], "href", [0, 0, "", ""]]], [[30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-1"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], "creator"]], [30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-3"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], "series"]], [30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-4"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], "character"]], [30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-0"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], ""]]]]]]]]

Every uploaded and match history can be seen on Front page (in this case http://127.0.0.1:5000).

Installation
------------

To install use pip:

.. code:: bash

    $ pip install iqdb_tagger


Or clone the repo:

.. code:: bash

    $ git clone https://github.com/rachmadaniHaryono/iqdb_tagger.git
    $ python setup.py install

CHANGELOG
---------

0.1.0 (TBA)
```````````

- change the way server start. run init subcommand first before start the server
- fix pillow error. Install pillow if error stil raised.
- fix png upload error.
- fix OSError when thumbnail is an empty file.

0.0.1
`````
- Program created

FAQ
---

libxml error in Windows
```````````````````````

If you are encounter this error on Windows

.. code::

    Could not find function xmlCheckVersion in library libxml2. Is libxml2 installed?

Please follow this guide to install lxml: `StackOverflow - how to install lxml on windows?`_

Contributing
------------

TBD

Licence
-------

This project is licensed under the MIT License - see the LICENSE file for details


Authors
-------

iqdb_tagger was written by softashell and maintained by Rachmadani Haryono

.. _StackOverflow - how to install lxml on windows?: https://stackoverflow.com/questions/29440482/how-to-install-lxml-on-windows
