#!/usr/bin/env python

"""Print entry in markdown table comparing 2 Ntuple size JSON files made by treeSizeReport.py"""


from __future__ import print_function
import os
import json
import argparse


# Inspiration from https://gitlab.cern.ch/cms-nanoAOD/nanoAOD-integration/blob/master/scripts/compare_sizes_json.py

def print_table_entry(ref_filename, new_filename, sample_name, do_header=False):
    """Print line in markdown table comparing sizes from 2 JSON files

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

    key_name = "total_branch_size_per_event"
    if do_header:
        print("| Sample | Reference {0} [kb] | PR {0} [kb] | diff |".format(key_name.lower().replace("_", " ")))
        print("| ------ | ------ | ------ | ------ |")

    # update name to include link to webpage
    # TODO: some way to coordinate this with doPRReview, etc
    url = "https://uhh2-integration.web.cern.ch/UHH2integration/%s/%s.html#size" % (os.environ['LOCALBRANCH'], sample_name)
    sample_name = "[%s](%s)" % (sample_name, url)

    # Do it this way to handle if one or both of the dicts doesn't exist
    line_args = {
        "name": sample_name,
        "refsize": "N/A",
        "newsize": "N/A",
        "diffsize": "N/A",
    }

    if ref_dict:
        refsize = ref_dict[key_name]
        line_args["refsize"] = "%.3f" % refsize
    if new_dict:
        newsize = new_dict[key_name]
        line_args["newsize"] = "%.3f" % newsize
    if ref_dict and new_dict:
        delta = newsize - refsize
        delta_pc = 100 * delta / refsize
        line_args["diff"] = "%.3f / %.2f %%" % (delta, delta_pc)

    print("| {name} | {refsize} | {newsize} | {diff} |".format(**line_args))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True, help="Reference JSON file")
    parser.add_argument("--new", required=True, help="New JSON file")
    parser.add_argument("--name", required=True, help="Sample name")
    parser.add_argument("--header", action="store_true", default=False, help="Print table header")
    args = parser.parse_args()
    print_table_entry(args.ref, args.new, args.name, args.header)
