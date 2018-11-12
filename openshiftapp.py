#!/usr/bin/env python

"""App to listen for github events, and carry out a corresponding task e.g. push to gitlab

NB if you rename this file to `app.py` in the future, you'll need to set
`APP_FILE` in openshift to null otherwise it'll run this instead of gunicorn:
https://github.com/sclorg/s2i-python-container/issues/190
"""


import sys
import logging
from flask import Flask, request
from subprocess import check_output


app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)


@app.route("/gitlab-forward", methods=["GET", "POST"])
def gitlab_forwarder():
    """Handle an incoming POST from github, do something to gitlab"""
    app.logger.info(request)
    request_json = request.get_json()
    app.logger.info(request_json)
    if request_json is None:
        return 'Doing nothing'

    # First figure out what the action was - since it's a Pull Request it could
    # be opened, closed, reopened, commented, labeled, etc
    action = request_json.get("action", None)
    if action is None:
        return 'Doing nothing'

    should_run_actions = ["opened", "reopened", "labeled"]
    if action not in should_run_actions:
        return 'Doing nothing'

    # We only want to trigger a build on specific labels
    if action == "labeled":
        # Get label added
        new_label = request_json["label"]["name"]
        app.logger.info("Added label %s" % new_label)
        # Only carry on if the label is what we wanted
        if new_label not in ['PleaseTest']:
            return 'Doing nothing'

    # Get pertinent info from the PR that we need - number, how to merge it, etc
    pr_num = request_json["number"]
    base_branch = request_json["pull_request"]["base"]["ref"]
    proposer = request_json["pull_request"]["user"]["login"]
    app.logger.info("Handling PR %d from %s, to merge into branch %s. PR was %s." % (pr_num, proposer, base_branch, action))

    # Now run the script that pushes a new branch to gitlab for this PR.
    # This will then trigger gitlab-ci to run on the new branch
    app.logger.info("Pushing to gitlab")
    check_output(['./testPR.sh', str(pr_num), base_branch])

    return 'Forwarding to gitlab'


@app.route('/')
def index():
    return "Hello. This is your new app."


if __name__ == '__main__':
    app.run()