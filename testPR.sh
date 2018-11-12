#!/usr/bin/env bash
#
# Test a PR by automatically updating to_test.sh
# then adding, committing, and pushing
# 
# Usage:
# ./testPR.sh <PR NUMBER> <REFBRANCH> <PRID>
# 
# PRID is optional, it will get updated in the CI job if it doesn't exist

PULLNUM="$1"
REFBRANCH="$2"
PRID="$3"

NEWBRANCH="test${PULLNUM}"
git checkout -b "${NEWBRANCH}" master
NEWFILE="scripts/to_test.sh"
echo "export PRNUM=${PULLNUM}" >> "${NEWFILE}"
echo "export REFBRANCH=${REFBRANCH}" >> "${NEWFILE}"
echo "export REMOTEBRANCH=pull/${PULLNUM}/head" >> "${NEWFILE}"
echo "export LOCALBRANCH=${NEWBRANCH}" >> "${NEWFILE}"
echo "export PRID=${PRID}" >> "${NEWFILE}"
git add "${NEWFILE}"
git commit -m "Test PR ${PULLNUM}"
git push -f origin "${NEWBRANCH}"  # use force push to overwrite existing branch
echo "Pushed to origin/${NEWBRANCH}"
git checkout master
