#!/usr/bin/env bash

# Do Ntuple comparisons & make table from all ROOT files present,
# comparing old & new

REPORTFILE="ntuple_report.md"
rm -f "$REPORTFILE"

args=""
for newfile in ${TESTDIR}/Ntuple*_new.root;
do
    echo $newfile
    reffile=${newfile/_new.root/_ref.root}
    if [ -f "$reffile" ]; then
        # Get sample name from filename
        name=$(basename "$newfile")
        name=${name/Ntuple_/}
        name=${name/_new.root/}
        python ${TESTDIR}/plotCompareNtuples.py "$newfile" --compareTo "$reffile" --json "${name}.json" --outputDir "plots_${name}" --fmt png
        args="$args --json plots_${name}.json --label ${name}"
    else
        echo "Cannot find matching file $reffile"
    fi
done
echo "args: $args"
${CI_PROJECT_DIR}/scripts/makeNtupleComparisonTable.py $args >> "$REPORTFILE"