#!/usr/bin/env bash
#
# Test a PR by automatically updating .gitlab-ci.yml
# then adding, committing, and pushing
# 
# Usage:
# ./testPR.sh <PR NUMBER> <REFBRANCH> <PRID>
# 
# PRID is optional, it will get updated in the CI job if it doesn't exist

set -x # help debugging by printing commands, watch out if you use secrets!

PULLNUM="$1"
REFBRANCH="$2"
PRID="$3"

NEWBRANCH="test${PULLNUM}"
git checkout master
# If local branch already exists, delete it and do it again
git branch -D "${NEWBRANCH}"
# git rev-parse --quiet --verify "${NEWBRANCH}" || git branch -d "${NEWBRANCH}"
git checkout -b "${NEWBRANCH}" master

REPLACESTR="#@TESTVARS@"

CONTENTS="  PRNUM: \"${PULLNUM}\"\n"
CONTENTS="$CONTENTS  REFBRANCH: \"${REFBRANCH}\"\n"
CONTENTS="$CONTENTS  REMOTEBRANCH: \"pull/${PULLNUM}/head\"\n"
CONTENTS="$CONTENTS  LOCALBRANCH: \"${NEWBRANCH}\"\n"
CONTENTS="$CONTENTS  PRID: \"${PRID}\"\n"
CONTENTS="$CONTENTS$REPLACESTR\n"  # add REPLACESTR back on for any future replacements

# Only work with gnu sed, be careful on mac
sed -i -e "s|${REPLACESTR}|${CONTENTS}|g" .gitlab-ci.yml

git add ".gitlab-ci.yml"
git commit -m "Test PR ${PULLNUM}"
git push -f origin "${NEWBRANCH}"  # use force push to overwrite existing branch
echo "Pushed to origin/${NEWBRANCH}"
git checkout master

set +x