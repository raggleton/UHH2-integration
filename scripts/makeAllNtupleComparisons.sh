#!/usr/bin/env bash

# Do Ntuple comparisons from all ROOT files present, comparing old & new

for newfile in ${TESTDIR}/Ntuple*_new.root;
do
    echo $newfile
    reffile=${newfile/_new.root/_ref.root}
    if [ -f "$reffile" ]; then
        # Get sample name from filename
        name=$(basename "$newfile")
        name=${name/Ntuple_/}
        name=${name/_new.root/}
        python ${CI_PROJECT_DIR}/scripts/plotCompareNtuples.py "$newfile" --compareTo "$reffile" --json "${name}.json" --outputDir "plots_${name}" --fmt pdf --thumbnails
    else
        echo "Cannot find matching file $reffile"
    fi
done
