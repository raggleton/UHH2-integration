#!/usr/bin/env python


"""Make webpage(s) from ntuple plots & timing, size infos"""


from __future__ import print_function

import os
import sys
import json
from jinja2 import Template, Environment, FileSystemLoader
import argparse
from collections import OrderedDict
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
    # parser.add_argument("--timingjson", help="Input timing JSON file", action='append')
    # parser.add_argument("--sizejson", help="Input size JSON file", action='append')
    parser.add_argument("--label", help="Label for given plot file.", required=True, action='append')
    parser.add_argument("--outputDir", help="Directory for output directories.", default=".")
    args = parser.parse_args(in_args)
    print(args)

    if not os.path.isdir(args.outputDir):
        os.makedires(args.outputDir)

    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)

    template = env.get_template("plotPage.html")

    set_of_pages = [(label, os.path.join(args.outputDir, "%s.html" % label.replace(" ", "_")))
                    for label in args.label]

    for plotjson, plotdir, label in zip(args.plotjson, args.plotdir, args.label):

        with open(plotjson) as f:
            orig_plot_data = json.load(f, object_pairs_hook=OrderedDict)

        # Do added/remove hists first:
        added_removed_plots = []
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

        # Render template with objects
        prnum = os.environ.get("PRNUM", -1)
        gitlab_url = os.environ.get("CI_PIPELINE_URL", "https://gitlab.cern.ch/raggleto/UHH2-integration/pipelines")
        output = template.render(prnum=prnum, sample=label,
                                 gitlab_url=gitlab_url,
                                 num_plots=orig_plot_data['total_number'],
                                 plot_data=plot_data,
                                 set_of_pages=set_of_pages
                                )

        html_filename = os.path.join(args.outputDir, "%s.html" % label.replace(" ", "_"))
        print("Writing html to", html_filename)
        with open(html_filename, "w") as outf:
            outf.write(output)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
