#!/usr/bin/env python

"""Print entry in markdown table comparing 2 cmsRun timing JSON files made by parseCmsRunSummary.py"""


from __future__ import print_function
import os
import json
import argparse


# Inspiration from https://gitlab.cern.ch/cms-nanoAOD/nanoAOD-integration/blob/master/scripts/compare_sizes_json.py

def print_table_entry(ref_filename, new_filename, sample_name, do_header=False):
    """Print line in markdown table comparing timing ffrom 2 JSON files
    
    Parameters
    ----------
    ref_filename : str
        Reference JSON filename
    new_filename : str
        New JSON filename
    sample_name : str
        Sample name
    do_header : bool, optional
        If True, print markdown table header
    """
    ref_dict = None
    if os.path.isfile(ref_filename):
        with open(ref_filename) as rf:
            ref_dict = json.load(rf)

    new_dict = None
    if os.path.isfile(new_filename):
        with open(new_filename) as nf:
            new_dict = json.load(nf)

    key_name = "event loop Real/event"
    if do_header:
        print("| Sample | Reference {0} [s] | PR {0} [s] | diff |".format(key_name.lower()))
        print("| ------ | ------ | ------ | ------ |".format(key_name))

    # Do it this way to handle if one or both of the dicts doesn't exist
    line_args = {
        "name": sample_name,
        "reftime": "N/A",
        "newtime": "N/A",
        "difftime": "N/A",
    }

    if ref_dict:
        reftime = ref_dict['event_timing'][key_name]
        line_args["reftime"] = "%.3f" % reftime
    if new_dict:
        newtime = new_dict['event_timing'][key_name]
        line_args["newtime"] = "%.3f" % newtime
    if ref_dict and new_dict:
        delta = newtime - reftime
        delta_pc = 100 * delta / reftime
        line_args["diff"] = "%.3f / %.2f %%" % (delta, delta_pc)

    print("| {name} | {reftime} | {newtime} | {diff} |".format(**line_args))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True, help="Reference JSON file")
    parser.add_argument("--new", required=True, help="New JSON file")
    parser.add_argument("--name", required=True, help="Sample name")
    parser.add_argument("--header", action="store_true", default=False, help="Print table header")
    args = parser.parse_args()
    print_table_entry(args.ref, args.new, args.name, args.header)
