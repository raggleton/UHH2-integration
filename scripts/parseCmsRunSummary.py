#!/usr/bin/env python


"""Parse summary output from cmsRun & save timings to JSON.

Requires you have:

process.options = cms.untracked.PSet(wantSummary=cms.untracked.bool(True))

in your CMSSW config
"""


import os
import sys
import json
import argparse


def parse_and_dump(input_filename, json_filename):
    """Parse input file, dump relevant info to JSON file.
    
    Parameters
    ----------
    input_filename : str
        Input filename with summary contents
    json_filename : str
        Output JSON filename
    
    Raises
    ------
    IOError
        If input file does not exists
    RuntimeError
        If bad parsing occurs
    """
    if not os.path.isfile(input_filename):
        raise IOError("Cannot find input file %s" % input_filename)

    event_timing = {}
    module_timing = {}
    
    with open(input_filename) as f:
        save_event_timing = False
        save_module_timing = False

        for line in f:
            if not line.startswith("TimeReport"):
                continue

            # Get timing about whole events
            if "Event  Summary ---[sec]" in line:
                save_event_timing = True
                save_module_timing = False
                continue

            if save_event_timing:
                if "-------" in line:
                    # end of Event timing
                    save_event_timing = False
                    continue
                newline = line.replace("TimeReport", "").strip()
                parts = newline.split("=")
                if len(parts) != 2:
                    raise RuntimeError("len(parts) != 2, check parsing: %s" % parts)
                event_timing[parts[0].strip()] = float(parts[1].strip())

            # Get per module timing
            if "Module Summary ---[Real sec]" in line:
                save_event_timing = False
                save_module_timing = True
                continue

            if save_module_timing:
                if "-------" in line:
                    # End of module timing
                    save_module_timing = False
                    continue
                newline = line.replace("TimeReport", "").strip()
                if "per event" in line:
                    continue
                
                parts = newline.split()
                if len(parts) != 4:
                    raise RuntimeError("len(parts) != 4, check parsing: %s" % parts)
                per_event, per_exec, per_visit, name = parts
                module_timing[name] = {
                    "per_event": float(per_event),
                    "per_exec": float(per_exec),
                    "per_visit": float(per_visit),
                    "per_event_frac": float(per_event) / float(event_timing['event loop Real/event']),
                    "per_exec_frac": float(per_exec) / float(event_timing['event loop Real/event']),
                    "per_visit_frac": float(per_visit) / float(event_timing['event loop Real/event']),
                }

        # print(event_timing)
        # print(module_timing)

    total_dict = {"event_timing": event_timing, "module_timing": module_timing}
    with open(json_filename, 'w') as jf:
        json.dump(total_dict, jf, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input log file")
    parser.add_argument("--output", default="log.json", help="Output JSON filename")
    args = parser.parse_args()

    parse_and_dump(args.input, args.output)
    
