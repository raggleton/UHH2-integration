#!/usr/bin/env bash

# Fetch miniaod from my cernbox/eos
# Assumes file is stored as just basename 
# 
# Requires you to have a kerberos token already, see kinit.sh,
# Also requries setting EOS_USERNAME as secure variable
# 

set +x  # Make sure no variables visible
set -e  # Quit on error

BNAME=$(basename "$1")
xrdcp --nopbar -f --retry 3 "root://eosuser.cern.ch//eos/user/r/${EOS_USERNAME}/UHH2MiniAOD/${BNAME}" "${BNAME}"
