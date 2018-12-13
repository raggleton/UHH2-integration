#!/usr/bin/env bash

# Assemble grand timing markdown table, using only those matching _ref and _new JSONs
# Execute in UHH2-integration dir

firstline=true

TIMINGFILE="timing_report.md"
rm -f "$TIMINGFILE"
touch "$TIMINGFILE"  # ensures we have a file for future scripts

for newfile in ${TESTDIR}/timing*_new.json;
do
    reffile=${newfile/_new.json/_ref.json}
    if [ -f "$reffile" ]; then
        # Get sample name from filename
        name=$(basename "$newfile")
        name=${name/timing_/}
        name=${name/_new.json/}
        #nn#ame=${name//_/ }
        headeropt=""
        if [ "$firstline" == true ]; then headeropt="--header"; firstline=false; fi
        ${CI_PROJECT_DIR}/scripts/timingJsonTable.py  --ref "$reffile" --new "$newfile" --name "$name" $headeropt >> "$TIMINGFILE"
    fi
done