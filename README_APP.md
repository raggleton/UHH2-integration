# uhh2-paas-app

This is a simple Flask web app that runs on a server. It is simply to allow github and gitlab to communicate.

More specifically, it's only goal in life is to listen for new & updated pull requests on github,
then perform some task on a corresponding gitlab repository (making a commit to a new branch to test that PR).
The gitlab repository will then automatically trigger it's CI process.

## Technical overview

Github has webhooks; these send a HTTP POST request when an event occurs (e.g. a new PR is created).
This app will be continuing listening for such a request.

The application logic is handled by Flask.
The python WSGI HTTP Server is handled by gunicorn.
These are hosted on a CERN openshift page.

(Or that's the plan at least)


## Odds n ends

- By default the openshift sites are only visible **inside** the CERN network. To configure access to the widerInternet, see https://cern.service-now.com/service-portal/article.do?n=KB0004359

- If you have `app.py`, and you haven't set `APP_CONFIG`, then it will ruun that instead of gunicorn etc, Which is not what you want.

