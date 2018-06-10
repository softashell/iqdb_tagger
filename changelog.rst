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
- First commit
