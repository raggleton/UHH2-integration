#!/usr/bin/env python


"""Produce JSON with size info about branch sizes from a Ntuple"""


from __future__ import print_function

import ROOT
import json
import argparse


class BranchInfo(object):
    """Class to store relevant info about a TBranch"""

    def __init__(self, name, classname, uncompressed_size, uncompressed_size_recursive, compressed_size, compressed_size_recursive, title, entries):
        self.name = name
        self.classname = classname
        self.uncompressed_size = uncompressed_size
        self.uncompressed_size_recursive = uncompressed_size_recursive
        self.compressed_size = compressed_size
        self.compressed_size_recursive = compressed_size_recursive
        self.title = title
        self.entries = entries
        self.children = []
        if classname == "" and title != "":
            self.classname = title.split('/')[-1]

    def __repr__(self):
        return ("{name}: {classname}, {uncompressed_size}b, {uncompressed_size_recursive}b (recur.), "
                "{compressed_size}b, {compressed_size_recursive}b (recur.), "
                "{title}, {nchild} children, {entries} entries".format(nchild=len(self.children), **self.__dict__))

    def __str__(self):
        return ("{name}: {classname}, {uncompressed_size}b, {uncompressed_size_recursive}b (recur.), "
                "{compressed_size}b, {compressed_size_recursive}b (recur.), "
                "{title}, {nchild} children, {entries} entries".format(nchild=len(self.children), **self.__dict__))

    def __eq__(self, other):
        return self.name == other.name and self.classname == other.classname


B_TO_KB = 1024.


def store_branches_recursively(tree, obj_list, indent=0):
    """Iterate through tree recursively, storing branch info as BranchInfo objects to obj_list.

    Note that this isn't perfect, it won't see more than 2 levels of nested
    vectors (e.g. those of subjets of TopJets). But it's enough for our diagnostics.

    Parameters
    ----------
    tree : TTree, TBranch - anything that has branches
        Description
    obj_list : list[BranchInfo]
        List to append BranchInfo objects to
    indent : int, optional
        Indentation for printout. If None, does not print
    """
    tree_name = tree.GetName()
    for b in tree.GetListOfBranches():
        this_name = b.GetName()
        # Add parent branch name since TTree::Draw doesn't care about repeated names,
        # and sometimes it gets left off
        if not this_name.startswith(tree_name):
            this_name = tree_name+"."+this_name
        # b.SetName(this_name)
        this_br_info = BranchInfo(name=this_name,
                                  classname=b.GetClassName(),
                                  uncompressed_size=b.GetTotBytes() / B_TO_KB,
                                  uncompressed_size_recursive=b.GetTotBytes('*') / B_TO_KB,
                                  compressed_size=b.GetZipBytes() / B_TO_KB,
                                  compressed_size_recursive=b.GetZipBytes('*') / B_TO_KB,
                                  title=b.GetTitle(),
                                  entries=b.GetEntries()  # broken, gives tree entries
                                  )
        new_indent = indent
        if indent is not None:
            print(" "*indent, this_br_info)
            new_indent += 2
        obj_list.append(this_br_info)
        store_branches_recursively(b, obj_list, new_indent)


def produce_size_json(input_filename, json_filename, tree_name, verbose=False):
    tree_info = []

    # Get all branch info
    f = ROOT.TFile(input_filename)
    tree = f.Get(tree_name)
    store_branches_recursively(tree, tree_info, 0 if verbose else None)

    total_branch_size = sum([b.compressed_size for b in tree_info])
    file_size = f.GetSize() / B_TO_KB
    other_size = file_size - total_branch_size

    n_entries = tree.GetEntries()
    size_dict = {
        "nentries": n_entries,
        "file_size": file_size,
        "size_per_event": file_size / n_entries,
        "other_size_per_event": other_size / n_entries,
        "other_size_frac": other_size / file_size,
        "total_branch_size_per_event": total_branch_size / n_entries,
        "total_branch_frac": total_branch_size / file_size,
        "branch_sizes": {},
    }

    for b in tree_info:
        if b.name.startswith(tree_name):
            # top level i.e. the collections themselves
            stripped_name = b.name.replace(tree_name+".", "")
            size_dict['branch_sizes'][stripped_name] = {
                "size_frac": b.compressed_size_recursive / total_branch_size,
                "size_per_event": b.compressed_size_recursive / n_entries,
                "children": {}
            }
        else:
            # nested, want to strip of the preceeding branch name
            # we don't have to do this down many layers, since we only care about
            # immediate children of this collection.
            # Use recursive size to ensure it captures any (hidden) children
            start_name = b.name.split(".")[0]
            new_name = ".".join(b.name.split(".")[1:])
            size_dict['branch_sizes'][start_name]['children'][new_name] = {
                "size_frac": b.compressed_size_recursive / total_branch_size,
                "size_per_event": b.compressed_size_recursive / n_entries
            }

    # print(size_dict)
    with open(json_filename, 'w') as f:
        json.dump(size_dict, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input ROOT ntuple filename")
    parser.add_argument("--json", help="JSON output filename", default="size.json")
    default_tree = "AnalysisTree"
    parser.add_argument("--treeName", help="Name of TTree, defaults to %s" % default_tree, default=default_tree)
    parser.add_argument("-v", help="Print branch infos", action='store_true')
    args = parser.parse_args()

    produce_size_json(args.input, args.json, args.treeName, args.v)
