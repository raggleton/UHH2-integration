#!/usr/bin/env python

"""Assemble all the relevant items and post to github pull request"""


from __future__ import print_function
import os
import sys
import argparse
import subprocess


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plots", help="Ntuple plots comparison markdown table filename", default=None)
    parser.add_argument("--timing", help="Timing markdown table filename", default=None)
    parser.add_argument("--size", help="Size markdown table filename", default=None)
    args = parser.parse_args()

    comment_text = "Report for PR %s\n" % (str(os.environ.get('PRNUM', None)))
    # this is set in makeAllWebpages, but we also include a backup incase something went wrong
    web_ending = os.environ.get('WEBEND', 'UHH2integration/'+os.environ['LOCALBRANCH'])
    comment_text += "Webpages with full plots, timing & size info: http://uhh2-integration.web.cern.ch/%s\n\n" % (web_ending)

    if args.plots:
        if not os.path.isfile(args.plots):
            print("Cannot find plots comparison file %s, skipping" % args.plots)
        comment_text += "\n\n**Ntuple comparison report**\n\n"
        with open(args.plots) as f:
            comment_text += f.read()
        comment_text += "\n\n"

    if args.timing:
        if not os.path.isfile(args.timing):
            print("Cannot find timing file %s, skipping" % args.timing)
        comment_text += "\n\n**Timing report**\n\n"
        with open(args.timing) as f:
            comment_text += f.read()
        comment_text += "\n\n"

    if args.size:
        if not os.path.isfile(args.size):
            print("Cannot find size file %s, skipping" % args.size)
        comment_text += "\n\n**Size report**\n(kB = kilobytes, `.` is decimal point not thousands separator)\n\n"
        with open(args.size) as f:
            comment_text += f.read()
        comment_text += "\n\n"

    comment_text = comment_text.replace("\n", "\\n").replace('"', '\\"')
    # print(comment_text)
    return_code = subprocess.call('source ${CI_PROJECT_DIR}/scripts/notify_github.sh "passed" "%s"' % (comment_text), shell=True)

    sys.exit(0)
