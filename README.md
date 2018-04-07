urlup
=====

This is a simple program to dereference URLs and determine their final destinations after following redirections.  _urlup_ can be pronounced "_urrrl-up_".

*Authors*:      [Michael Hucka](http://github.com/mhucka)<br>
*Repository*:   [https://github.com/caltechlibrary/urlup](https://github.com/caltechlibrary/urlup)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

☀ Introduction
-----------------------------

Sometimes we have a list of URLs and we need to find out the ultimate destinations after any redirections have taken place. _urlup_ is a simple program to dereference a list of URLs for that purpose.

✺ Installation instructions
---------------------------

### ⓵&nbsp;&nbsp; _Check and install dependencies_

`urlup` uses some Python modules that may or may not be installed in your Python environment.  Depending on the approach you use to install Spiral, you may or may not need to install them separately:

* [plac](https://pypi.python.org/pypi/plac), a command line arguments parser.
* [termcolor](https://pypi.python.org/pypi/termcolor), for color-coding text printed to the terminal

### ⓶&nbsp;&nbsp; _Download and install urlup_

To install `urlup`, clone the git repository to a location on your computer.

▶︎ Basic operation
------------------

_urlup_ provides a command-line utility as well as a library.  The command-line utility is called `urlup` and can be used from a terminal shell.  It prints help text when given the `-h` option.

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

Here is a screen cast to demonstrate. Click on the following image:

[![demo](.graphics/urlup-asciinema.png)](https://asciinema.org/a/s14GQit2kI4eSiX1sluRjtINO?autoplay=1)


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/urlup/issues) for this repository.


☮︎ Copyright and license
---------------------

Copyright (C) 2018, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.
