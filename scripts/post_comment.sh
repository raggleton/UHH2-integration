#!/user/bin/env bash

set +x  # Otherwise our token will get exposed!
set +u  # Below tests might fail otherwise

# Post a comment to Github
# Requires the following envvars to be set:
# - GITHUB_TOKEN
# - PRID
#
# Setting GITHUB_QUIET=1 will not send any comments to github.
# To post, unset or set to 0
#
# Usage:
# ./post_comment.sh "Blah blah blah"

if [ -n "$GITHUB_QUIET" ] && [ "$GITHUB_QUIET" -ne 0 ]
then
    # don't post
    return 0
else
    QUERY="mutation { addComment(input: { subjectId: \\\"${PRID}\\\", clientMutationId: \\\"integration-test\\\", body: \\\"${1}\\\"}) { clientMutationId } }"
    curl -H "Authorization: bearer ${GITHUB_TOKEN}" -X POST -d "{ \"query\":\"$QUERY\"}" https://api.github.com/graphql -s -o /dev/null
fi