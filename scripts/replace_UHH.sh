#!/usr/bin/env bash
set -e
set -x # Print command before executing it - easier for looking at logs

# Run after the install script to copy the version of UHH2 under test,
echo "Doing replace_UHH"

# In install.sh we clone the main branch, but on CI we want to test the PR of interest
# So we need to remove the UHH2 inside CMSSW and copy our one over from $CI_PROJECT_DIR/UHH2
# (which got cloned by gitlab at the start of the job)
# Copy not move as could still need to reference scripts etc from the yaml
cd ${CMSSW_BASE}/src
mv ${CMSSW_BASE}/src/UHH2/JECDatabase ${CI_PROJECT_DIR}/UHH2/
rm -rf "${CMSSW_BASE}/src/UHH2"
cp -r ${CI_PROJECT_DIR}/UHH2 ${CMSSW_BASE}/src
ls ${CMSSW_BASE}/src
if [ ! -d "${CMSSW_BASE}/src/UHH2" ];
then
    echo "Cannot find UHH2 dir, replacement failed"
    exit 1
fi
