#!/usr/bin/env bash
set -e
set -x # Print command before executing it - easier for looking at logs
set -u # Don't allow use of unset variables

# Run after the install script to copy the version of UHH2 under test,
# and to compile everything
echo "Doing post_install"

# In install.sh we clone the main branch, but on CI we want to test the PR of interest
# So we need to remove the UHH2 inside CMSSW and copy our one over from $WORKDIR/UHH2
# (which got cloned by gitlab at the start of the job)
# Copy not move as could still need to reference scripts etc from the yaml
cd ${CMSSW_BASE}/src
mv ${CMSSW_BASE}/src/UHH2/JECDatabase $WORKDIR/UHH2/
rm -rf "${CMSSW_BASE}/src/UHH2"
cp -r $WORKDIR/UHH2 ${CMSSW_BASE}/src
ls ${CMSSW_BASE}/src
if [ ! -d "${CMSSW_BASE}/src/UHH2" ];
then
    echo "Cannot find UHH2 dir, replacement failed"
    exit 1
fi

# Compile SFrame and UHH
cd ${CMSSW_BASE}/../SFrame
source setup.sh
time make $MAKEFLAGS
cd ${CMSSW_BASE}/src/UHH2
time make $MAKEFLAGS

# Hack to make cmsRun work on the images as no default site set
export CMS_PATH=/cvmfs/cms-ib.cern.ch/

set +u