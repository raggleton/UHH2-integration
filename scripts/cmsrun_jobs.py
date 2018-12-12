#!/usr/bin/env python

"""Do a cmsRun job, choosing from one of the pre-determined setups"""


import os
import sys
import argparse
import subprocess
from copy import deepcopy


NEVENTS = 2000

# Setup for all configs
# The first key must be a valid argument to the `year` arg in generate_process(),
# the nested key should then be "data" or "mc". These determine the config.
# For each you can then set the config & actual list of jobs that should be run
# i.e. input filename, # events, job name for each.
# The job name is used for output file and logs, thus should be unique and meaningful
#
# Maybe in the future this will get out of hand, and it should just be a flattened list,
# or a set of function calls
#
# Note that we assume the input file is in EOS (cernbox), see fetchMiniAOD.sh,
# thus you should copy xrdcp any files first to the EOS location
CONFIGS = {
    ######################
    # 2018 PromptReco MINIAOD
    ######################

    "2018": {
        "data": {
            "config": "ntuplewriter_data_2018.py",
            "jobs": [
                {
                    "name": "JetHT",
                    "inputfile": "/store/data/Run2018D/JetHT/MINIAOD/PromptReco-v2/000/325/170/00000/9494B803-292B-F343-9BCC-6CAD47CB0C8B.root",
                },
                {
                    "name": "SingleMu",
                    "inputfile": "/store/data/Run2018D/SingleMuon/MINIAOD/PromptReco-v2/000/321/233/00000/6C7B6F79-24A3-E811-A7BF-FA163EC61E98.root",
                },
                {
                    "name": "EGamma",  # for 2018 they changed SingleElectron to EGamma
                    "inputfile": "/store/data/Run2018D/EGamma/MINIAOD/PromptReco-v2/000/320/500/00000/CEC0AF98-F895-E811-919A-FA163EE8C7E8.root",
                },
            ]
        },
        "mc": {
            "config": "ntuplewriter_mc_2018.py",
            "jobs":[
                {
                    "name": "TTHadronic",
                    "inputfile": "/store/mc/RunIIAutumn18MiniAOD/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/MINIAODSIM/102X_upgrade2018_realistic_v15-v1/100000/2A6B8F74-04C7-1B46-A56E-8C786D0C2E84.root",
                },
                {
                    "name": "TTLeptonic",
                    "inputfile": "/store/mc/RunIIAutumn18MiniAOD/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/MINIAODSIM/102X_upgrade2018_realistic_v15-v1/110000/D774DA06-04F6-5E45-B02E-70ECD0DD697F.root",
                },
            ]
        }
    },

    ######################
    # 2018 MINIAOD
    ######################

    "2017": {
        "data": {
            "config": "ntuplewriter_data_2017.py",
            "jobs": [
                {
                    "name": "JetHT",
                    "inputfile": "/store/data/Run2017D/JetHT/MINIAOD/31Mar2018-v1/70000/DAAA92B6-8044-E811-9E9E-0CC47A4D7638.root",
                },
                {
                    "name": "SingleMu",
                    "inputfile": "/store/data/Run2017D/SingleMuon/MINIAOD/31Mar2018-v1/80000/1E703527-F436-E811-80A7-E0DB55FC1055.root",
                },
                {
                    "name": "SingleElectron",
                    "inputfile": "/store/data/Run2017D/SingleElectron/MINIAOD/31Mar2018-v1/80000/4899B9E7-F038-E811-8012-00000065FE80.root",
                },
            ]
        },
        "mc": {
            "config": "ntuplewriter_mc_2017.py",
            "jobs":[
                {
                    "name": "TTHadronic",
                    "inputfile": "/store/mc/RunIIFall17MiniAOD/TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8/MINIAODSIM/94X_mc2017_realistic_v10-v1/40000/2657B2FF-650D-E811-99F6-0025905A6060.root",
                },
                {
                    "name": "TTSemiLeptonic",
                    "inputfile": "/store/mc/RunIIFall17MiniAODv2/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/MINIAODSIM/PU2017_12Apr2018_94X_mc2017_realistic_v14-v2/30000/D221F074-FF58-E811-958D-509A4C78138B.root",
                },
            ]
        },
    },

    ######################
    # 2016 v3 MINIAOD
    ######################

    "2016v3": {
        "data": {
            "config": "ntuplewriter_data_2016v3.py",
            "jobs": [
                {
                    "name": "JetHT",
                    "inputfile": "/store/data/Run2016D/JetHT/MINIAOD/17Jul2018-v1/80000/601A2C83-5E8D-E811-9BF9-1CB72C0A3DBD.root",
                },
                {
                    "name": "SingleMu",
                    "inputfile": "/store/data/Run2016B/SingleMuon/MINIAOD/17Jul2018_ver1-v1/20000/F846D019-069B-E811-A03B-0242AC1C0502.root",
                },
                {
                    "name": "SingleElectron",
                    "inputfile": "/store/data/Run2016H/SingleElectron/MINIAOD/17Jul2018-v1/00000/0CE37460-7B8F-E811-BF05-002590DBDFE2.root",
                },
            ]
        },
        "mc": {
            "config": "ntuplewriter_mc_2016v3.py",
            "jobs":[
                {
                    "name": "TTbar",
                    "inputfile": "/store/mc/RunIISummer16MiniAODv3/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/MINIAODSIM/PUMoriond17_94X_mcRun2_asymptotic_v3-v1/00000/02AF6CD5-22C3-E811-B5AA-0CC47AFC3C64.root",
                }
            ]
        }
    },

    ######################
    # 2016 v2 (80X) MINIAOD
    ######################

    "2016v2": {
        "data": {
            "config": "ntuplewriter_data_2016v2.py",
            "jobs": [
                {
                    "name": "JetHT",
                    "inputfile": "/store/data/Run2016E/JetHT/MINIAOD/03Feb2017-v1/80000/D6BA9954-07F0-E611-BEAB-0CC47A7C34D0.root",
                },
                {
                    "name": "SingleMu",
                    "inputfile": "/store/data/Run2016F/SingleMuon/MINIAOD/03Feb2017-v1/110000/7A95EB9B-04EF-E611-8C78-0CC47A4D7626.root",
                },
                {
                    "name": "SingleElectron",
                    "inputfile": "/store/data/Run2016E/SingleElectron/MINIAOD/03Feb2017-v1/110001/7C28F3E1-7AEB-E611-BB15-0025905A6064.root",
                },
            ]
        },
        "mc": {
            "config": "ntuplewriter_mc_2016v2.py",
            "jobs":[
                {
                    "name": "TTbar",
                    "inputfile": "/store/mc/RunIISummer16MiniAODv2/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/MINIAODSIM/PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/80000/E022CF80-0ABF-E611-B5CD-00259048A87C.root",
                },
            ]
        }
    }

}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", required=True, help="Year of config to run e.g. 2018, 2016v2")
    parser.add_argument("--isData", action='store_true', help="Use if running over data")
    parser.add_argument("--append", type=str, help="Optional append to add to Ntuple & log files", default="")
    args = parser.parse_args()

    year_dict = CONFIGS.get(args.year, None)
    if year_dict is None:
        raise KeyError("Cannot find entry in dictionary with year argument %s" % args.year)
    type_str = 'data' if args.isData else 'mc'
    jobs_dict = year_dict.get(type_str, None)
    if jobs_dict is None:
        raise KeyError("Cannot find entry in dictionary argument %s" % type_str)

    config_filename = jobs_dict['config']
    jobs = jobs_dict['jobs']

    for job in jobs:
        if "inputfile" not in job:
            raise RuntimeError("No 'inputfile' key, you must specify an inputfile")
        if "name" not in job:
            raise RuntimeError("No 'name' key, you must specify a name")

        # First copy the file across from EOS to avoid XROOTD errors
        cp_cmd = "source ${{CI_PROJECT_DIR}}/scripts/fetchMiniAOD.sh {inputfile}".format(**job)
        fetch_return_code = subprocess.call(cp_cmd, shell=True)
        if fetch_return_code != 0:
            sys.exit(fetch_return_code)

        # Now run the actual cmsRun command
        append = "%s_%s_%s%s" % (type_str, args.year, job['name'], args.append)

        cms_dict = deepcopy(job)
        cms_dict['inputfile'] = os.path.basename(job['inputfile'])
        cms_dict['config'] = config_filename
        cms_dict['outputfile'] = "Ntuple_%s.root" % append
        cms_dict['logfile'] = "log_%s.txt" % append
        cms_dict['cmdlineopt'] = job.get("cmdlineopt", "")  # for other commandline options
        cms_dict['numthreads'] = job.get("numthreads", 1)
        cms_dict['maxevents'] = job.get("maxevents", NEVENTS)

        # Hack to make cmsRun work on the images as no default site set
        os.environ['CMS_PATH'] = '/cvmfs/cms-ib.cern.ch/'

        # Use tee to pipe to file & stdout simultaneously for monitoring
        cmsrun_cmd = ('cmsRun -n {numthreads} ${{CMSSW_BASE}}/python/UHH2/core/{config} {cmdlineopt} '
            'maxEvents={maxevents} wantSummary=1 inputFiles=file:{inputfile} outputFile={outputfile} '
            '2>&1 | tee {logfile}'.format(**cms_dict))
        return_code = subprocess.call(cmsrun_cmd, shell=True, stderr=subprocess.STDOUT)
        if return_code != 0:
            sys.exit(return_code)

    sys.exit(0)
