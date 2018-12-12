#!/usr/bin/env python

"""Generate all the necessary XRDCP commands to copy files for cmsrun jobs"""


from __future__ import print_function
import os
from cmsrun_jobs import CONFIGS


# Set this to your desired location
DESTINATION = "root://eosuser.cern.ch//eos/user/r/raggleto/UHH2MiniAOD"


XROOTD_REDIR = "root://xrootd-cms.infn.it"


for year, year_dict in CONFIGS.items():
    for type_str, job_dicts in year_dict.items():
        for job in job_dicts['jobs']:
            filename = job['inputfile']
            this_source = '/'.join([XROOTD_REDIR, filename])
            this_destination = os.path.join(DESTINATION, os.path.basename(filename))
            print("xrdcp --retry 3 %s %s" % (this_source, this_destination))