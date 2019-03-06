#!/usr/bin/env bash
set -e
set -x # Print command before executing it - easier for looking at logs

# Info about machine
ulimit -a

# Compile SFrame and UHH
cd ${CMSSW_BASE}/../SFrame
source setup.sh
which time
time make ${MAKEFLAGS}
cd ${CMSSW_BASE}/src/UHH2
time make ${MAKEFLAGS}

# Hack to make cmsRun work on the images as no default site set
export CMS_PATH=/cvmfs/cms-ib.cern.ch/
