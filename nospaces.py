#!/usr/bin/env python3
# vim:fileencoding=utf-8:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Last modified: 2017-06-04 13:46:58 +0200
#
# To the extent possible under law, Roland Smith has waived all copyright and
# related or neighboring rights to nospaces.py. This work is published from the
# Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

"""Change whitespace in file names to underscores."""

import os
import sys

__version__ = '1.0.1'


def main(argv):
    """
    Entry point for nospaces.

    Arguments:
        argv: All command line arguments.
    """
    if len(argv) == 1:
        binary = os.path.basename(argv[0])
        print("{} version {}".format(binary, __version__), file=sys.stderr)
        print("Usage: {} [file ...]".format(binary), file=sys.stderr)
        sys.exit(0)
    del argv[0]  # delete the name of the script.
    for n in argv:
        try:
            os.rename(n, fixname(n))
        except OSError as e:
            print('Renaming "{}" failed: {}'.format(n, e.strerror))


def fixname(path):
    """
    Replace whitespace in a path by underscores.

    Arguments:
        path: The path to change.

    Returns:
        The updated path.
    """
    path = os.path.normpath(path)
    head, tail = os.path.split(path)
    tl = tail.split()
    tail = '_'.join(tl)
    return os.path.join(head, tail)


if __name__ == '__main__':
    main(sys.argv)
