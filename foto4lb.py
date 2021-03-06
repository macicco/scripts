#!/usr/bin/env python3
# file: foto4lb.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2011-2018 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2011-11-07T21:40:58+01:00
# Last modified: 2018-07-07T18:49:17+0200
"""Shrink fotos to a size suitable for use in my logbook."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from os import cpu_count, mkdir, scandir, sep, utime
from os.path import exists
from time import mktime
import argparse
import logging
import sys
import subprocess

from PIL import Image
from PIL.ExifTags import TAGS

__version__ = '2.1.0'
outdir = 'foto4lb'
extensions = ('.jpg', '.jpeg', '.raw')


def main(argv):
    """
    Entry point for foto4lb.

    Arguments:
        argv: Command line arguments without the script name.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-w', '--width', default=886, type=int, help='width of the images in pixels (default 886)'
    )
    parser.add_argument(
        '--log',
        default='warning',
        choices=['debug', 'info', 'warning', 'error'],
        help="logging level (defaults to 'warning')"
    )
    parser.add_argument('-v', '--version', action='version', version=__version__)
    parser.add_argument('path', nargs='*', help='directory in which to work')
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log.upper(), None), format='%(levelname)s: %(message)s'
    )
    logging.debug(f'Command line arguments = {argv}')
    logging.debug(f'Parsed arguments = {args}')
    if not args.path:
        parser.print_help()
        sys.exit(0)
    checkfor('mogrify', rv=1)

    pairs = []
    count = 0
    for path in args.path:
        if exists(path + sep + outdir):
            logging.warning(f'"{outdir}" already exists in "{path}", skipping this path.')
            continue
        files = [
            f.name for f in scandir(path) if f.is_file() and f.name.lower().endswith(extensions)
        ]
        count += len(files)
        pairs.append((path, files))
        logging.debug(f'Path: "{path}"')
        logging.debug(f'Files: {files}')
    if len(pairs) == 0:
        logging.info('nothing to do.')
        return
    logging.info(f'found {count} files.')
    logging.info('creating output directories.')
    for dirname, _ in pairs:
        mkdir(dirname + sep + outdir)
    with ThreadPoolExecutor(max_workers=cpu_count()) as tp:
        agen = ((p, fn, args.width) for p, flist in pairs for fn in flist)
        for fn, rv in tp.map(processfile, agen):
            if rv == 0:
                fps = f"file '{fn}' processed."
            elif rv == 1:
                fps = f"file '{fn}' is not an image, skipped."
            elif rv == 2:
                fps = f"error running convert on '{fn}'."
            logging.info(fps)


def checkfor(args, rv=0):
    """
    Ensure that a program necessary for using this script is available.

    If the required utility is not found, this function will exit the program.

    Arguments:
        args: String or list of strings of commands. A single string may not
            contain spaces.
        rv: Expected return value from evoking the command.
    """
    if isinstance(args, str):
        if ' ' in args:
            raise ValueError('no spaces in single command allowed')
        args = [args]
    try:
        rc = subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc != rv:
            raise OSError
        logging.info(f'found required program "{args[0]}"')
    except OSError as oops:
        logging.error(f'required program "{args[0]}" not found: {oops.strerror}.')
        sys.exit(1)


def processfile(packed):
    """
    Read an image file and write a smaller version.

    Arguments:
        packed: A 3-tuple of (path, filename, output width)

    Returns:
        A 2-tuple (input file name, status).
        Status 0 indicates a succesful conversion,
        status 1 means that the input file was not a recognized image format,
        status 2 means a subprocess error.
    """
    path, name, newwidth = packed
    fname = sep.join([path, name])
    oname = sep.join([path, outdir, name.lower()])

    try:
        img = Image.open(fname)
        ld = {}
        for tag, value in img._getexif().items():
            decoded = TAGS.get(tag, tag)
            ld[decoded] = value
        want = set(['DateTime', 'DateTimeOriginal', 'CreateDate', 'DateTimeDigitized'])
        available = sorted(list(want.intersection(set(ld.keys()))))
        fields = ld[available[0]].replace(' ', ':').split(':')
        dt = datetime(
            int(fields[0]), int(fields[1]), int(fields[2]), int(fields[3]), int(fields[4]),
            int(fields[5])
        )
    except Exception:
        logging.warning('exception raised when reading the file time.')
        ed = {}
        dt = datetime.today()
        ed['CreateDate'] = f'{dt.year}:{dt.month}:{dt.day} {dt.hour}:{dt.minute}:{dt.second}'
    args = [
        'convert', fname, '-strip', '-resize',
        str(newwidth), '-units', 'PixelsPerInch', '-density', '300', '-unsharp', '2x0.5+0.7+0',
        '-quality', '80', oname
    ]
    rp = subprocess.call(args)
    if rp != 0:
        return (name, 2)
    modtime = mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0, -1))
    utime(oname, (modtime, modtime))
    return (fname, 0)


if __name__ == '__main__':
    main(sys.argv[1:])
