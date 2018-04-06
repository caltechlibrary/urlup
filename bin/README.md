urlup
=====

(Pronounced _urrr-lop_) This is a simple program to dereference URLs and determine their final destinations after following redirections.


✺ Installation instructions
---------------------------

### ⓵&nbsp;&nbsp; _Check and install dependencies_

`urlup` uses some Python modules that may or may not be installed in your Python environment.  Depending on the approach you use to install Spiral, you may or may not need to install them separately:

* [plac](https://pypi.python.org/pypi/plac), a command line arguments parser.
* [termcolor](https://pypi.python.org/pypi/termcolor), for color-coding text printed to the terminal

To install `urlup`, clone the git repository to a location on your computer.

▶︎ Basic operation
------------------

`urlup` provides a command-line utility as well as a library.  The command-line utility can be used from a terminal shell.  It prints help text when given the `-h` option.

For a simple, quick check of one or two URLs, you can simply provide the URLs on the command line:

```
# ./bin/urlup http://sbml.org
No output file given -- results won't be saved.
http://sbml.org ==> http://sbml.org/Main_Page [301]
Done.
```

The typical usage is to provide it with a list of URLs in a file (one per line) with the `-i` option, and to tell it to write the results to a CSV file with the `-o` option.

```
# ./bin/urlup  -i original_urls.txt  -o final_urls.csv
```
