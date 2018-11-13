#!/usr/bin/env bash

set +x  # Otherwise our token will get exposed!

# Pre-defined things to post to github
#
# Usage:
# ./notify_github.sh <keyword> <optional message>

PASS_LABEL="Passed"
FAIL_LABEL="Failed"

case $1 in
start)
    source ${CI_PROJECT_DIR}/scripts/post_comment.sh "Starting setup & tests, see ${CI_PIPELINE_URL}"
    source ${CI_PROJECT_DIR}/scripts/remove_label.sh "PleaseTest"
    source ${CI_PROJECT_DIR}/scripts/remove_label.sh "${PASS_LABEL}"
    source ${CI_PROJECT_DIR}/scripts/remove_label.sh "${FAIL_LABEL}"
    ;;
passed)
    source ${CI_PROJECT_DIR}/scripts/add_label.sh "${PASS_LABEL}"
    COMMENT="$2"
    [ -z "$COMMENT" ] && COMMENT="Passed pipeline"
    source ${CI_PROJECT_DIR}/scripts/post_comment.sh "${COMMENT}"
    ;;
failed)
    source ${CI_PROJECT_DIR}/scripts/add_label.sh "${FAIL_LABEL}"
    COMMENT="$2"
    [ -z "$COMMENT" ] && COMMENT="Failed pipeline"
    source ${CI_PROJECT_DIR}/scripts/post_comment.sh "${COMMENT}"
    ;;
*)
    exit 1;
esac;