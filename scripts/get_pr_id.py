#!/usr/bin/env python


"""
Get the Github Pull Request unique ID.
Needed for posting comments, etc

Can also apend to a file as a bash variable
"""


from __future__ import print_function
import os
import sys
import json
import optparse  # can't use argparse as python2.6 default on worker nodes
try:
    # python2
    from urllib2 import Request
    from urllib2 import urlopen
except ImportError:
    # python3
    from urllib.request import Request
    from urllib.request import urlopen


parser = optparse.OptionParser()
parser.add_option('--id',
                  help="Pull Request ID",
                  type="int")
parser.add_option('--dumpFilename',
                  help="Filename to dump PR ID into",
                  type="str")
parser.add_option('--dumpVarname',
                  help="Variable name to set as PR ID",
                  type="str",
                  default="PRID")
options, args = parser.parse_args()

query = """
{
    repository(
        owner: "UHH2",
        name: "UHH2"
    ) {
        pullRequest(number: %d) {
            id
        }
    }
}
""" % (options.id)

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', None)
if not GITHUB_TOKEN:
    raise RuntimeError("No github token, cannot make API requests")
headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization' : 'bearer %s' % GITHUB_TOKEN}
blob = json.dumps(dict(query=query.strip())).encode('utf-8')
this_request = Request("https://api.github.com/graphql", blob, headers)
response = urlopen(this_request)
data = json.loads(response.read().decode('utf-8'))
pr = data['data']['repository']['pullRequest']
if pr:
    pr_id = pr['id']
    print(pr_id)
    if options.dumpFilename != "":
        with open(options.dumpFilename, "a") as f:
            f.write("export %s=%s\n" % (options.dumpVarname, pr_id))
else:
    print("No Pull Request number %d" % options.id)
