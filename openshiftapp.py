#!/usr/bin/env python

"""App to listen for github events, and carry out a corresponding task e.g. push to gitlab

NB if you rename this file to `app.py` in the future, you'll need to set 
`APP_FILE` in openshift to null otherwise it'll run this instead of gunicorn:
https://github.com/sclorg/s2i-python-container/issues/190
"""


import sys
import logging
from flask import Flask, request


app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)


@app.route("/gitlab-forward", methods=["GET", "POST"])
def gitlab_forwarder():
    """Handle an incoming POST from github, do something to gitlab"""
    app.logger.info(request)
    app.logger.info(request.get_json())
    return 'Forwarding'


@app.route('/')
def index():
    return "Hello. This is your app."


if __name__ == '__main__':
    app.run()