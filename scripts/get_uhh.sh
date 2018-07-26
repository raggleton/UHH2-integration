#!/usr/bin/env bash
set -e
set -x # Print command before executing it - easier for looking at logs
set -u # Don't allow use of unset variables

# Get the desired version of UHH2 code from the PR

mkdir UHH2
cd UHH2
git init
git remote add UHH https://github.com/UHH2/UHH2.git
git fetch UHH pull/${PRNUM}/head:${PRBRANCH}
git checkout ${PRBRANCH}

set +u