#!/usr/bin/env bash

# Do Ntuple comparisons from all ROOT files present, comparing old & new
# Uses JSON data as extracted by dumpNtuple.py

for newfile in ${TESTDIR}/data*_new.json;
do
    echo $newfile
    reffile=${newfile/_new/_ref}
    if [ -f "$reffile" ]; then
        # Get sample name from filename
        name=$(basename "$newfile")
        name=${name/data_/}
        name=${name/_new.json/}
        python ${CI_PROJECT_DIR}/scripts/compareTreeDumps.py "$newfile" --compareTo "$reffile" --json "plots_${name}.json" --outputDir "plots_${name}" --fmt pdf --thumbnails
    else
        echo "Cannot find matching file $reffile"
    fi
done
