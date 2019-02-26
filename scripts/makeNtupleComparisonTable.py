#!/usr/bin/env python

"""Make markdown table from JSON made by compareNtuples.py.
Table contents produced as STDOUT.

Can process multiple JSON, for each both --json and --label must be specified.
"""

from __future__ import print_function

import os
import sys
import json
import argparse
from collections import OrderedDict


def get_number_safely(idict, key):
    entry = idict.get(key, None)
    if None:
        return -1
    return int(entry['number'])


def main(in_args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="Input JSON plot file", action='append')
    parser.add_argument("--label", help="Label for given plot file.", action='append')
    args = parser.parse_args(in_args)

    if len(args.json) != len(args.label):
        raise RuntimeError("number of --json must match number of --label")

    input_data = {}
    for filename, label in zip(args.json, args.label):
        if not os.path.isfile(filename):
            print("Cannot find %s, skipping" % filename)
        with open(filename) as f:
            this_data = json.load(f)
        input_data[label] = this_data

    parsed_data = OrderedDict()
    all_statuses = []
    status_descriptions = {}
    for label in sorted(list(input_data.keys())):
        idict = input_data[label]
        parsed_data[label] = OrderedDict()
        parsed_data[label]['total_#_hists'] = idict['total_number']
        parsed_data[label]['added_collections'] = get_number_safely(idict, 'added_collections')
        parsed_data[label]['removed_collections'] = get_number_safely(idict, 'removed_collections')
        parsed_data[label]['added_hists'] = get_number_safely(idict, 'added_hists')
        parsed_data[label]['removed_hists'] = get_number_safely(idict, 'removed_hists')
        comparison_dict = idict['comparison']
        for status_name, status_entry in comparison_dict.items():
            parsed_data[label][status_name] = status_entry['number']
            all_statuses.append(status_name)
            status_descriptions[status_name] = status_entry['description']

    all_statuses = sorted(list(set(all_statuses)))
    # want last col to be "same" as least interesting
    all_statuses.insert(len(all_statuses), all_statuses.pop(all_statuses.index('SAME')))

    # bit hacky as we want to put DIFF_MEAN_RMS earliest
    all_statuses_mod = all_statuses[:]
    if 'DIFF_MEAN_RMS' in all_statuses:
        all_statuses_mod.remove("DIFF_MEAN_RMS")

    fields = ['name', 'total_#_hists', 'DIFF_MEAN_RMS', 'added_collections', 'added_hists', 'removed_collections', 'removed_hists']
    fields.extend(all_statuses_mod)  # fields is used for keys for later string formatting, determines order of columns

    # Print out column headings using fields
    header = "| " + ' | '.join([f.replace("_", " ").lower() for f in fields]) + " |"
    print(header)
    hline = "| " + ' | '.join(['----' for x in fields]) + " |"
    print(hline)

    # Print table contents
    for name, data in parsed_data.items():
        # Update data to account for missing labels
        for s in all_statuses:
            if s not in parsed_data[name]:
                parsed_data[name][s] = 0

        data_str = " | ".join(["{"+f+"}" for f in fields])  # create template str for this row
        # update name to include link to webpage
        # TODO: some way to coordinate this with doPRReview, etc
        url = "https://uhh2-integration.web.cern.ch/UHH2integration/%s/%s.html" % (os.environ['LOCALBRANCH'], name)
        fancy_name = "[%s](%s)" % (name, url)
        table_entry = ("| " + data_str + " |").format(name=fancy_name, **parsed_data[name])  # numbers actually get put in here
        print(table_entry)
    print("\n")

    # Print description of each status
    for s in all_statuses:
        print(" - **{name}**: {description}".format(name=s.replace("_", " ").lower(), description=status_descriptions[s]))
    print("\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
