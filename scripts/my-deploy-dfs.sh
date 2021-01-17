#!/bin/bash

# This is a replacement for the standard deploy-dfs,
# to allow me to do post-transfer checks (since sometimes it fails)
# Mostly a copy of https://gitlab.cern.ch/ci-tools/ci-web-deployer/-/blob/master/bin/deploy-dfs

set -e

# April 2016 Borja Aparicio
# Receives:
# Environment variables
#   DFS_WEBSITE_USERNAME
#   DFS_WEBSITE_PASSWORD
#   CI_WEBSITE_DIR => default: public/
#   DFS_WEBSITE_NAME
#   DFS_WEBSITE_PATH
#   SMB_PROTOCOL => default: smb3
#
# Produces:
#  Uploads to --dfs-website-path in DFS the files found in --source-dir

# SMBCLIENT present to connect to Windoes DFS filesystem
smbclient="/usr/bin/smbclient"
if [ ! -x $smbclient ]
then
    echo "ERROR: $smbclient not found"
    exit 1
fi

# Set smbclient protocol from input
smbclient="${smbclient} -m ${SMB_PROTOCOL:-smb3}"

# Authenticate user via Kerberos
kinit="/usr/bin/kinit"
if [ ! -x $kinit ]
then
    echo "ERROR: $kinit not found"
    exit 1
fi

kdestroy="/usr/bin/kdestroy"
if [ ! -x $kdestroy ]
then
    echo "ERROR: $kdestroy not found"
    exit 1
fi

# Validate input
#: "${DFS_WEBSITE_NAME:?DFS_WEBSITE_NAME not provided}"
: "${DFS_WEBSITE_USERNAME:?DFS_WEBSITE_USERNAME not provided}"
: "${DFS_WEBSITE_PASSWORD:?DFS_WEBSITE_PASSWORD not provided}"

# Protected or configuration files in DFS. Don't override or delete this with the deploy job
if [ -z "$DFS_PROTECTED_FILES" ];
then
    DFS_PROTECTED_FILES="web.config:robots.txt:Global.asax"
fi

# Directory where the web site has been generated in the CI environment
# If not provided by the user
if [ -z "$CI_WEBSITE_DIR" ];
then
    CI_WEBSITE_DIR="public/"
fi
# make it absolute path
CI_WEBSITE_DIR=$(pwd)/${CI_WEBSITE_DIR}

# Check the source directory exists
if [ ! -d "$CI_WEBSITE_DIR" ]
then
    echo "ERROR: Source directory '$CI_WEBSITE_DIR' doesn't exist"
    exit 1
fi

# Get credentials
echo "$DFS_WEBSITE_PASSWORD" | $kinit "$DFS_WEBSITE_USERNAME@CERN.CH" 2>&1 >/dev/null
if [ $? -ne 0 ]
then
    echo "Failed to get Krb5 credentials for '$DFS_WEBSITE_USERNAME'"
        exit 1
fi

# From the Website name, we build the path in DFS
# If DFS_WEBSITE_NAME is "test-gitlab-pages", DFS_WEBSITE_PATH is "\Websites\t\test-gitlab-pages"
# If a value is provided for DFS_WEBSITE_DIR (e.g. "mydir") then  DFS_WEBSITE_PATH becomes "\Websites\t\test-gitlab-pages\mydir"
# Get the first letter of the website
website_prefix=${DFS_WEBSITE_NAME:0:1}

# If the user provides the DFS_WEBSITE_PATH path, use it. Otherwise calculate it
if [ -z "$DFS_WEBSITE_PATH" ];
then
    : "${DFS_WEBSITE_NAME:?DFS_WEBSITE_NAME not provided}"
    DFS_WEBSITE_PATH="\Websites\\$website_prefix\\$DFS_WEBSITE_NAME\\$DFS_WEBSITE_DIR"
fi

# Check the target directory in DFS exists and the user has the needed permissions
$smbclient -k //cerndfs.cern.ch/dfs -c "cd $DFS_WEBSITE_PATH"
if [ $? -ne 0 ]
then
    echo "ERROR: Failed to access '//cerndfs.cern.ch/dfs/$DFS_WEBSITE_PATH'"
        exit 1
fi

# Copy the contents to the folder specified
$smbclient -k //cerndfs.cern.ch/dfs -c "lcd $CI_WEBSITE_DIR; cd $DFS_WEBSITE_PATH; recurse; prompt OFF; mask *; mput *"
if [ $? -ne 0 ]
then
    echo "ERROR: Failed to update '//cerndfs.cern.ch/dfs/$DFS_WEBSITE_PATH'"
       exit 1
fi

function checkCopyFiles {
    # This function iterates over all files in a directory, and for each
    # checks its existence on SMB mount, and its size. If it doesn't exist, or
    # has a mismatched size, then retry copying. Redo this until it matches, up
    # to a maximum of 5 times
    thisdir=$1  # should be relative to ${LOCALBRANCH}
    echo "$thisdir"
    set -u
    set +e  # allow errors, e.g. for not finding files
    # Get listing for this directory on DFS once
    # This avoids calling it for all files individually
    smbout=$($smbclient -k //cerndfs.cern.ch/dfs -c "cd ${DFS_WEBSITE_PATH}/${WEBDIR}/; ls $thisdir/*")
    echo "$smbout"
    for fname in "$thisdir"/*;
    do
        if [ ! -f "$fname" ]; then
            continue
        fi
        echo "Checking $fname"

        # get local size
        dusize=$(du -sb "$fname" | cut -f 1)

        # check remote file exists
        smbsize="-1"
        patternname=$(basename "$fname")  # strip off leading ./mc_2017_figs/ for example
        # echo "$smbout" | grep "$patternname"

        if ! echo "$smbout" | grep -q "$patternname" ; then
            echo "Missing $fname"
        else
            # get dfs size
            smbsize=$(echo "$smbout" | awk -v pat="$patternname" '$0~pat {print $3}')
        fi

        # copy until the sizes match
        counter=1
        while [ "$dusize" != "$smbsize" ]; do
            echo "Mismatch in sizes: $dusize vs $smbsize"
            echo "Trying to copy $fname again (# $counter)..."
            # mput ONLY works if you have the basename as the mask for mput
            # i.e. $fname won't work there
            # But it does work for ls
            $smbclient -k //cerndfs.cern.ch/dfs -c "lcd ${CI_WEBSITE_DIR}/${WEBDIR}/${thisdir}; cd ${DFS_WEBSITE_PATH}/${WEBDIR}/${thisdir}; recurse; prompt OFF; mask *; mput $patternname"
            smbsize=$($smbclient -k //cerndfs.cern.ch/dfs -c "ls ${DFS_WEBSITE_PATH}/${WEBDIR}/$fname" | awk -v pat="$patternname" '$0~pat {print $3}')
            (( counter++ ))
            if [ "$counter" -eq 6 ]; then
                echo "WARNING: couldn't copy $fname, tried 5 times"
                break
            fi
            sleep 1s  # be nice?
        done
    done
    set -e
    set +u
}

# New part: check that all the directories got copied correctly
# I wish I could do directory size check, or checksum, but no luck
cd "${CI_WEBSITE_DIR}/${WEBDIR}/"
# can't use -exec with function AND have bash vars
# ignore . as find will include it
find . ! -path . -type d -print0 | while IFS= read -r -d '' line;
do
    echo "$line"
    checkCopyFiles "$line"
done

# Destroy credentials
$kdestroy
if [ $? -ne 0 ]
then
    echo "Krb5 credentials for '$DFS_WEBSITE_USERNAME' have not been cleared up"
fi

#rm -rf temp

echo "Updated DFS web site in '$DFS_WEBSITE_PATH'"
exit 0
