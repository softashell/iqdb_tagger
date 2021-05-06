Changelog
=========

0.3.2 (2021-05-06)
``````````````````

- return when no file id
- chunks file ids
- resize flag for subcommands

0.3.1 (2019-07-26)
``````````````````

- fix permission error
- fix minimum similarity
- update hydrus requirement

0.3.0 (2019-04-30)
``````````````````
- search and send tag to hydrus
- search and send url to hydrus
- merge cli and server

0.2.2 (2018-07-01)
``````````````````
- minimum similarity
- more iqdb place

0.2.1 (2018-05-31)
``````````````````
- fix windows bug on temp file

0.2.0 (2018-03-31)
``````````````````
- add template for manifest.in
- not creating thumbnail anymore

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

0.0.1 (2012-04-09)
``````````````````

- new: documentation [rachmadaniHaryono]
- change: upload folder is moved to temporary folder based on each os [rachmadaniHaryono]
- First commit
