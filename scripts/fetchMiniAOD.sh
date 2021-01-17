#!/usr/bin/env bash

# Fetch miniaod from service account cernbox/EOS
# Assumes file is stored as just basename
# Copy files over beforehand using generateXrdcpCmds.py
# 
# Requires you to have a kerberos token already, see kinit.sh,
# Also requries setting EOS_ACCOUNT_USERNAME as secure variable
# 

set +x  # Make sure no variables visible
# set -e  # Quit on error

${CI_PROJECT_DIR}/scripts/kinit.sh
echo "filename: $1"
BNAME=$(basename "$1")
time xrdcp --nopbar -f --retry 3 "root://eosuser.cern.ch//eos/project/${EOS_ACCOUNT_USERNAME:0:1}/${EOS_ACCOUNT_USERNAME}/UHH2MiniAOD/${BNAME}" "${BNAME}"
