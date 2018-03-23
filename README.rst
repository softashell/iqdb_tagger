IQDB TAGGER
===========

.. image:: https://travis-ci.org/rachmadaniHaryono/iqdb_tagger.svg?branch=master
    :target: https://travis-ci.org/rachmadaniHaryono/iqdb_tagger

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


Use as Hydrus as cli program
````````````````````````````

To parse folder of images (e.g. in this example :code:`image_folder:`) and write tags to text file, use following command:

.. code:: bash

    iqdb-tagger --resize --match-filter best-match --write-tags --input-mode folder image_folder


Use as Hydrus iqdb script server
````````````````````````````````
1. Run :code:`iqdb-tagger-server init` when you run the server for first time.
2. Run :code:`iqdb-tagger-server start` and note the server address.
3. Import one of the parsing scripts below to Hydrus parsing scripts.
4. Check the server address and edit it as needed.

Danbooru parsing script

.. code:: json

    [32, "local iqdb danbooru", 1, ["http://127.0.0.1:5000/?place=danbooru&resize", 1, 0, 0, "file", {}, [[29, 1, ["link to danbooru", [27, 2, [[["a", {"data-status": "best-match", "data-netloc": "danbooru-donmai"}, 0]], "href", [0, 0, "", ""]]], [[30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-1"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], "creator"]], [30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-3"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], "series"]], [30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-4"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], "character"]], [30, 1, ["", 0, [27, 2, [[["section", {"id": "tag-list"}, 0], ["li", {"class": "category-0"}, null], ["a", {"class": "search-tag"}, 0]], null, [0, 0, "", ""]]], ""]]]]]]]]

IQDB parsing script

.. code:: json

    [32, "local iqdb tag cache", 1, ["http://127.0.0.1:5000/?resize", 1, 0, 0, "file", {}, [[29, 1, ["link to local cache", [27, 2, [[["a", {"data-status": "best-match", "class": "img-match-detail"}, null]], "href", [0, 0, "", ""]]], [[30, 1, ["", 0, [27, 2, [[["ul", {"id": "tag-info-list"}, 0], ["li", {"class": "tag-creator"}, null]], null, [0, 0, "", ""]]], "creator"]], [30, 1, ["", 0, [27, 2, [[["ul", {"id": "tag-info-list"}, 0], ["li", {"class": "tag-character"}, null]], null, [0, 0, "", ""]]], "character"]], [30, 1, ["", 0, [27, 2, [[["ul", {"id": "tag-info-list"}, 0], ["li", {"class": "tag-series"}, null]], null, [0, 0, "", ""]]], "series"]], [30, 1, ["", 0, [27, 2, [[["ul", {"id": "tag-info-list"}, 0], ["li", {"class": "tag-general"}, null]], null, [0, 0, "", ""]]], ""]], [30, 1, ["", 0, [27, 2, [[["ul", {"id": "tag-info-list"}, 0], ["li", {"class": "tag-meta"}, null]], null, [0, 0, "", ""]]], "meta"]], [30, 1, ["", 0, [27, 2, [[["ul", {"id": "tag-info-list"}, 0], ["li", {"class": "tag-circle"}, null]], null, [0, 0, "", ""]]], "circle"]], [30, 1, ["", 0, [27, 2, [[["ul", {"id": "tag-info-list"}, 0], ["li", {"class": "tag-style"}, null]], null, [0, 0, "", ""]]], "style"]]]]]]]]

Every uploaded and match history can be seen on Front page (in this case http://127.0.0.1:5000).

Installation
------------

Install it with from pypi

.. code:: bash

    $ pip install iqdb_tagger

Or install it manually

.. code:: bash

    $ git clone https://github.com/rachmadaniHaryono/iqdb_tagger.git
    $ cd iqdb_tagger
    # run the command below
    $ python setup.py install
    # for windows user: to force it using python3 run following command
    $ python -3 setup.py install
    # or
    $ pip install .

If you are in windows and get SyntaxError, check your python version.
To install under python3 follow the instruction on this link https://stackoverflow.com/a/18059129/1766261

CHANGELOG
---------

0.1.0 (2018-02-26)
``````````````````

- new input mode. Now the program can parse folder to find file
- new single match page
- new argument :code:`abort-on-error` to stop the program when error occured
- new argument :code:`write-tags` to write parsed tag to text file
- change the post method. now it is default to use :code:`requests.post`
- change the way server start. run init subcommand first before start the server
- remove :code:`html-dump` argument.
- fix pillow error. Install pillow if error stil raised.
- fix png upload error.
- fix OSError when thumbnail is an empty file.


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
