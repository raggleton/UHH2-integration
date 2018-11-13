#!/user/bin/env bash

set +x  # Otherwise our token will get exposed!

# Add a label to a Github Pull Request
# Requires the following envvars to be set:
# - GITHUB_TOKEN
# - PRID
#
# The token must be for a user with push access to the repo
#
# Usage:
# ./add_label.sh "Blah blah blah"

# Have to use v3 API as v4 doesn't have it (wtf?)
curl -H "Authorization: token ${GITHUB_TOKEN}" -X POST -d "[\"$1\"]" "https://api.github.com/repos/UHH2/UHH2/issues/${PRNUM}/labels" -s -o /dev/null
