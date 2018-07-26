#!/usr/bin/env bash

# This script is run before install script to ensure vars set, etc
# It is designed to be run one dir above UHH2

set -e
set -x # Print command before executing it - easier for looking at logs
# CRUCIAL for cmsrel, etc as aliases not expanded in non-interactive shells
shopt -s expand_aliases


setGitSetting() {
    # Check if git config setting is blank, if so set it to a value
    # args: <setting name> <new value>
    settingName="$1"
    newValue="$2"
    # the || true is vital as will return 1 if empty and fail otherwise
    ans=$(git config --global "$settingName" || true)
    if [ -z "$ans" ]
    then
        echo "git $settingName not set - setting it to $newValue"
        git config --global "$settingName" "$newValue"
    fi
}


echo "Doing pre_install"

ls -lh

# Check CVMSFS
ls -1 /cvmfs/cms.cern.ch/

# Store top location
export WORKDIR=$(pwd)

export CMSSW_GIT_REFERENCE=$WORKDIR/cmssw.git

# Necessary for cms-init or addpkg
setGitSetting "user.name" "Jim Hopper"
setGitSetting "user.email" "jane@ives.com"
setGitSetting "user.github" "testUHH"

