#!/usr/bin/env python


"""Tests for the different filetypes in the PR diff.

Tests both the whole file, as well as the lines under change.
"""


from __future__ import print_function
import sys
from diff_parser import parse_diff


def print_line_message(filename, line_location, message):
    print(filename, "[L"+str(line_location)+"]:", message)
    

def cpp_filetests(filename):
    """Tests to run on whole C++ file"""
    return True


def cpp_linetests(filediff):
    """Tests to run on individual diff lines in C++ file"""
    for change in filediff.changes:
        for line in change.get_new_lines():
            if "cout" in line.line_contents:
                print_line_message(filediff.new_filename, change.new_loc[0], "cout - probably don't want this?")
    
    return True


def xml_filetests(filename):
    """Tests to run on whole XML file"""
    return True


def xml_linetests(filediff):
    """Tests to run on individual diff lines in C++ file"""
    return True


def py_filetests(filename):
    """Tests to run on whole python file"""
    # test with pylint
    pass


def py_linetests(filediff):
    """Tests to run on individual diff lines in python file"""
    pass


def test_diff(diff_file):
    test_fileext_mapping = {
        (('cxx', 'cpp', 'cc'), cpp_filetests, cpp_linetests),
        (('xml'), xml_filetests, xml_linetests),
        (('py'), py_filetests, py_linetests),
    }

    for f in parse_diff(diff_file):
        for ext, filetest, linetest in test_fileext_mapping:
            if f.new_filename.endswith(ext):
                filetest(f.new_filename)
                linetest(f)

    return 0


if __name__ == "__main__":
    sys.exit(test_diff(sys.argv[1]))
