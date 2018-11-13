#!/user/bin/env bash

set +x  # Otherwise our token will get exposed!

# Remove a label to a Github Pull Request
# Requires the following envvars to be set:
# - GITHUB_TOKEN
# - PRID
#
# The token must be for a user with push access to the repo
#
# Usage:
# ./add_label.sh "Blah blah blah"

# Have to use v3 API as v4 doesn't have it (wtf?)
# Note that we have to replace all space in the label string with %20
curl -H "Authorization: token ${GITHUB_TOKEN}" -X DELETE "https://api.github.com/repos/UHH2/UHH2/issues/${PRNUM}/labels/${1// /%20}" -s -o /dev/null
