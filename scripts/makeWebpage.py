#!/usr/bin/env python


"""Make webpage(s) from ntuple plots & timing, size infos"""


from __future__ import print_function

import os
import sys
import json
import argparse
import pandas as pd
from collections import OrderedDict
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

    def __init__(self, this_id, title, plots):
        self.id = this_id
        self.title = title
        self.plots = plots


class Plot(object):

    def __init__(self, this_id, thumbnailname, filename, caption):
        self.id = this_id
        self.thumbnailname = thumbnailname
        self.filename = filename
        self.caption = caption


def add_plot_group(group_key, plot_names, plot_dir, skip_these=None):
    plots = []
    skip_these = skip_these or []
    for plot_name in plot_names:
        if plot_name in skip_these:
            continue
        this_thumbnailname = plot_name.replace("()", "") + ".gif"
        this_filename = plot_name.replace("()", "") + ".pdf"
        plots.append(Plot(this_id=plot_name,
                          thumbnailname=os.path.join(plot_dir, "thumbnails", this_thumbnailname),
                          filename=os.path.join(plot_dir, this_filename),
                          caption=plot_name))

    this_title = group_key.replace("_", " ").title()
    this_title += " (%d)" % len(plots)
    this_item = Group(this_id=group_key.replace(" ", "_"),
                      title=this_title,
                      plots=plots)
    return this_item


def main(in_args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plotjson", help="Input plots JSON file", required=True, action='append')
    parser.add_argument("--plotdir", help="Directory with plots in JSON file", required=True, action='append')
    parser.add_argument("--timingrefjson", help="Input reference timing JSON file", action='append')
    parser.add_argument("--timingnewjson", help="Input new timing JSON file", action='append')
    # parser.add_argument("--sizejson", help="Input size JSON file", action='append')
    parser.add_argument("--label", help="Label for given plot file.", required=True, action='append')
    parser.add_argument("--outputDir", help="Directory for output directories.", default=".")
    args = parser.parse_args(in_args)
    print(args)

    if not os.path.isdir(args.outputDir):
        os.makedires(args.outputDir)

    file_loader = FileSystemLoader('templates')
    # trim extra newlines around template entries
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)

    template = env.get_template("plotPage.html")

    set_of_pages = [(label, os.path.join(args.outputDir, "%s.html" % label.replace(" ", "_")))
                    for label in args.label]

    for plotjson, plotdir, timing_ref_json, timing_new_json, label in zip(args.plotjson, args.plotdir, args.timingrefjson, args.timingnewjson, args.label):

        with open(plotjson) as f:
            orig_plot_data = json.load(f, object_pairs_hook=OrderedDict)

        # Do added/remove hists first:
        plot_data = [
                     add_plot_group(group_key=key,
                                    plot_names=orig_plot_data[key]['names'],
                                    plot_dir=plotdir)
                     for key in ['added_hists', 'removed_hists']
                    ]

        # Now do all other comparisons
        plot_data.extend([
                          add_plot_group(group_key=key,
                                         plot_names=orig_plot_data['comparison'][key]['names'],
                                         plot_dir=plotdir)
                          for key in orig_plot_data['comparison']
                         ])

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
        drop_cols = ['per_exec', 'per_visit']
        df_mod_timing_ref.drop(columns=drop_cols, inplace=True)
        df_mod_timing_ref.rename(lambda x: x.replace("_", " ").title() + " (Ref) [s]", axis='columns', inplace=True)
        headers_ref = list(df_mod_timing_ref.columns.values)

        df_mod_timing_new = pd.DataFrame.from_dict(timing_new_data['module_timing'], orient='index')
        df_mod_timing_new.drop(columns=drop_cols, inplace=True)
        df_mod_timing_new.rename(lambda x: x.replace("_", " ").title() + " (New) [s]", axis='columns', inplace=True)
        headers_new = list(df_mod_timing_new.columns.values)

        df_mod_timing_diff = df_mod_timing_ref.join(df_mod_timing_new, how='outer')
        df_mod_timing_diff = df_mod_timing_diff[~(df_mod_timing_diff==0).all(axis=1)]  # get rid of rows that are all 0s
        for href, hnew in zip(headers_ref, headers_new):
            df_mod_timing_diff[href.replace('[s]', '[%]')] = 100. * df_mod_timing_ref[href] / df_mod_timing_ref[href].sum(skipna=True)
            df_mod_timing_diff[hnew.replace('[s]', '[%]')] = 100. * df_mod_timing_new[hnew] / df_mod_timing_new[hnew].sum(skipna=True)
            df_mod_timing_diff['Diff '+href.replace(" (Ref)", "")] = df_mod_timing_new[hnew] - df_mod_timing_ref[href]

        timing_mod_dict = df_mod_timing_diff.to_dict(orient='split')
        timing_mod_headers = ['Module name'] + timing_mod_dict['columns']
        timing_mod_rows = [[m] + data for m, data in zip(timing_mod_dict['index'], timing_mod_dict['data'])]

        # Render template with objects
        prnum = os.environ.get("PRNUM", -1)
        gitlab_url = os.environ.get("CI_PIPELINE_URL", "https://gitlab.cern.ch/raggleto/UHH2-integration/pipelines")
        output = template.render(prnum=prnum, sample=label,
                                 gitlab_url=gitlab_url,
                                 num_plots=orig_plot_data['total_number'],
                                 plot_data=plot_data,
                                 set_of_pages=set_of_pages,
                                 timing_event_headers=timing_event_headers,
                                 timing_event_rows=timing_event_rows,
                                 timing_mod_headers=timing_mod_headers,
                                 timing_mod_rows=timing_mod_rows,
                                )

        html_filename = os.path.join(args.outputDir, "%s.html" % label.replace(" ", "_"))
        print("Writing html to", html_filename)
        with open(html_filename, "w") as outf:
            outf.write(output)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
