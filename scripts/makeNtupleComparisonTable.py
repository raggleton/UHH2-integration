#!/usr/bin/env python

"""Make markdown table from JSON made by compareNtuples.py"""

from __future__ import print_function

import os
import sys
import json
import argparse
from collections import OrderedDict


def get_number_safely(idict, key):
    entry = idict.get(key, None)
    if None:
        return 0
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
    for label, idict in input_data.items():
        parsed_data[label] = OrderedDict()
        parsed_data[label]['total'] = idict['total_number']
        parsed_data[label]['added_collections'] = get_number_safely(idict, 'added_collections')
        parsed_data[label]['removed_collections'] = get_number_safely(idict, 'removed_collections')
        parsed_data[label]['added_hists'] = get_number_safely(idict, 'added_hists')
        parsed_data[label]['removed_hists'] = get_number_safely(idict, 'removed_hists')
        comparison_dict = idict['comparison']
        for sname, sentry in comparison_dict.items():
            parsed_data[label][sname] = sentry['number']
            all_statuses.append(sname)
            status_descriptions[sname] = sentry['description']

    all_statuses = sorted(list(set(all_statuses)))
    # want 1st col to be "same"
    all_statuses.insert(0, all_statuses.pop(all_statuses.index('SAME')))

    fields = ['name', 'total', 'added_collections', 'added_hists', 'removed_collections', 'removed_hists']
    fields.extend(all_statuses)
    header = "| " + ' | '.join([f.replace("_", " ").lower() for f in fields]) + " |"
    print(header)
    hline = "| " + ' | '.join(['----' for x in fields]) + " |"
    print(hline)
    for name, data in parsed_data.items():
        # Update data to account for missing labels
        for s in all_statuses:
            if s not in parsed_data[name]:
                parsed_data[name][s] = 0
        
        data_str = " | ".join(["{"+f+"}" for f in fields])
        table_entry = ("| " + data_str + " |").format(name=name, **parsed_data[name])
        print(table_entry)
    print("\n")
    for s in all_statuses:
        print(" - **{name}**: {description}".format(name=s.replace("_", " ").lower(), description=status_descriptions[s]))
    print("\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
