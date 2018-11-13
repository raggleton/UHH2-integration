#!/usr/bin/env bash
set -e
set -x # Print command before executing it - easier for looking at logs
set -u # Don't allow use of unset variables

# Get the desired versions of UHH2 code, the reference version 
# and the user's modified version
UHHDIR="UHH2"
mkdir "$UHHDIR"
cd "$UHHDIR"
git init
git remote add UHHREF https://github.com/UHH2/UHH2.git
git fetch -u UHHREF ${REFBRANCH}:${REFBRANCH}  # need the -u for master
git checkout ${REFBRANCH}

git fetch UHHREF ${REMOTEBRANCH}:${LOCALBRANCH}
git checkout ${LOCALBRANCH}
git diff ${REFBRANCH}..HEAD > PR.diff
# Replicate PR - merge changes into reference branch
# Don't want this if not a PR?
git merge -m "Merge PR ${PRNUM}" ${REFBRANCH}
cd ..

set +u