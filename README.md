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

The following is probably the simplest and most direct way to install `urlup` on your computer:
```sh
sudo pip3 install git+https://github.com/caltechlibrary/urlup.git
```

Alternatively, you can clone this GitHub repository and then run `setup.py`:
```sh
git clone https://github.com/caltechlibrary/urlup.git
cd urlup
sudo python3 -m pip install .
```
Both of these installation approaches should automatically install some Python dependencies that `urlup` relies upon, namely [plac](https://pypi.python.org/pypi/plac) and [termcolor](https://pypi.python.org/pypi/termcolor).

▶︎ Basic operation
------------------

_urlup_ provides a command-line utility as well as a library.  The command-line utility is called `urlup` and can be used from a terminal shell.  It prints help text when given the `-h` option.

For a simple, quick check of one or two URLs, you can simply provide the URLs on the command line:

```
# urlup http://sbml.org
No output file given -- results won't be saved.
http://sbml.org ==> http://sbml.org/Main_Page [301]
Done.
```

The typical usage is to provide it with a list of URLs in a file (one per line) with the `-i` option, and to tell it to write the results to a CSV file with the `-o` option.

```
# urlup  -i original_urls.txt  -o final_urls.csv
```

Here is a screen cast to demonstrate. Click on the following image:

[![demo](.graphics/urlup-asciinema.png)](https://asciinema.org/a/Q90dPtCEO3D1iQvYVaSvqoecW?autoplay=1)


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/urlup/issues) for this repository.


☮︎ Copyright and license
---------------------

Copyright (C) 2018, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.
    
<div align="center">
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src=".graphics/caltech-round.svg">
  </a>
</div>
