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

    iqdb-tagger run --resize --match-filter best-match --write-tags --input-mode folder image_folder


Use as Hydrus iqdb script server
````````````````````````````````
1. Run :code:`iqdb-tagger-server init` when you run the server for first time.
2. Run :code:`iqdb-tagger-server start` and note the server address.
3. Import one of the parsing scripts below to Hydrus parsing scripts.
4. Check the server address and edit it as needed.

IQDB parsing script

.. code:: json

    [32, "local iqdb", 2, ["http://127.0.0.1:5006", 1, 0, [55, 1, [[], "some hash bytes"]], "file", {"place": "0", "resize": "on"}, [[29, 1, ["link", [27, 5, [[["a", {"data-status": "best-match", "class": "img-match-detail"}, null]], 0, "href", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], [[30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-creator"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], "creator"]], [30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-series"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], "series"]], [30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-character"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], "character"]], [30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-general"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], ""]]]]]]]]

Every uploaded and match history can be seen on Front page (in this case http://127.0.0.1:5006).

Installation
------------

Install it with from pypi

.. code:: bash

    $ pip install iqdb_tagger

Or install it manually

.. code:: bash

    $ git clone https://github.com/softashell/iqdb_tagger.git
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

0.2.0 (2018-03-31)
``````````````````

- new argument :code:`write-tags` to write parsed tag to text file
- both cli and server now don't create thumbnail anymore
- main cli command is moved to :code:`run` command

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
