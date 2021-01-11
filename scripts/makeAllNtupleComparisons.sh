#!/usr/bin/env bash

# Do Ntuple comparisons from all ROOT files present, comparing old & new
# Uses JSON data as extracted by dumpNtuple.py

for newfile in ${TESTDIR}/data*_new.awkd;
do
    echo $newfile
    reffile=${newfile/_new/_ref}
    # Get sample name from filename
    name=$(basename "$newfile")
    name=${name/data_/}
    name=${name/_new.awkd/}
    if [ -f "$reffile" ]; then
        time python ${CI_PROJECT_DIR}/scripts/compareTreeDumps.py "$newfile" --compareTo "$reffile" --json "plots_${name}.json" --outputDir "plots_${name}" --fmt pdf --thumbnails
    else
        echo "Cannot find matching file $reffile"
        time python ${CI_PROJECT_DIR}/scripts/compareTreeDumps.py "$newfile" --json "plots_${name}.json" --outputDir "plots_${name}" --fmt pdf --thumbnails
    fi
done
