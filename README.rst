IQDB TAGGER
===========

Overview
--------

Get result from iqdb.org from CLI.

Feature::

 - iqdb and danbooru.iqdb parser
 - Hydrus integration


Usage
-----

Use as Hydrus iqdb script server
````````````````````````````````

1. Run *iqdb-tagger-server* and note the server address.
2. Import parsing script below to Hydrus parsing scripts.
3. Check the server address and edit it as needed.

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

Contributing
------------

TBD

Licence
-------

This project is licensed under the MIT License - see the LICENSE file for details


Authors
-------

iqdb_tagger was written by softashell and maintained by Rachmadani Haryono