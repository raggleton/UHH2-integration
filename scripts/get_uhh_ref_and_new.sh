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
git fetch UHHREF ${REFBRANCH}:${REFBRANCH}
git checkout ${REFBRANCH}

git remote add UHHNEW https://github.com/${REMOTENAME}/UHH2.git
git fetch UHHNEW ${REMOTEBRANCH}:${LOCALBRANCH}
git checkout ${LOCALBRANCH}
git diff ${REFBRANCH}..HEAD > PR.diff
cd ..

set +u