#!/usr/bin/env bash

# Do Ntuple comparisons table using all plot json files

REPORTFILE="ntuple_report.md"
rm -f "$REPORTFILE"

args=""
for plotfile in ${TESTDIR}/plot*.json;
do
    echo $plotfile
    # Get sample name from filename
    name=$(basename "$plotfile")
    name=${name/plots_/}
    name=${name/.json/}
    args="$args --json ${plotfile} --label ${name}"
done
echo "args: $args"
${CI_PROJECT_DIR}/scripts/makeNtupleComparisonTable.py $args >> "$REPORTFILE"