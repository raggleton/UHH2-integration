#!/usr/bin/env python

"""Assemble all the relevant items and post to github pull request"""


from __future__ import print_function
import os
import sys
import argparse
import subprocess


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing", help="Timing markdown table filename", default=None)
    args = parser.parse_args()

    comment_text = "Report for PR %s\n\n" % (str(os.environ.get('PRNUM', None)))

    if args.timing:
        if not os.path.isfile(args.timing):
            print("Cannot find timing file %s, skipping" % args.timing)
        comment_text += "\n\n**Timing report**\n\n"
        with open(args.timing) as f:
            comment_text += f.read()

    
    comment_text = comment_text.replace("\n", "\\n").replace('"', '\\"')
    # print(comment_text)
    return_code = subprocess.call('source ${CI_PROJECT_DIR}/scripts/post_comment.sh "%s"' % (comment_text), shell=True)