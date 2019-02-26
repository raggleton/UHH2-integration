#!/usr/bin/env bash
#
# Do comparison plots, & compile all analysis info into webpage

args=""
for newfile in ${TESTDIR}/Ntuple*_new.root;
do
    echo $newfile
    # Get sample name from filename
    name=$(basename "$newfile")
    name=${name/Ntuple_/}
    name=${name/_new.root/}

    reffile=${newfile/_new.root/_ref.root}
    if [ !-f "$reffile" ]; then
        # Horrible hack - incase of no ref file, copy the new file as ref
        echo "Cannot find matching file $reffile, copying new ones as ref"
        cp timing_${name}_new.json timing_${name}_ref.json
        cp size_${name}_new.json size_${name}_ref.json
    fi
    args="$args --plotjson plots_${name}.json --plotdir plots_${name} \
                --timingrefjson timing_${name}_ref.json --timingnewjson timing_${name}_new.json \
                --sizerefjson size_${name}_ref.json --sizenewjson size_${name}_new.json \
                --label ${name}"
done
echo "args: "$args

# Need to put website contents in directory "public"
export WEBEND="UHH2integration/${LOCALBRANCH}"
ODIR=${CI_PROJECT_DIR}/public/${WEBEND}
mkdir -p $ODIR
python ${CI_PROJECT_DIR}/scripts/makeWebpage.py --outputDir "$ODIR" $args
