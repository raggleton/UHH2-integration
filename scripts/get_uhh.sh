#!/usr/bin/env bash
set -e
set -x # Print command before executing it - easier for looking at logs
set -u # Don't allow use of unset variables

# Get the desired version of UHH2 code from the PR

mkdir UHH2
cd UHH2
git init
git remote add UHH https://github.com/${REMOTENAME}/UHH2.git
git fetch UHH ${REMOTEBRANCH}:${LOCALBRANCH}
git checkout ${LOCALBRANCH}

# Get the diff for later analysis
# FIXME: broken if the user isn't testing a PR
wget -O PR.diff https://patch-diff.githubusercontent.com/raw/UHH2/UHH2/pull/${PRNUM}.diff

set +u