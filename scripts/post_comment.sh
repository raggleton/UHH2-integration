#!/user/bin/env bash
#
# Post a comment to Github
# Requires the following envvars to be set:
# - GITHUB_TOKEN
# - PRID
#
# Usage:
# ./post_comment.sh "Blah blah blah"
QUERY="mutation { addComment(input: { subjectId: \\\"${PRID}\\\", clientMutationId: \\\"integration-test\\\", body: \\\"${1}\\\"}) { clientMutationId } }"
curl -H "Authorization: bearer ${GITHUB_TOKEN}" -X POST -d "{ \"query\":\"$QUERY\"}" https://api.github.com/graphql -s -o /dev/null
