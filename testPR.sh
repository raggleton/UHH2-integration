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

NEWBRANCH="test$PULLNUM"
git checkout -b $NEWBRANCH master
sed -i .bak -E "s/export PRNUM=[0-9]*/export PRNUM=$PULLNUM/" to_test.sh
sed -i .bak -E "s/export REFBRANCH=\".*\"/export REFBRANCH=\"$REFBRANCH\"/" to_test.sh
git add to_test.sh
git commit -m "Test PR $PULLNUM"
git push origin $NEWBRANCH
echo "Pushed to origin/$NEWBRANCH"
