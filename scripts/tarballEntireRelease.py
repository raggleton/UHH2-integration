#!/usr/bin/env python

"""Script to create a tarball from one or all of:

- CMSSW environment
- SFrame

To deploy, use the produced deploy script: e.g `source deploy_all.sh`
This should be done BEFORE untarring, since there are steps to do before untarring.

Used to pass between Gitlab CI jobs (or just to deploy your setup elsewhere)
We don't need to tar up fastjet as the libs should already be installed in CMSSW_*

Returns 0 if successful and below file size limit, 1 otherwise.
"""


from  __future__ import division   # make division work like in python3

import os
import sys
from glob import glob
import logging
import argparse
import tarfile


logger = logging.getLogger("TARBALL")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


# Borrowed heavily from:
# https://github.com/dmwm/CRABClient/blob/master/src/python/CRABClient/JobType/UserTarball.py

def generate_deploy_script(script_kwargs, do_cmssw=True, do_sframe=True):
    script_lines = [
        "#!/usr/bin/env bash",
        "#"
        "# You MUST run this as: source <filename>",
        "# Otherwise the setup will not happen in your current shell"
        "export SCRAM_ARCH={scram_arch}",
        "shopt -s expand_aliases"
        "source /cvmfs/cms.cern.ch/cmsset_default.sh"
    ]
    if do_cmssw:
        script_lines.extend([
            "cmsrel {cmssw_ver}",
            "cd {cmssw_ver}/src",
            "eval `scramv1 runtime -sh`", # as cmsenv behaves weirdly in a script
            "cd ../..",
            "tar xvzf {tar_filename}",
        ])
    if do_sframe:
        script_lines.extend([
            '[ -z "$CMSSW_BASE" ] && echo "You must setup a CMSSW area first" && false',
            "cd SFrame",
            "source setup.sh",
            "cd ..",
        ])
    contents = '\n'.join(script_lines)
    contents = contents.format(**script_kwargs)
    return contents


def check_directory(dir_):
    """Checking for infinite symbolic link loop"""
    try:
        for root , _ , files in os.walk(dir_, followlinks = True):
            for file_ in files:
                os.stat(os.path.join(root, file_ ))
    except OSError as msg:
        err = 'Error: Infinite directory loop found in: %s \nStderr: %s' % (dir_ , msg)
        raise EnvironmentException(err)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a tarball from current CMSSW/SFrame setup.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--output", "-o",
                        help="Output tarball filename",
                        default="testTarball.tgz")
    parser.add_argument("--contents",
                        choices=['all', 'cmssw', 'sframe'],
                        help="Choose which part to store",
                        default='all')
    args = parser.parse_args()

    start_dir = os.getcwd()

    # start at the top
    CMSSW_BASE = os.environ.get('CMSSW_BASE', None)
    if CMSSW_BASE is None:
        raise RuntimeError("CMSSW_BASE is not set, have you done cmsenv?")
    CMSSW_VERSION = os.environ['CMSSW_VERSION']

    tar_filename = os.path.abspath(args.output)

    top_dir = os.path.dirname(CMSSW_BASE)
    os.chdir(top_dir)

    # dereference is VITAL otherwise symlinks to actual locations on disk
    tarfile = tarfile.open(name=tar_filename, mode='w:gz', dereference=True)

    do_cmssw = args.contents in ['all', 'cmssw']

    if do_cmssw:
        add_python = True  # has UHH2 ntuple configs
        add_external = True  # has fastjet libs
        add_examples = True  # add UHH2 sframe example analyses
        # We do not include .SCRAM dir, even though it makes scram think it's a valid CMSSW setup.
        # It will setup env vars to point to the location of the original CMSSW installation,
        # which we don't want.
        # Instead we do cmsrel, then overwrite the directories using the ones in the tarball.
        directories = ['lib', 'biglib', 'module']
        if add_python:
            directories.extend(['python', 'cfipython'])
        if add_external:
            directories.append('external')
        if add_examples:
            directories.append('src/UHH2/examples/config')

        for directory in directories:
            full_path = os.path.join(CMSSW_BASE, directory)
            logger.debug("Checking directory %s" % full_path)
            if os.path.exists(full_path):
                logger.debug("Adding directory %s to tarball" % full_path)
                check_directory(full_path)
                tarfile.add(full_path, os.path.join(CMSSW_VERSION, directory), recursive=True)

        # Note that data_dirs are only looked-for and added under the src/ folder.
        # /data/ subdirs contain data files needed by the code
        # /interface/ subdirs contain C++ header files needed e.g. by ROOT6
        data_dirs = ['data', 'interface']

        # Search for and tar up "data" directories in src/
        src_path = os.path.join(CMSSW_BASE, 'src')
        for root, _, _ in os.walk(src_path):
            if os.path.basename(root) in data_dirs:
                directory = root.replace(CMSSW_BASE, CMSSW_VERSION)
                logger.debug("Adding data directory %s to tarball" % root)
                check_directory(root)
                tarfile.add(root, directory, recursive=True)

    do_sframe = args.contents in ['all', 'sframe']

    if do_sframe:
        sframe_dirs = ['bin', 'lib', 'setup.sh'] # 'core/include'
        for directory in sframe_dirs:
            full_path = os.path.join(top_dir, 'SFrame', directory)
            if os.path.exists(full_path):
                logger.debug("Adding directory %s to tarball" % full_path)
                check_directory(full_path)
                tarfile.add(full_path, os.path.join('SFrame', directory), recursive=True)

    tarfile.close()
    logger.debug("Created tarball %s", tar_filename)

    # Create script to help deployment
    script_kwargs = {
        'tar_filename': os.path.basename(tar_filename),
        'scram_arch': os.environ['SCRAM_ARCH'],
        'cmssw_ver': CMSSW_VERSION,
    }

    deploy_script_contents = generate_deploy_script(script_kwargs,
                                                    do_cmssw=do_cmssw,
                                                    do_sframe=do_sframe)

    deploy_script = os.path.join(os.path.dirname(tar_filename), 'deploy_script_%s.sh' % (os.path.splitext(script_kwargs['tar_filename'])[0]))
    with open(deploy_script, 'w') as f:
        logger.debug("Creating deploy script %s" % deploy_script)
        f.write(deploy_script_contents)
        f.write('\n')
    os.chmod(deploy_script, 0o755)  # make executable

    # Check size
    size_bytes = os.path.getsize(tar_filename)
    # in python3 and python2 with __future__ division, // means integer division
    size_mb = "%3.1f MB" % (size_bytes // (1024 * 1024))
    file_size_limit = (100-3)*1024*1024  # 100MB, with some padding for safety/alert
    limit_mb = "%3.1f MB" % (file_size_limit // (1024 * 1024))

    if size_bytes >= file_size_limit:
        logger.error(("Error: tarball size %s exceeds the limit of %s. "
                      "Consider splitting into separate CMSSW & SFrame tarballs" % (size_mb, limit_mb)))
        sys.exit(1)
    else:
        logger.info("Success: tarball size %s is below limit of %s" % (size_mb, limit_mb))


    sys.exit(0)

