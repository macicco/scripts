#!/usr/bin/env python3
# vim:fileencoding=utf-8:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Last modified: 2015-10-21 23:10:02 +0200
#
# To the extent possible under law, Roland Smith has waived all copyright and
# related or neighboring rights to foto4lb.py. This work is published from the
# Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

"""Shrink fotos to a size suitable for use in my logbook and other
   documents."""

__version__ = '1.2.0'

from datetime import datetime
from os import utime, cpu_count
from time import mktime, monotonic
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
import sys

from wand.image import Image


def main(argv):
    """Main program.

    Keyword arguments:
    argv -- command line arguments
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-w', '--width',
                        default=886,
                        type=int,
                        help='width of the images in pixels (default 886)')
    parser.add_argument('--log', default='warning',
                        choices=['debug', 'info', 'warning', 'error'],
                        help="logging level (defaults to 'warning')")
    parser.add_argument('-v', '--version',
                        action='version',
                        version=__version__)
    parser.add_argument('file', nargs='*')
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log.upper(), None),
                        format='%(levelname)s: %(message)s')
    logging.debug('Command line arguments = {}'.format(argv))
    logging.debug('Parsed arguments = {}'.format(args))
    if not args.file:
        parser.print_help()
        sys.exit(0)
    with ProcessPoolExecutor(max_workers=cpu_count()) as tp:
        fl = [tp.submit(processfile, fn, newwidth=args.width)
              for fn in args.file]
        for fut in as_completed(fl):
            fn, dt = fut.result()
            logging.info("file '{}' processed in {:.1f} sec.".format(fn, dt))


def processfile(name, newwidth):
    starttime = monotonic()
    with Image(filename=name) as img:
        w, h = img.size
        scale = newwidth / w
        exif = {k[5:]: v for k, v in img.metadata.items()
                if k.startswith('exif:')}
        img.units = 'pixelsperinch'
        img.resolution = (300, 300)
        img.resize(width=newwidth, height=round(scale*h))
        img.strip()
        img.compression_quality = 80
        img.unsharp_mask(radius=2, sigma=0.5, amount=0.7, threshold=0)
        img.save(filename=name)
    want = set(['DateTime', 'DateTimeOriginal', 'DateTimeDigitized'])
    try:
        available = list(want.intersection(set(exif.keys())))
        available.sort()
        fields = exif[available[0]].replace(' ', ':').split(':')
        dt = datetime(int(fields[0]), int(fields[1]), int(fields[2]),
                      int(fields[3]), int(fields[4]), int(fields[5]))
    except:
        dt = datetime.today()
    modtime = mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
                      0, 0, -1))
    utime(name, (modtime, modtime))
    endtime = monotonic()
    return name, endtime - starttime


if __name__ == '__main__':
    main(sys.argv[1:])
