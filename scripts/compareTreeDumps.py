#!/usr/bin/env python


"""Script to compare all entries in 2 tree dumps made by dumpNtuple.py
Plots are made, with the option of separate thumbnail plots fo use in a website.

An analysis is also performed to categorise plot comaprisons.
The results are saved to a JSON file.
"""


from __future__ import print_function
from six import string_types

import os
import re
import json
import argparse
import numpy as np
from array import array
from itertools import chain
from collections import OrderedDict, Counter
from tqdm import tqdm
import ROOT


ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(1)
ROOT.TH1.SetDefaultSumw2()
# ROOT.gErrorIgnoreLevel = ROOT.kError
ROOT.gErrorIgnoreLevel = ROOT.kBreak  # to turn off all Error in <TCanvas::Range> etc


# don't use kBlack as you can't see it against the axes
HIST_COLOURS = [ROOT.kBlue, ROOT.kRed]


def get_collections(tree_data_keys):
    """Figure out branches/collections from tree_data dict keys
    i.e. names of nested method calls

    e.g. ['run', 'slimmedJets.pt()'] -> ['run', 'slimmedJets']
    Parameters
    ----------
    tree_data_keys :
        List of method names from tree

    Returns
    -------
    [str]
        List of unique collections
    """
    collections = []
    for key in tree_data_keys:
        key += "."
        collections.append(key.split(".")[0])
    collections = sorted(list(set(collections)))
    return collections


def make_hists_ROOT(data1, data2, method_str):
    """Create ROOT TH1s for data1 & data2.
    Also returns stats boxes, which are tricky to handle.

    Auto figures out x axis limits from range of both data1 & data2

    Parameters
    ----------
    data1 : [...]
        List of data to go into hist1
    data2 : [...]
        List of data to go into hist2
    method_str : TYPE
        Description

    Returns
    -------
    TYPE
        Description
    """
    hname_clean = method_str.replace("()", "")
    c = ROOT.TCanvas("ctmp"+hname_clean, "", 800, 600)

    nbins = 50

    h1, stats1, h2, stats2 = None, None, None, None
    # Need special procedure for strings
    # Use six.string_types to handle string in both py2 and 3
    # Since they are u'xxx' in py2, and 'xxx' in py3
    # and test for bytes type since awkward seems to use that for strings?
    def _get_first_entry(iterable):
        return iterable[0] if len(iterable) > 0 else None
    data1_first_entry = _get_first_entry(data1) if data1 is not None else None
    data2_first_entry = _get_first_entry(data2) if data2 is not None else None

    if ((data1 is not None and isinstance(data1_first_entry, (string_types, bytes))) or
        (data2 is not None and isinstance(data2_first_entry, (string_types, bytes)))):
        # To plot hists for string values, we plot a frequency plot for each unique string
        counter1 = Counter(data1)
        counter2 = Counter(data2)
        all_values = set(data1) | set(data2)
        all_values = sorted(list(all_values))
        nbins = len(all_values)
        xmin, xmax = 0, nbins

        if data1 is not None:
            h1name = "h1_%s" % (hname_clean)
            h1 = ROOT.TH1F(h1name, ";%s;N" % method_str, nbins, xmin, xmax)
            stats1 = None
            ax = h1.GetXaxis()
            ax.SetAlphanumeric()
            for ind, val in enumerate(all_values):
                ax.SetBinLabel(ind+1, val.decode())
                if val in counter1:
                    h1.Fill(ind, counter1[val])
            h1.Draw("HIST")
            c.Update()
            # Get stat boxes for repositioning
            # Draw hist by itself to get it, then plot them together afterwards
            stats1 = h1.GetListOfFunctions().FindObject("stats").Clone("stats1")
            h1.SetStats(0)

        if data2 is not None:
            h2name = "h2_%s" % (hname_clean)
            h2 = ROOT.TH1F(h2name, ";%s;N" % method_str, nbins, xmin, xmax)
            stats2 = None
            ax = h2.GetXaxis()
            ax.SetAlphanumeric()
            for ind, val in enumerate(all_values):
                ax.SetBinLabel(ind+1, val.decode())
                if val in counter2:
                    h2.Fill(ind, counter2[val])
            h2.Draw("HIST")
            c.Update()
            stats2 = h2.GetListOfFunctions().FindObject("stats").Clone("stats2")
            h2.SetStats(0)
            c.Clear()
    else:
        # Figure out axis range using both hists is possible
        xmin, xmax = 0, 1
        if isinstance(data1_first_entry, type(None)) or isinstance(data2_first_entry, type(None)):
            pass
        else:
            if isinstance(data1_first_entry, (bool, np.bool_)) or isinstance(data2_first_entry, (bool, np.bool_)):
                xmin, xmax = 0, 2
                nbins = 2
            else:
                try:
                    xmin = min(chain(data1, data2))
                    xmax = max(chain(data1, data2))
                    # add extra padding
                    delta = xmax - xmin
                    if delta == 0:
                        delta = xmin/10.  # extra padding incase only 1 value
                    xmin -= (0.1 * delta)
                    xmax += (0.1 * delta)
                except ValueError:
                    # happens if both sequences are empty
                    pass

        # Make hists
        # We make hists even if no data, to make further plotting easier
        if data1 is not None:
            h1name = "h1_%s" % (hname_clean)
            h1 = ROOT.TH1F(h1name, ";%s;N" % method_str, nbins, xmin, xmax)
            stats1 = None
            for d in data1:
                h1.Fill(d)
            h1.Draw("HIST")
            c.Update()
            # Get stat boxes for repositioning
            # Draw hist by itself to get it, then plot them together afterwards
            stats1 = h1.GetListOfFunctions().FindObject("stats").Clone("stats1")
            h1.SetStats(0)

        if data2 is not None:
            h2name = "h2_%s" % (hname_clean)
            h2 = ROOT.TH1F(h2name, ";%s;N" % method_str, nbins, xmin, xmax)
            stats2 = None
            for d in data2:
                h2.Fill(d)
            h2.Draw("HIST")
            c.Update()
            stats2 = h2.GetListOfFunctions().FindObject("stats").Clone("stats2")
            h2.SetStats(0)

        c.Clear()

    return h1, stats1, h2, stats2


def get_xy(graph):
    """Return lists of x, y points from a graph"""
    xarr = list(array('d', graph.GetX()))
    yarr = list(array('d', graph.GetY()))
    return xarr, yarr


def plot_hists_ROOT(h1, stats1, h2, stats2, output_dir=".",
                    canvas_size=(800, 600), fmt='pdf',
                    prepend="", append="", make_thumbnail=False):
    """Make a (comparison) plot from histogram h1 + stats box stats1, and h2+stats2 and save to file.

    h1/stats1 or h2/stats2 can be None, in which case a simpler plot is made
    from non-Null objects.

    Plot saved as <output_dir>/<prepend><method_str><append>.<fmt>
    where method_str is extracted from the histogram name.

    Can also save an additional smaller version
    as a thumbnail in <output_dir>/thumbnails

    Parameters
    ----------
    h1 : ROOT.TH1, optional
        If None, skip hist
    stats1 : ROOT.TPaveStats, optional
        If None, skip stats box
    h2 : ROOT.TH1, optional
        If None, skip hist
    stats2 : ROOT.TPaveStats, optional
        If None, skip stats box
    output_dir : str
        Output directory for plot
    canvas_size : tuple, optional
        Size of canvas
    fmt : str, optional
        Description
    prepend : str, optional
        <prepend> in filename
    append : str, optional
        <append> in filename
    make_thumbnail : bool, optional
        If True, save additional copy as small gif in subdir "thumbnails"

    """
    if not h1 and not h2:
        print("No TH1 object - not plotting")
        return

    hname = h1.GetName().replace("h1_", "") if h1 else h2.GetName().replace("h2_", "")
    c = ROOT.TCanvas("c"+hname, "", *canvas_size)
    c.SetTicks(1, 1)

    # Check if our version of ROOT has TRatioPlot
    do_ratioplot = True
    try:
        ROOT.TRatioPlot
    except AttributeError:
        do_ratioplot = False

    # Style hists
    h1_colour, h2_colour = HIST_COLOURS[0:2]
    if h1:
        h1.SetLineColor(h1_colour)
        h1.SetLineWidth(2)
    if h2:
        h2.SetLineColor(h2_colour)
        h2.SetLineStyle(2)
        if h1:
            h2.SetLineWidth(0)
        h2.SetMarkerColor(h2_colour)
        h2.SetMarkerStyle(33)
        h2.SetMarkerSize(1.5)

    # Do final plotting
    if do_ratioplot and h1 and h2:
        # Clone h1, since a bug in TRatioPlot will screw up h1
        # and change e.g. GetMean()
        rp = ROOT.TRatioPlot(h1.Clone(ROOT.TUUID().AsString()), h2.Clone(ROOT.TUUID().AsString()))
        rp.SetGridlines(array('d', [1.]), 1)
        # Set margins so that we can fit the stats box off the plot
        rp.SetLeftMargin(0.12)
        rp.SetRightMargin(0.18)
        rp.SetUpTopMargin(0.1)
        rp.SetGraphDrawOpt("ALP")
        rp.Draw("grid")

        # Manually set y axis range to ensure we see both hists fully, since this
        # class only uses the range of h1!
        ymax = max(h1.GetMaximum(), h2.GetMaximum())
        yax = rp.GetUpperRefYaxis()
        yax.SetRangeUser(0, ymax * 1.1)  # factor to pad it out a bit

        if h1.GetEntries() > 0 or h2.GetEntries() > 0:
            lower_gr = rp.GetLowerRefGraph()
            # Reset y errors to 0 in ratio graph as not useful
            for i in range(0, lower_gr.GetN()):
                exl = lower_gr.GetErrorXlow(i)
                exh = lower_gr.GetErrorXhigh(i)
                lower_gr.SetPointError(i, exl, exh, 0, 0)
            lower_gr.SetLineColor(ROOT.kRed)
            lower_gr.SetLineWidth(2)
            ratio_x, ratio_y = get_xy(lower_gr)
            # GetM[ax|in]imum() doesn't work here, do it manually
            default_min, default_max = 0.8, 1.2
            # We want to zoom in here to show minute differences - larger
            # differences should be immediately visible on the main plot
            # We set the largest range, and if possible zoom in on the ratios
            if len(ratio_y) > 0:
                min_ratio = min(ratio_y)
                max_ratio = max(ratio_y)
                if max_ratio >= 1 and min_ratio <= 1:
                    lower_gr.SetMinimum(max(default_min, 0.99 * min_ratio))
                    lower_gr.SetMaximum(min(default_max, 1.01 * max_ratio))
            else:
                lower_gr.SetMinimum(default_min)
                lower_gr.SetMaximum(default_max)

        rp.GetLowerRefYaxis().SetTitle("h1 / h2")
        rp.GetLowerRefYaxis().SetTitleOffset(1.65)

        # Try and reset labels to get same ones as component hists
        # Broken in ROOT, no idea how to fix
        # https://root-forum.cern.ch/t/tratioplot-with-alphanumeric-label/40682
        if h1.GetXaxis().IsAlphanumeric():
            print("Warning:", h1.GetName().replace("h1_", ""), "has alphanumeric axis labels, but TRatioPlot doesn't support them")
        xax_ref = h1.GetXaxis()
        nbins = h1.GetNbinsX()
        xax = rp.GetLowerRefXaxis()
        for i in range(1, nbins+1):
            ref_label = xax_ref.GetBinLabel(i)
            if not ref_label:
                continue
            xax.SetBinLabel(i-1, ref_label)
        c.Modified()
        c.Update()
    else:
        xtitle, ytitle = "", ""
        if h1:
            xtitle = h1.GetXaxis().GetTitle()
            ytitle = h1.GetYaxis().GetTitle()
        elif h2:
            xtitle = h2.GetXaxis().GetTitle()
            ytitle = h2.GetYaxis().GetTitle()
        hst = ROOT.THStack("hst"+hname, ";"+xtitle+";"+ytitle)
        if h1:
            hst.Add(h1)
        if h2:
            hst.Add(h2)
        # Set margins so that we can fit the stats box off the plot
        ROOT.gPad.SetRightMargin(0.18)
        ROOT.gPad.SetTopMargin(0.1)
        hst.Draw("NOSTACK HIST")

    c.cd()

    # Format stats boxes & draw
    fmt_str = "1.2g"
    if stats1:
        stats1.SetY1NDC(0.72)
        stats1.SetX1NDC(0.825)
        stats1.SetX2NDC(0.99)
        stats1.SetY2NDC(0.9)
        stats1.SetStatFormat(fmt_str)
        stats1.SetTextColor(h1_colour)
        stats1.GetListOfLines()[0].SetTitle("h1 (new)")
        stats1.Draw()

    if stats2:
        stats2.SetY1NDC(0.52)
        stats2.SetX1NDC(0.825)
        stats2.SetX2NDC(0.99)
        stats2.SetY2NDC(0.7)
        stats2.SetStatFormat(fmt_str)
        stats2.SetTextColor(h2_colour)
        stats2.GetListOfLines()[0].SetTitle("h2 (ref)")
        stats2.Draw()

    c.Modified()

    output_filename = "%s%s%s.%s" % (prepend, hname, append, fmt)
    output_name = os.path.join(output_dir, output_filename)
    c.SaveAs(output_name)

    if make_thumbnail:
        c.SetCanvasSize(300, 200)
        output_filename = "%s%s%s.%s" % (prepend, hname, append, 'gif')
        output_name = os.path.join(output_dir, "thumbnails", output_filename)
        c.SaveAs(output_name)


class HistSummary(object):

    def __init__(self, name, description):
        """Simple class to hold info about summary between 2 hists

        Parameters
        ----------
        name : str
            Classification of summary
        description : str
            Detailed description
        """
        self.name = name.upper().replace(" ", "_")
        self.description = description

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return "HistSummary(%s, %s)" % (self.name, self.description)

    def __str__(self):
        return "HistSummary(%s, %s)" % (self.name, self.description)

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)


def isclose(a, b, rel_tol=1e-06, abs_tol=0.0):
    """Safe way to compare 2 floats instead of exact equality.

    Parameters
    ----------
    a : float
    b : float
        floats to compare
    rel_tol : float, optional
        Maximum relative difference allowed. Can see rel differences
        ~ 5E-7 that are just rounding errors, so 1E-6 is sensible.
    abs_tol : float, optional
        Maximum absolute difference allowed

    Returns
    -------
    bool
    """
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def analyse_hists(hist1, hist2):
    """Analyse the 2 histograms and return status string

    Parameters
    ----------
    hist1 : ROOT.TH1, optional
    hist2 : ROOT.TH1, optional

    Returns
    -------
    HistSummary
        Summary info in the form of a HistSummary object
    """

    if hist2 is None and hist1 is None:
        return HistSummary("BOTH_EMPTY", "Both hists not available")

    if hist2 is None or hist1 is None:
        return HistSummary("ONE_EMPTY", "One hist not available")

    n_entries1 = hist1.GetEntries()
    n_entries2 = hist2.GetEntries()

    if n_entries1 == 0 and n_entries2 == 0:
        return HistSummary("NO_ENTRIES", "Both hists has 0 entries")

    if n_entries2 != n_entries1:
        return HistSummary("DIFF_ENTRIES", "Differing number of entries")

    mean1, mean2 = hist1.GetMean(), hist2.GetMean()
    rms1, rms2 = hist1.GetRMS(), hist2.GetRMS()
    if not isclose(mean1, mean2) or not isclose(rms1, rms2):
        return HistSummary("DIFF_MEAN_RMS", "Differing means and/or RMS")

    # Check x axis range to see if unusually large, or occupies only large numbers
    # X range should be same for both by design
    xmin, xmax = hist1.GetXaxis().GetXmin(), hist1.GetXaxis().GetXmax()
    delta = xmax - xmin
    # hopefully nothing spans that range
    range_lim = 1.0E10
    if delta > range_lim:
        return HistSummary("VERY_LARGE_RANGE", "Values have very large range (> %g)" % range_lim)

    # Maybe range is small, but all values are very very large (or v.v.small)
    if xmax > range_lim or xmin < -range_lim:
        return HistSummary("EXTREME_VALUES", "x axis has very large values (+- %g)" % range_lim)

    if (isclose(mean1, 0) and isclose(rms1, 0)) or (isclose(mean2, 0) and isclose(rms2, 0)):
        return HistSummary("ZERO_VALUE", "One or both hists have only 0s")

    if isclose(rms1, 0) or isclose(rms2, 0):
        return HistSummary("ZERO_RMS", "One or both RMSs are 0: stores same value")

    return HistSummary("SAME", "Histograms are the same (lowest priority)")


def save_to_json(json_data, hist_status, output_filename):
    """Save plot info to JSON

    Parameters
    ----------
    json_data : dict
        Main dict about added hists etc
    hist_status : dict
        Dict of {histname: HistSummary}
    output_filename : str
    """
    # Discard the common_hists list, we use hist_status info instead
    # We only keep original info about added/removed collections
    if 'common_hists' in json_data:
        del json_data['common_hists']

    # Store histograms grouped by status
    statuses = sorted(list(set(hist_status.values())))
    status_dict = {}
    for status in statuses:
        status_dict[status.name] = {
                                    "description": status.description,
                                    "number": 0,
                                    "names": []
                                   }

    added_removed_hists = json_data['added_hists'] + json_data['removed_hists']
    for hist_name, status in hist_status.items():
        if hist_name in added_removed_hists:
            continue
        status_dict[status.name]['number'] += 1
        status_dict[status.name]['names'].append(hist_name)

    json_data['comparison'] = status_dict

    def _convert_entry(my_dict, key):
        """Replace basic list with dict of list and length"""
        col = my_dict[key]
        new_entry = {"number": len(col), "names": col}
        my_dict[key] = new_entry

    # Reorganise the added/removed hists to also store #s, easier for table
    _convert_entry(json_data, 'added_collections')
    _convert_entry(json_data, 'removed_collections')
    _convert_entry(json_data, 'added_hists')
    _convert_entry(json_data, 'removed_hists')

    with open(output_filename, 'w') as jf:
        json.dump(json_data, jf, indent=2, sort_keys=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filename",
                        help='Ntuple dump filename (made by dumpNtuple.py,'
                             ' will be labelled "new" in plots)')
    parser.add_argument("--compareTo",
                        help='Optional reference comparison dump file '
                             '(made by dumpNtuple.py, will be labelled "ref" in plots)')

    default_output_dir = "treePlots"
    parser.add_argument("--outputDir",
                        help="Output directory for plots, defaults to %s" % default_output_dir,
                        default=default_output_dir)
    default_fmt = "pdf"
    parser.add_argument("--fmt",
                        help="Output plot file format, defaults to %s. "
                             "Pass space-separated list to save file in each format" % default_fmt,
                        nargs="+",
                        default=[default_fmt])

    default_json_filename = "comparison.json"
    parser.add_argument("--json",
                        help="Output JSON filename template used for plot comparison result JSON, defaults to %s" % default_json_filename,
                        default=default_json_filename)
    parser.add_argument("--thumbnails",
                        help="Make thumbnail plots in <outputDir>/thumbnails",
                        action='store_true')
    parser.add_argument("--verbose", "-v",
                        help="Printout extra info",
                        action='store_true')
    args = parser.parse_args()

    tree_data1 = {}
    tree_data2 = {}

    # whether to handle as HDF5 or awkward arrays
    is_hdf5_1 = "hdf5" in os.path.splitext(args.filename)[1]
    if not is_hdf5_1 and "awkd" not in os.path.splitext(args.filename)[1]:
        raise IOError("Input must be .hdf5 or .awkd")

    if is_hdf5_1:
        import h5py
        tree_data1 = h5py.File(args.filename)
        print(len(tree_data1.keys()), "hists in main file")
    else:
        import awkward
        major, minor, _ =  awkward.version.version_info
        major = int(major)
        minor = int(minor)
        if major == 1:
            raise ImportError("Need awkward 0.12.X, you have %s" % awkward.__version__)
        elif minor > 14:
            raise ImportError("Need awkward 0.12 / 0.13 / 0.14, you have %s" % awkward.__version__)
        elif minor < 12:
            raise ImportError("Need awkward 0.12 / 0.13 / 0.14, you have %s" % awkward.__version__)

        tree_data1 = awkward.load(args.filename)
        print(len(tree_data1.columns), "hists in main file")

    is_hdf5_2 = False
    if args.compareTo:
        is_hdf5_2 = "hdf5" in os.path.splitext(args.compareTo)[1]
        if not is_hdf5_2 and "awkd" not in os.path.splitext(args.compareTo)[1]:
            raise IOError("--compareTo input must be .hdf5 or .awkd")

        if is_hdf5_2:
            if not is_hdf5_1:
                import h5py
            tree_data2 = h5py.File(args.compareTo)
            print(len(tree_data2.keys()), "hists in compareTo file")
        else:
            if is_hdf5_1:
                import awkward
                major, minor, _ =  awkward.version.version_info
                major = int(major)
                minor = int(minor)
                if major == 1:
                    raise ImportError("Need awkward 0.12.X, you have %s" % awkward.__version__)
                elif minor > 14:
                    raise ImportError("Need awkward 0.12 / 0.13 / 0.14, you have %s" % awkward.__version__)
                elif minor < 12:
                    raise ImportError("Need awkward 0.12 / 0.13 / 0.14, you have %s" % awkward.__version__)

            tree_data2 = awkward.load(args.compareTo)
            print(len(tree_data2.columns), "hists in compareTo file")


    json_data = {
        "added_collections": [],
        "removed_collections": [],
        "added_hists": [],
        "removed_hists": []
    }

    tree1_keys = tree_data1.keys() if is_hdf5_1 else tree_data1.columns
    collections1 = get_collections(tree1_keys)

    tree2_keys, collections2 = [], []
    if args.compareTo:
        tree2_keys = tree_data2.keys() if is_hdf5_2 else tree_data2.columns
        collections2 = get_collections(tree2_keys)
        # Store added/removed collections
        # Added/removed are defined relative to the tree passed as --compareTo
        cols1 = set(collections1)
        cols2 = set(collections2)
        added = sorted(list(cols1 - cols2))
        removed = sorted(list(cols2 - cols1))
        json_data['added_collections'].extend(added)
        json_data['removed_collections'].extend(removed)

        # Store added/removed hists
        hists1 = set(tree1_keys)
        hists2 = set(tree2_keys)
        added_hists = sorted(list(hists1 - hists2))
        removed_hists = sorted(list(hists2 - hists1))
        json_data['added_hists'].extend(added_hists)
        json_data['removed_hists'].extend(removed_hists)
        json_data['common_hists'] = sorted(list(hists1 & hists2))

    # Setup output dirs
    if not os.path.isdir(args.outputDir):
        os.makedirs(args.outputDir)

    thumbnails_dir = os.path.join(args.outputDir, "thumbnails")
    if args.thumbnails and not os.path.isdir(thumbnails_dir):
        os.makedirs(thumbnails_dir)

    hist_status = OrderedDict()

    # Make & plot (comparison) hists
    common_hists = sorted(json_data.get('common_hists', tree1_keys))  # If only ref file, just do all
    added_hists = json_data.get('added_hists', [])
    removed_hists = json_data.get('removed_hists', [])
    all_hists = list(chain(common_hists, added_hists, removed_hists))

    print("Producing", len(all_hists), "hists")
    json_data['total_number'] = len(all_hists)

    # Use tqdm to get nice progress bar, and add hist name if verbose,
    # padded to keep constant position for progress bar
    # disable on non-TTY
    pbar = tqdm(all_hists, disable=None)
    max_len = max(len(l) for l in all_hists)
    fmt_str = "{0: <%d}" % (max_len+2)
    for method_str in pbar:
        if args.verbose:
            pbar.set_description(fmt_str.format(method_str))

        # Make histograms
        data1 = tree_data1[method_str] if method_str in tree1_keys else []
        if not is_hdf5_1 and len(data1) > 0:
            data1 = data1.flatten()

        data2 = tree_data2[method_str] if method_str in tree2_keys else []
        if not is_hdf5_2 and len(data2) > 0:
            data2 = data2.flatten()

        hist1, stats1, hist2, stats2 = make_hists_ROOT(data1, data2, method_str)

        # Plot to file
        if hist1 or hist2:
            for fmt in args.fmt:
                plot_hists_ROOT(hist1, stats1, hist2, stats2,
                                args.outputDir,
                                canvas_size=(800, 600),
                                fmt=fmt,
                                prepend="", append="",
                                make_thumbnail=args.thumbnails)

        # Do comparison
        status = analyse_hists(hist1, hist2)
        hist_status[method_str] = status

    print(len(hist_status), "plots produced")

    # Save JSON data. Always needed for later steps in pipeline to work.
    save_to_json(json_data, hist_status, output_filename=args.json)

    if is_hdf5_1:
        tree_data1.close()
    if is_hdf5_2:
        tree_data2.close()
