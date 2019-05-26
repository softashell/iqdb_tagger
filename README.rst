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

    iqdb-tagger cli-run --resize --match-filter best-match --write-tags --input-mode folder image_folder


Use as Hydrus iqdb script server
````````````````````````````````
1. Run :code:`iqdb-tagger run` and note the server address.

  To run it on `127.0.0.1` on port `5006`, run the following command:

.. code:: bash

    `iqdb-tagger run -h 127.0.0.1 -p 5006`
  
2. Import one of the parsing scripts below to Hydrus parsing scripts.
3. Check the server address and edit it as needed.

IQDB parsing script

.. code:: json

    [32, "local iqdb", 2, ["http://127.0.0.1:5006", 1, 0, [55, 1, [[], "some hash bytes"]], "file", {"place": "0", "resize": "on"}, [[29, 1, ["link", [27, 5, [[["a", {"data-status": "best-match", "class": "img-match-detail"}, null]], 0, "href", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], [[30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-creator"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], "creator"]], [30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-series"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], "series"]], [30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-character"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], "character"]], [30, 2, ["", 0, [27, 5, [[["li", {"class": "tag-general"}, null]], 1, "", [51, 1, [3, "", null, null, "example string"]], [55, 1, [[], "parsed information"]]]], ""]]]]]]]]

Every uploaded and match history can be seen on Front page (in this case http://127.0.0.1:5006).

Using IQDB-tagger with Hydrus API
`````````````````````````````````

Set up your hydrus to get the access key, which will be used for this feature.


after that you can run the command below. For example to run the command with image tagged as 'thread:cat' on hydrus

.. code:: bash

   # to get tags
   iqdb-tagger search-hydrus-and-send-tag --access-key 1234_your_access_key 'thread:cat'
   # to get matching urls
   iqdb-tagger search-hydrus-and-send-url --access-key 1234_your_access_key 'thread:cat'

Note: hydrus version 349 have default bandwidth of 100 mb data per month,
which may raise `ApiError` when the bandwidth reached.

to fix it, go to `services` menu -> `manage services` -> client api and raise your bandwidth limit

Setting Hydrus iqdb script server on NAS
````````````````````````````````````````

Here is example for Synology DS1817+ with DSM6.1.7 running on an Intel Atom C2538

0. Make sure SSH is turned on in your control panel
1. Install python 3 community package: https://synocommunity.com/package/python3
2. Install pip3

.. code:: bash

  install pip3 with:
  sudo -i
  wget https://bootstrap.pypa.io/get-pip.py
  python3 get-pip.py

3. Install iqdb-tagger

.. code:: bash

  cd /volume1/@appstore/py3k/usr/local/bin
  ./pip install iqdb_tagger

3.1 Add `bin` folder to path (optional)

.. code:: bash

  export PATH=$PATH:/volume1/@appstore/py3k/usr/local/bin 

That command line above can also be put on `~/.bashrc`, so NAS will run it everytime user login.

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
