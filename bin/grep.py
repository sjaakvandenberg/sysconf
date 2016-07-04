#!/usr/bin/env python

# TODO: may want to implement also the AND logic, not only OR
# TODO: implement num of lines above and below

"""
Recursively grep (or replaces) occurrences of <str> in all "dev" files
in this directory.  Very similar to "ack" CLI util."

Usage:
    grep.py [-e <exts>] [-r] [-i] [<pattern> ...]

Options:
    -e <exts> --exts=<exts>   # a list of extensions defult=%s
    -r --replace              # replace 2 patterns
    -i --ignore-case          # case insensitive

Examples:
    grep.py -e py,c,h pattern    # extensions
    grep.py foo bar              # search for 'foo' AND 'bar' on the same line
    grep.py -r foo bar           # replaces 'foo' with 'bar'
"""

from __future__ import print_function
import os
import sys

from docopt import docopt

from sysconf import hilite


DEFAULT_EXTS = [
    'c',
    'h',
    'in',
    'ini',
    'md',
    'py',
    'rst',
    'txt',
    'yaml',
    'yml',
]
SPECIAL_NAMES = [
    'README',
]
IGNORE_ROOT_DIRS = [
    '.git',
    'build',
    'dist',
]
__doc__ = __doc__ % str(tuple(DEFAULT_EXTS))


def grep_file(filepath, patterns, replace=False, ignore_case=False):
    def get_file_content():
        with open(filepath, 'r') as f:
            data = f.read()
        if ignore_case:
            data = data.lower()
        return data

    def print_occurrences(lines, patterns):
        if not isinstance(lines, list):
            # probably a file object
            lines = iter(lines)
        occurrences = 0
        header_printed = False
        for lineno, line in enumerate(lines, 1):
            for pattern in patterns:
                # lowercase() the line on the fly, but we want to keep
                # the original one around in order to print it.
                temp_line = line if not ignore_case else line.lower()
                if pattern not in temp_line:
                    break
            else:
                if not header_printed:
                    print(hilite(filepath, bold=1))
                    header_printed = True
                # Note: if case-sensitive, this may not highlit the
                # line (well... who cares =)).
                for pattern in patterns:
                    line = line.replace(pattern, hilite(pattern))
                print("%s: %s" % (
                    hilite(lineno, ok=None, bold=1), line.rstrip()))
                occurrences += 1
        if occurrences:
            print()
        return occurrences

    def find_single_pattern(pattern):
        assert isinstance(pattern, basestring)
        data = get_file_content()
        occurrences = 0
        if pattern in data:
            lines = data.splitlines()
            occurrences += print_occurrences(lines, patterns)
        return occurrences

    def find_multi_patterns(patterns):
        assert isinstance(patterns, list)
        if replace and len(patterns) != 2:
            sys.exit("with --replace you must specifcy 2 <pattern>s")
        with open(filepath, 'r') as f:
            occurrences = print_occurrences(f, set(patterns))
        return occurrences

    def replace_patterns(patterns):
        with open(filepath, 'r') as f:
            data = f.read()
        src, dst = patterns
        new_data = data.replace(src, dst)
        occurrences = 0
        if data != new_data:
            occurrences = data.count(src)
            print("%s (%s occurrences)" % (
                hilite(filepath, bold=1), hilite(occurrences)))
            with open(filepath, 'w') as f:
                f.write(new_data)
        return occurrences

    if ignore_case:
        patterns = [x.lower() for x in patterns]
    if len(set(patterns)) != len(patterns):
        sys.exit("<pattern>s can't be equal")
    if len(patterns) == 1 and not ignore_case:
        return find_single_pattern(patterns[0])
    if len(patterns) == 2 and replace:
        if ignore_case:
            sys.exit("can't user --ignore-case with --replace")
        return replace_patterns(patterns)
    else:
        return find_multi_patterns(patterns)


def main(argv=None):
    # CLI
    args = docopt(__doc__, argv=None)
    if args['--exts']:
        exts = args['--exts'].split(',')
    else:
        exts = DEFAULT_EXTS
    for i, ext in enumerate(exts):
        if not ext.isalnum() and ext != '*':
            sys.exit("invalid extension %s" % ext)
        if not ext.startswith('.'):
            exts[i] = '.' + ext
    exts = set(exts)

    patterns = args['<pattern>']
    replace = args['--replace']
    ignore_case = args['--ignore-case']

    # run
    start_ext = exts == set(['.*'])
    files_matching = 0
    occurrences = 0
    for root, dirs, files in os.walk('.', topdown=False):
        parent_root = os.path.normpath(root).split('/')[0]
        if parent_root in IGNORE_ROOT_DIRS:
            continue  # skip
        if parent_root.endswith('.egg-info'):
            continue  # skip
        for name in files:
            if os.path.splitext(name)[1] not in exts:
                if name not in SPECIAL_NAMES:
                    if not start_ext:
                        continue   # skip
            filepath = os.path.join(root, name)
            ocs = grep_file(
                filepath, patterns, replace=replace, ignore_case=ignore_case)
            occurrences += ocs
            if ocs:
                files_matching += 1

    if occurrences:
        print("occurrences=%s, files-matching=%s" % (
            hilite(occurrences, bold=1),
            hilite(files_matching, bold=1)
        ))


if __name__ == '__main__':
    main()
