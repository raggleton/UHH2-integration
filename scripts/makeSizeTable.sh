#!/usr/bin/env bash

# Assemble grand size markdown table, using only those matching size*_ref and size*_new JSONs
# Execute in UHH2-integration dir

firstline=true

SIZEFILE="size_report.md"
rm -f "$SIZEFILE"
touch "$SIZEFILE"  # ensures we have a file for future scripts

for newfile in ${TESTDIR}/size*_new.json;
do
    reffile=${newfile/_new.json/_ref.json}
    if [ -f "$reffile" ]; then
        # Get sample name from filename
        name=$(basename "$newfile")
        name=${name/size_/}
        name=${name/_new.json/}
        # name=${name//_/ }  # don't use spaces...seems to cause issues later on passing arg, but only on runner
        headeropt=""
        if [ "$firstline" == true ]; then headeropt="--header"; firstline=false; fi
        # Dont use double quotes on headeropt, otherwise runner seems to interpret it badly
        ${CI_PROJECT_DIR}/scripts/sizeJsonTable.py  --ref "$reffile" --new "$newfile" --name "$name" $headeropt >> "$SIZEFILE"
    fi
done