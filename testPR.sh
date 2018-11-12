#!/usr/bin/env bash
#
# Test a PR by automatically updating to_test.sh
# then adding, committing, and pushing
# 
# Usage:
# ./testPR.sh <PR NUMBER> <REFBRANCH>
# 

PULLNUM="$1"
REFBRANCH="$2"

NEWBRANCH="test${PULLNUM}"
git checkout -b "${NEWBRANCH}" master
echo "export PRNUM=${PULLNUM}" >> to_test.sh
echo "export REFBRANCH=${REFBRANCH}" >> to_test.sh
echo "export REMOTEBRANCH=pull/${PULLNUM}/head" >> to_test.sh
echo "export LOCALBRANCH=${NEWBRANCH}" >> to_test.sh
git add to_test.sh
git commit -m "Test PR ${PULLNUM}"
git push -f origin "${NEWBRANCH}"  # use force push to overwrite existing branch
echo "Pushed to origin/${NEWBRANCH}"
git checkout master
