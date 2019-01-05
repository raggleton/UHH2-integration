#!/usr/bin/env python


"""Make webpage(s) from ntuple plots & timing, size infos"""


from __future__ import print_function

import os
import sys
import json
import shutil
import argparse
import pandas as pd
import numpy as np
from collections import OrderedDict
from distutils.dir_util import copy_tree
from jinja2 import Template, Environment, FileSystemLoader
try:
    # py2
    from itertools import izip_longest
except ImportError:
    # py3
    from itertools import zip_longest as izip_longest


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks

    Taken from iterools recipes
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


class Group(object):

    def __init__(self, this_id, title, contents):
        self.id = this_id
        self.title = title
        self.contents = contents


class Plot(object):

    def __init__(self, this_id, thumbnailname, filename, caption, title):
        self.id = this_id
        self.thumbnailname = thumbnailname
        self.filename = filename
        self.caption = caption
        self.title = title


def add_plot_group(group_key, plot_names, plot_dir, skip_these=None):
    plots = []
    skip_these = skip_these or []
    for plot_name in plot_names:
        if plot_name in skip_these:
            continue
        this_thumbnailname = plot_name.replace("()", "") + ".gif"  # As specified in plotCompareNtuples.py
        this_filename = plot_name.replace("()", "") + ".pdf"  # As specified in makeNtupleCOmparisonTableAll.sh
        plots.append(Plot(this_id=plot_name,
                          thumbnailname=os.path.join(plot_dir, "thumbnails", this_thumbnailname),
                          filename=os.path.join(plot_dir, this_filename),
                          # use <wbr> to allow line break, otherwise need spaces to wrap
                          caption=plot_name.replace(".", "<wbr>."),
                          title=plot_name,
                          )
                    )

    this_title = group_key.replace("_", " ").title()
    this_title += " (%d)" % len(plots)
    this_item = Group(this_id=group_key.replace(" ", "_"),
                      title=this_title,
                      contents=plots
                      )
    return this_item


def safe_str(label):
    """Create HTML/filesystem safe str ie no spaces, etc"""
    return label.replace(" ", "_")


def main(in_args):
    """This is setup to allow multiple pages to be made in one go,
    which will have a common menu to switch between their samples.
    Thus it is best used for all the pages from one CI pipeline run.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plotjson", help="Input plots JSON file", required=True, action='append')
    parser.add_argument("--plotdir", help="Directory with plots in JSON file", required=True, action='append')
    parser.add_argument("--timingrefjson", help="Input reference timing JSON file", action='append')
    parser.add_argument("--timingnewjson", help="Input new timing JSON file", action='append')
    parser.add_argument("--sizerefjson", help="Input reference size JSON file", action='append')
    parser.add_argument("--sizenewjson", help="Input new size JSON file", action='append')
    parser.add_argument("--label", help="Label for given plot file", required=True, action='append')
    parser.add_argument("--outputDir", help="Directory for output files & figures", default=".")
    args = parser.parse_args(in_args)
    print(args)

    if not os.path.isdir(args.outputDir):
        os.makedirs(args.outputDir)

    # Get location of tempalte dir relative to where this file is,
    # since can't guarantee where this file is being run from
    script_dir = os.path.dirname(__file__)
    TEMPLATE_DIR = os.path.normpath(os.path.join(script_dir, '..', 'templates'))
    file_loader = FileSystemLoader(TEMPLATE_DIR)

    # trim extra newlines around template entries
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)

    template = env.get_template("plotPage.html")

    # no outputDir as relative to other pages, all of which in outputDir
    set_of_pages = [(label, "%s.html" % safe_str(label)) for label in args.label]

    # Check length of args to ensure all matching arguments
    all_args = [args.plotjson, args.plotdir,
                args.timingrefjson, args.timingnewjson,
                args.sizerefjson, args.sizenewjson,
                args.label]

    if not all(len(x) == len(all_args[0]) for x in all_args[1:]):
        raise RuntimeError("You must provide the same number of "
                           "--plotjson, plotdir, timingrefjson, timingnewjson, "
                           "sizerefjson, sizenewjson, label argument")

    # Make page & everything for each sample
    for (plotjson, plotdir, timing_ref_json, timing_new_json,
         size_ref_json, size_new_json, label) in zip(*all_args):

        label_safe = safe_str(label)
        # Define this here first, since everything else will need to be relative to it
        html_filename = os.path.join(args.outputDir, "%s.html" % (label_safe))

        #######################################################################
        # PLOTS
        #######################################################################

        # Copy files to figs dir, including thumbnail
        figs_dir = os.path.join(args.outputDir, label_safe + '_figs')
        if not os.path.isdir(figs_dir):
            os.makedirs(figs_dir)
        placeholder_dest = os.path.join(figs_dir, 'placeholder.jpg')
        placeholder_src = os.path.join(TEMPLATE_DIR, 'placeholder.jpg')
        shutil.copyfile(placeholder_src, placeholder_dest)
        # location relative to HTML file, for use in the HTML
        rel_placeholder_img = os.path.relpath(placeholder_dest, os.path.dirname(html_filename))
        copy_tree(plotdir, figs_dir)

        with open(plotjson) as f:
            orig_plot_data = json.load(f, object_pairs_hook=OrderedDict)

        # Do added/remove hists first
        # Use new location for plots, relative to where HTML will end up
        rel_figs_dir = os.path.relpath(figs_dir, os.path.dirname(html_filename))
        plot_data = [
                     add_plot_group(group_key=key,
                                    plot_names=orig_plot_data[key]['names'],
                                    plot_dir=rel_figs_dir)
                     for key in ['added_hists', 'removed_hists']
                    ]

        # Now do all other comparisons
        plot_data.extend([
                          add_plot_group(group_key=key,
                                         plot_names=orig_plot_data['comparison'][key]['names'],
                                         plot_dir=rel_figs_dir)
                          for key in orig_plot_data['comparison']
                         ])

        #######################################################################
        # TIMING
        #######################################################################
        # Get timing data
        with open(timing_ref_json) as f:
            timing_ref_data = json.load(f, object_pairs_hook=OrderedDict)

        with open(timing_new_json) as f:
            timing_new_data = json.load(f, object_pairs_hook=OrderedDict)

        # Per event timing
        df_event_timing_new = pd.DataFrame.from_dict(timing_new_data['event_timing'], orient='index')
        df_event_timing_new.rename(lambda x: 'New', axis='columns', inplace=True)
        df_event_timing_new.rename(lambda x: x+' [s]', inplace=True)

        df_event_timing_ref = pd.DataFrame.from_dict(timing_ref_data['event_timing'], orient='index')
        df_event_timing_ref.rename(lambda x: 'Ref', axis='columns', inplace=True)
        df_event_timing_ref.rename(lambda x: x+' [s]', inplace=True)

        df_event_timing_diff = df_event_timing_ref.join(df_event_timing_new)
        df_event_timing_diff['Diff'] = df_event_timing_diff['New'] - df_event_timing_diff['Ref']
        # df_event_timing_diff = df_event_timing_diff.T

        timing_event_dict = df_event_timing_diff.to_dict(orient='split')
        timing_event_headers = ['Module name'] + timing_event_dict['columns']
        timing_event_rows = [[m] + data for m, data in zip(timing_event_dict['index'], timing_event_dict['data'])]

        # Per module timing
        df_mod_timing_ref = pd.DataFrame.from_dict(timing_ref_data['module_timing'], orient='index')
        drop_cols = ['per_exec', 'per_visit', 'per_exec_frac', 'per_visit_frac']
        df_mod_timing_ref.drop(columns=drop_cols, inplace=True)
        df_mod_timing_ref.rename(lambda x: x.replace("_", " ").title() + " (Ref) [s]", axis='columns', inplace=True)
        for header in df_mod_timing_ref.columns.values:  # convert from fraction to %, drop fraction
            if 'frac' not in header.lower():
                continue
            df_mod_timing_ref[header] = 100. * df_mod_timing_ref[header]
            df_mod_timing_ref.rename(columns={header: header.replace('[s]', '[%]')}, inplace=True)

        df_mod_timing_new = pd.DataFrame.from_dict(timing_new_data['module_timing'], orient='index')
        df_mod_timing_new.drop(columns=drop_cols, inplace=True)
        df_mod_timing_new.rename(lambda x: x.replace("_", " ").title() + " (New) [s]", axis='columns', inplace=True)
        for header in df_mod_timing_new.columns.values:
            if 'frac' not in header.lower():
                continue
            df_mod_timing_new[header] = 100. * df_mod_timing_new[header]
            df_mod_timing_new.rename(columns={header: header.replace('[s]', '[%]')}, inplace=True)

        df_mod_timing_diff = df_mod_timing_ref.join(df_mod_timing_new, how='outer')
        df_mod_timing_diff = df_mod_timing_diff[~(df_mod_timing_diff==0).all(axis=1)]  # get rid of rows that are all 0s
        for href, hnew in zip(df_mod_timing_ref.columns.values, df_mod_timing_new.columns.values):
            if '%' in href:
                # only do absolute differences, not diff in %s
                continue
            df_mod_timing_diff['Diff '+href.replace(" (Ref)", "")] = df_mod_timing_new[hnew] - df_mod_timing_ref[href]

        timing_mod_dict = df_mod_timing_diff.to_dict(orient='split')
        timing_mod_headers = ['Module name'] + timing_mod_dict['columns']
        timing_mod_rows = [[m] + data for m, data in zip(timing_mod_dict['index'], timing_mod_dict['data'])]

        #######################################################################
        # FILESIZE
        #######################################################################
        # Get filesize data
        with open(size_ref_json) as f:
            size_ref_data = json.load(f, object_pairs_hook=OrderedDict)

        with open(size_new_json) as f:
            size_new_data = json.load(f, object_pairs_hook=OrderedDict)

        # Overall info (over all collections)
        headers = ["size_per_event", "size_frac"]

        total_coll_name = "Total"
        def _make_size_df(size_dict, label):
            this_dict = {}
            for colname, data in size_dict['branch_sizes'].items():
                this_dict[colname] = {h:data[h] for h in headers}
            # manually add total as another entry
            this_dict[total_coll_name] = {
                "size_per_event": size_dict["total_branch_size_per_event"],
                "size_frac": size_dict["total_branch_frac"]
            }
            df_size = pd.DataFrame.from_dict(this_dict, orient='index')
            df_size['size_frac'] = 100. * df_size['size_frac']
            df_size.rename({"size_frac": "%", "size_per_event": "kb / event"}, axis=1, inplace=True)
            df_size.rename(lambda x: x + " (" + label + ")", axis=1, inplace=True)  # do it last as we need originals for prior renaming
            return df_size

        df_size_ref = _make_size_df(size_ref_data, 'Ref')
        df_size_new = _make_size_df(size_new_data, 'New')

        df_size_diff = df_size_ref.join(df_size_new, how='outer')
        df_size_diff = df_size_diff[~(df_size_diff==0).all(axis=1)]  # get rid of rows that are all 0s

        # Add difference column(s)
        for href, hnew in zip(df_size_ref.columns.values, df_size_new.columns.values):
            if '%' in href:
                # only do absolute differences, not diff in %s
                continue
            df_size_diff['Diff '+href.replace(" (Ref)", "")] = df_size_new[hnew] - df_size_ref[href]

        size_overall_headers = ['Collection name'] + list(df_size_diff.columns.values)
        size_mod_dict = df_size_diff.to_dict(orient='split')
        size_overall_rows = [[m] + data for m, data in zip(size_mod_dict['index'], size_mod_dict['data']) if m != total_coll_name]
        size_overall_total = [[m] + data for m, data in zip(size_mod_dict['index'], size_mod_dict['data']) if m == total_coll_name]

        # Per collection info
        size_mod_data = OrderedDict()
        size_mod_headers = []

        def _make_coll_size_df(col_size_dict, label):
            this_dict = {}
            total_frac = col_size_dict['size_frac']
            if len(col_size_dict['children']) == 0:
                return None
            for varname, vardata in col_size_dict['children'].items():
                this_dict[varname] = {
                    'size_per_event': vardata['size_per_event'],
                    'size_frac': 100. * vardata['size_frac'] / total_frac
                }
            df_size = pd.DataFrame.from_dict(this_dict, orient='index')
            df_size.rename({"size_frac": "%", "size_per_event": "kb / event"}, axis=1, inplace=True)
            df_size.rename(lambda x: x + " (" + label + ")", axis=1, inplace=True)  # do it last as we need originals for prior renaming
            return df_size

        for colname, data in size_ref_data['branch_sizes'].items():
            df_mod_size_ref = _make_coll_size_df(data, "Ref")
            if df_mod_size_ref is None:
                continue
            size_mod_data[colname] = [df_mod_size_ref, None]

        for colname, data in size_new_data['branch_sizes'].items():
            df_mod_size_new = _make_coll_size_df(data, "New")
            if df_mod_size_new is None:
                continue
            existing = size_mod_data.get(colname, None)
            if existing:
                existing = existing[0]
            size_mod_data[colname] = [existing, df_mod_size_new]

        data_frames = OrderedDict()
        for colname in sorted(size_mod_data.keys()):
            data = size_mod_data[colname]
            # account for missing collections
            if data[0] is None and data[1] is not None:
                existing = data[1]
                data[0] = pd.DataFrame(np.zeros_like(existing), index=existing.index, columns=existing.columns)
            elif data[0] is not None and data[0] is None:
                existing = data[0]
                data[1] = pd.DataFrame(np.zeros_like(existing), index=existing.index, columns=existing.columns)

            if len(data) != 2:
                raise RuntimeError("Each collection should have 2 dataframes")

            df_size_ref, df_size_new = data
            # Create combined dataframe
            df_size_diff = df_size_ref.join(df_size_new, how='outer')
            # Add difference column(s)
            for href, hnew in zip(df_size_ref.columns.values, df_size_new.columns.values):
                if '%' in href:
                    # only do absolute differences, not diff in %s
                    continue
                df_size_diff['Diff '+href.replace(" (Ref)", "")] = df_size_new[hnew] - df_size_ref[href]

            data_frames[colname] = df_size_diff

        size_mod_headers = ['Member name'] + list(list(data_frames.values())[0].columns.values)
        size_mod_rows = OrderedDict()
        for colname, df in data_frames.items():
            this_size_mod_dict = df.to_dict(orient='split')
            size_rows = [[m] + data for m, data in zip(this_size_mod_dict['index'], this_size_mod_dict['data'])]
            size_mod_rows[colname] = size_rows

        #######################################################################
        # MAKE FINAL HTML
        #######################################################################
        # Render template with objects
        prnum = os.environ.get("PRNUM", -1)
        gitlab_url = os.environ.get("CI_PIPELINE_URL", "https://gitlab.cern.ch/raggleto/UHH2-integration/pipelines")
        output = template.render(prnum=prnum, sample=label,
                                 gitlab_url=gitlab_url,
                                 num_plots=orig_plot_data['total_number'],
                                 plot_data=plot_data,
                                 placeholder_img=rel_placeholder_img,
                                 set_of_pages=set_of_pages,
                                 timing_event_headers=timing_event_headers,
                                 timing_event_rows=timing_event_rows,
                                 timing_mod_headers=timing_mod_headers,
                                 timing_mod_rows=timing_mod_rows,
                                 size_overall_headers=size_overall_headers,
                                 size_overall_total=size_overall_total,  # do separately for own special fixed row
                                 size_overall_rows=size_overall_rows,
                                 size_mod_headers=size_mod_headers,
                                 size_mod_data=size_mod_rows
                                )

        print("Writing html to", html_filename)
        with open(html_filename, "w") as outf:
            outf.write(output)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
