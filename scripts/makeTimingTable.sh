#!/usr/bin/env bash

# Assemble grand timing markdown table, using only those matching _ref and _new JSONs
# Execute in UHH2-integration dir

firstline=true

TIMINGFILE="timing_report.md"
rm -f "$TIMINGFILE"

for newfile in timing*_new.json;
do
    reffile=${newfile/_new/_ref}
    if [ -f "$reffile" ]; then
        # Get sample name from filename
        name=${newfile/timing_/}
        name=${name/_new.json/}
        name=${name//_/ }
        headeropt=""
        if [ "$firstline" == true ]; then headeropt="--header"; firstline=false; fi
        scripts/timingJsonTable.py  --ref "$reffile" --new "$newfile" --name "$name" "$headeropt" >> "$TIMINGFILE"
    fi
done