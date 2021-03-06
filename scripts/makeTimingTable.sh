#!/usr/bin/env bash

# Assemble grand timing markdown table, using only those matching timing*_ref and timing*_new JSONs
# Execute in UHH2-integration dir

firstline=true

TIMINGFILE="timing_report.md"
rm -f "$TIMINGFILE"
touch "$TIMINGFILE"  # ensures we have a file for future scripts

for newfile in ${TESTDIR}/timing*_new.json;
do
    reffile=${newfile/_new.json/_ref.json}
    if [ ! -f "$reffile" ]; then
        # horrible hack to get it working in the event of no reffile
        echo "Copying new file as ref"
        cp "$newfile" "$reffile"
    fi
    # Get sample name from filename
    name=$(basename "$newfile")
    name=${name/timing_/}
    name=${name/_new.json/}
    # name=${name//_/ }  # don't use spaces...seems to cause issues later on passing arg, but only on runner
    headeropt=""
    if [ "$firstline" == true ]; then headeropt="--header"; firstline=false; fi
    # Dont use double quotes on headeropt, otherwise runner seems to interpret it badly
    ${CI_PROJECT_DIR}/scripts/timingJsonTable.py  --ref "$reffile" --new "$newfile" --name "$name" $headeropt >> "$TIMINGFILE"
done
