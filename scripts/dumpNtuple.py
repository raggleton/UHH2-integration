#!/usr/bin/env python


"""Script to save all variables of all collections in a ntuple to a file in a flattened format.
Methods are called recursively on objects.

Class info can also be saved to a JSON file.
"""


from __future__ import print_function

import os
import re
import sys
import json
import argparse
import inspect
from operator import methodcaller, attrgetter
from collections import OrderedDict, defaultdict
from tqdm import trange
import ROOT


ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(1)
ROOT.TH1.SetDefaultSumw2()
# ROOT.gErrorIgnoreLevel = ROOT.kError
ROOT.gErrorIgnoreLevel = ROOT.kBreak  # to turn off all Error in <TCanvas::Range> etc


BUILTIN_TYPES = [
    # ROOT-isms, see TTree docs
    "C", "B", "b", "S", "s", "I", "i", "F", "D", "L", "l", "O",
    "Char_t", "UChar_t", "Short_t", "UShort_t", "Int_t", "UInt_t", "Float_t", "Double_t", "Long64_t", "ULong64_t", "Bool_t",
    # C++ ones
    "char", "unsigned char", "short", "unsigned short", "int", "unsigned int", "float", "double", "long", "unsigned long", "bool", "string"
]

# Horrific mapping between ROOT types (short & full names), Python array types (short names only), and C++ names
TYPES = [
    {'root_short': 'C', 'root_full': None,        'py_short': 'c',  'cpp': 'string'},  # this is a null-terminated character string in ROOT. string probably isn't right? but we need it somewhere
    {'root_short': 'B', 'root_full': 'Char_t',    'py_short': 'b',  'cpp': 'char'},  #  also 1+ bytes
    {'root_short': 'b', 'root_full': 'UChar_t',   'py_short': 'B',  'cpp': 'unsigned char'},  # yes the py_short and root_short are opposites
    {'root_short': 'S', 'root_full': 'Short_t',   'py_short': 'h',  'cpp': 'short'},  # 2+ bytes
    {'root_short': 's', 'root_full': 'UShort_t',  'py_short': 'H',  'cpp': 'unsigned short'},
    {'root_short': 'I', 'root_full': 'Int_t',     'py_short': 'i',  'cpp': 'int'},
    {'root_short': 'i', 'root_full': 'UInt_t',    'py_short': 'I',  'cpp': 'unsigned int'},
    {'root_short': 'F', 'root_full': 'Float_t',   'py_short': 'f',  'cpp': 'float'},
    {'root_short': 'D', 'root_full': 'Double_t',  'py_short': 'd',  'cpp': 'double'},
    {'root_short': 'L', 'root_full': 'Long64_t',  'py_short': 'l',  'cpp': 'long'},
    {'root_short': 'l', 'root_full': 'ULong64_t', 'py_short': 'L',  'cpp': 'unsigned long'},
    {'root_short': 'O', 'root_full': 'Bool_t',    'py_short': 'b',  'cpp': 'bool'},
]

BUILTIN_TYPES = []
for k in TYPES[0].keys():
    BUILTIN_TYPES.extend([d[k] for d in TYPES if d[k] is not None])

# Methods specific to TLorentzVector, ROOT::TMath::LorentzVector, since we don't
# want every method
LORENTZVECTOR_METHODS = ["E", "Pt", "Pz", "X", "Y", "Z"]


class BranchInfo(object):

    """Lightweight class to hold info about a branch"""

    def __init__(self, name, classname, typename, title):
        self.name = name
        self.classname = classname
        self.typename = typename
        self.title = title
        if classname == "" and title != "":
            self.classname = title.split('/')[-1].strip()

    def __repr__(self):
        return "{name}: {classname}, {typename}, {title}".format(**self.__dict__)

    def __str__(self):
        return "{name}: {classname}, {typename}, {title}".format(**self.__dict__)

    def __eq__(self, other):
        return self.name == other.name and self.classname == other.classname


def store_branches(tree, obj_list, do_recursive=False, indent=0):
    """Iterate through tree (optionally recursively),
    storing branch info as BranchInfo objects to obj_list.

    Parameters
    ----------
    tree : TTree, TBranch
        Anything that has branches
    obj_list : list[BranchInfo]
        List to append BranchInfo objects to
    do_recursive : bool, optional
        If True, go through branches recursively
    indent : int, optional
        Indentation for printout. If None, does not print
    """
    for b in tree.GetListOfBranches():
        this_name = b.GetName()
        classname = b.GetClassName()
        typename = classname
        if isinstance(b, ROOT.TBranchElement):
            typename = b.GetTypeName()
        this_br_info = BranchInfo(name=this_name,
                                  classname=classname,
                                  typename=typename,
                                  title=b.GetTitle())
        new_indent = indent
        if indent is not None:
            print(" " * indent, this_br_info)
            new_indent += 2
        obj_list.append(this_br_info)
        if do_recursive:
            store_branches(b, obj_list, True, new_indent)


def check_enum(this_type):
    """Check if a type is actually an enum

    in older pyROOT __name__ resolves to 'int'
    in newer pyROOT __name__ resolves to e.g. 'SimType' which we don't want

    Parameters
    ----------
    this_type : type

    Returns
    -------
    bool
    """
    return (int in this_type.__bases__) or (this_type.__name__ == "int")


def resolve_type(typename):
    """Convert the cppyy type to python types

    e.g. enum Muon::SimType -> int

    Parameters
    ----------
    typename : str

    Returns
    -------
    str
        Resolved type
    """
    if "LorentzVector" in typename or typename == "void":
        return typename

    typename = unvectorise_classname(typename).replace("::", ".")
    parts = typename.split(".")
    if parts[0] not in BUILTIN_TYPES:
        current = getattr(ROOT, parts[0])
        # this resolves e.g. ROOT.Muon.SimType,
        # since we can't do getattr(ROOT, 'Muon.SimType')
        for p in parts[1:]:
            current = getattr(current, p)
        if check_enum(current):
            return 'int'
        return current.__name__
    else:
        return parts[0]


def parse_function_signature(signature):
    """Handle cpp function signature, giving return type & function name

    Parameters
    ----------
    signature : str
        C++ function signature

    Returns
    -------
    str, str, str
        Return type, function name, arguments
    """
    # remove bits we don't care about
    signature = signature.strip().replace("&", "").replace("*", "")
    signature = signature.replace("const", "").replace("final", "").replace("static", "")

    # remove extra spaces around < > ( )
    signature = re.sub(r'([(<]) *', r'\1', signature)
    signature = re.sub(r' +([>)])', r'\1', signature)

    # parts should now be of the form <return type> <class::method>
    # but need to be able to handle:
    # ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiE4D<Double32_t> > MET::uncorr_v4()
    # void GenTopJet::add_subjet( Particle p)
    # unsigned int PrimaryVertex::nTracks()
    # GenParticle GenParticle::daughter(vector<GenParticle> gplist, int ind = 1)

    # Form is: <return type> <class>::<method name>(<optional arg type>)
    m = re.match(r'([\w <>::,]+) ([\w <>::]+)::([\w <>::,]+)\(([\w <>:: =,]*)\)', signature)
    if m:
        return_type = m.group(1).strip()
        method_name = m.group(3).strip()
        args = m.group(4)
    else:
        raise RuntimeError("Couldn't parse signature %s" % signature)

    return return_type, method_name, args


def get_function_info(classname, method):
    """Get the return type for a given method in class `classname`

    Does manual override of return type for select classes to avoid issues later.

    Parameters
    ----------
    classname : str
        Name of C++ class
    method : str
        Method name (without the ())

    Returns
    -------
    str, str, str
        Return typename, method name, arguments
    """
    # Manually override these classes
    # TODO must be a better way than this
    if (("TLorentzVector" in classname or "Math.LorentzVector" in classname)
        and method in LORENTZVECTOR_METHODS):
        # Assumes every method returns a float!
        return "float", method, ""

    this_class = getattr(ROOT, classname)
    signature = getattr(this_class, method).__doc__  # get c++ method definition
    return_type, method_name, args = parse_function_signature(signature)
    return return_type, method_name, args


def get_class_getters_info(classname, class_infos, do_recursive=False):
    """For a given class, get all getter methods & their return types,
    and all the class' properties. Updates/adds class_infos entry for that classname.

    Parameters
    ----------
    classname : str
        Name of class
    class_infos : list
        Dict of getters/properties for each class
    do_recursive : bool, optional
        If True, build chained methods using getters from objects
        returned by this class' getters
    """
    getter_info = {}
    # print("Getting getters for", classname)

    # Get getter methods
    for method in get_class_methods(classname):
        if (method.startswith("set_")  # skip setters
            or "operator" in method    # skip operators for now
            or method in ["Class"]):   # ROOT added or special methods
            continue

        return_type, method_name, args = get_function_info(classname, method)
        # ensure we only have getters
        if (return_type is None or return_type == "void" or return_type.startswith("_") or args != ""):
            continue

        return_type = resolve_type(return_type)  # since enums are really ints, etc

        method_name += "()"  # need to store the () to distinguish from properties
        # make python-friendly so it can be used in getattr
        return_type = return_type.replace("::", ".")
        getter_info[method_name] = return_type

        if (do_recursive and
            ("." in return_type
             or unvectorise_classname(return_type) not in BUILTIN_TYPES
             and return_type != "void")):
            # Need to check if this return class is in our dict
            return_type = unvectorise_classname(return_type)
            # if return_type not in class_infos:
            get_class_getters_info(return_type, class_infos, do_recursive)

    # Get properties e.g. enums
    # FIXME is it possible to get return type? normally int or float, but how to check?
    # __doc__ doesn't work, neither dir(), nor inspect
    properties = [m for m in get_class_properties(classname)
                    if not (m.startswith("set_")  # skip setters
                            or "operator" in m    # skip operators for now
                            or m in ["Class"])    # ROOT added methods we don't want
                 ]

    class_infos[classname] = {"methods": getter_info, "properties": properties}
    # print(class_infos[classname])


def unvectorise_classname(classname):
    """Find the type of element stored in vector. Assumes form "vector<xxxx>".
    If no vector<, returns original class name

    Parameters
    ----------
    classname : str
        Name of class

    Returns
    -------
    str
    """
    classname = classname.strip()
    if classname.startswith("vector<"):  # use startswith to ensure not LorentzVector
        # hope there are no newlines...
        matches = re.search(r'vector<(.+)>', classname)
        if matches:
            classname = matches.group(1).strip()
    return classname


def get_class_methods(classname):
    """Get all methods for a given class

    Parameters
    ----------
    classname : str
        Name of class

    Returns
    -------
    list[str]
    """
    # manually handle otherwise entire infinite recursion
    if "LorentzVector" in classname:
        return LORENTZVECTOR_METHODS[:]
    if classname.startswith("ROOT"):
        return []

    # resolve handle nested classes e.g. Muon.SimType
    parts = classname.strip().split(".")
    this_class = ROOT
    for part in parts:
        this_class = getattr(this_class, part)
    # using ismethod avoids enum values
    methods = [name for name, type_obj
               in inspect.getmembers(this_class, predicate=inspect.ismethod)
               if not name.startswith("_")]
    return methods


def get_class_properties(classname):
    """Get all properties for a given class

    A property can be an enum value, or a class property
    e.g. source_candidate.E

    Parameters
    ----------
    classname : str
        Name of class

    Returns
    -------
    list[str]
    """
    # TODO: unify with get_class_methods as too much overlap?
    if "lorentzvector" in classname.lower():
        return []
    if classname.startswith("ROOT"):
        return []

    # resolve nested classes e.g. Muon.SimType
    parts = classname.strip().split(".")
    this_class = ROOT
    for part in parts:
        this_class = getattr(this_class, part)
    properties = []
    for key, val in vars(this_class).items():  # can't use getmembers for e.g. source_candidate
        if key.startswith("_"):
            continue
        if not isinstance(val, ROOT.PropertyProxy):
            continue
        properties.append(key)
    return properties


def add_list_of_methods(branch_name, branch_type, class_infos, method_list, do_properties=True):
    """Add list of methods corresponding to class getters, does it recursively

    Parameters
    ----------
    branch_name : str
        Name of branch
    branch_type : str
        Branch class
    class_infos : dict
        Dict of getters/properties for each class
    method_list : list[str]
        List of nested getters corresponding to a histogram that will be updated
    do_properties : bool, optional
        If True, also add in class properties (filtered)
    """
    join_char = "."
    if branch_type in BUILTIN_TYPES:
        # trivial type, need to keep this for recursive scenario?
        method_list.append(branch_name)
    else:
        # add getter methods
        for method_name, return_type in class_infos[branch_type]['methods'].items():
            return_type = unvectorise_classname(return_type)
            if return_type in BUILTIN_TYPES or return_type not in class_infos:
                # trivial type, can therefore add and stop there
                method_list.append(join_char.join([branch_name, method_name]))
            else:
                # return type is a class, so must go through all of its methods as well
                add_list_of_methods(join_char.join([branch_name, method_name]),
                                    return_type,
                                    class_infos,
                                    method_list,
                                    do_properties)

        # add properties e.g. enums
        # only do this for properties of select classes eg source_candidate,
        # not enums, which are more complicated and get taken care of separately
        if do_properties and branch_type in ['source_candidate']:
            for prop in class_infos[branch_type]['properties']:
                method_list.append(join_char.join([branch_name, prop]))


def get_compounded_return_types(method, tree_info, class_infos):
    """For a given chained set of methods on a collection, return
    a list of the return types, each entry corresponding to one of the methods.

    If collection does not exist in tree_info, return empty list

    Assumes float type for a property (probably shouldn't!)

    e.g. slimmedJets_SoftDrop.subjets().pt() -> [TopJet, Jet, float]

    Parameters
    ----------
    method : str
        Total chained method e.g. slimmedJets.subjets().pt()
    tree_info : list[BranchInfo]
        List with info about branch collections in tree
    class_infos : dict
        Dict with info about methods for classes

    Returns
    -------
    list[str]
        List of return types, empty if collection does not exist in tree_info
    """
    # Have to go through each level of access, and check return type
    method_parts = method.split(".")
    # First figure out what type this branch is and if it even exists in the tree
    br_info = [x for x in tree_info if x.name == method_parts[0]]
    if br_info:
        br_info = br_info[0]
    else:
        return []

    return_types = [br_info.classname]
    this_type = br_info.classname
    for meth in method_parts[1:]:
        if meth.endswith("()"):  # distinguish method from property
            this_type = class_infos[unvectorise_classname(this_type)]['methods'][meth]
            return_types.append(this_type)
        else:
            # silly default, but no idea how to get actual type of properties
            # hopefully is never a vector
            return_types.append("float")
    return return_types


def safe_iter(thing):
    """Return an iterable over `thing`, regardless of whether
    it is iterable or a single value
    """
    try:
        return iter(thing)
    except TypeError:
        return iter([thing])


def safe_next(thing):
    """Call next() on `thing`: if iterable, then returns next in sequence as usual;
    if single object returns object.

    Also returns bool as to whether it was a single objext or iterable
    """
    try:
        return next(thing), True
    except TypeError:
        return thing, False


def iter_data(collection, methods):
    # Using safe_iter here is required since our collection might be
    # a single object (genInfo) or a vector (slimmedJets)
    for obj in safe_iter(collection):
        xs = [safe_iter(methods[0](obj))]
        while xs:
            try:
                x, iterable = safe_next(xs[-1])
                if len(xs) < (len(methods)):
                    # Build up the stack of objects: we call the relevant
                    # method on the previous layer's object (x)
                    xs.append(safe_iter(methods[len(xs)](x)))
                else:
                    # Here we have all the necessary layers,
                    # so we just return the value
                    yield x
                # handle case of singel value, needs StopIteration to exit
                if not iterable:
                    raise StopIteration
            except StopIteration:
                xs.pop()


# This is needed to process a ROOT.vector<bool>, since they are treated differently,
# and badly (really a vector of ROOT._bit_reference, which are impossible to deal with)
# Instead we load this function, to neatly convert the vector into a vector of ints
# Taken from https://gist.github.com/rmanzoni/5b65bdcd5a89bfd871a1be13145d9306
PROCESS_VECTOR_OF_BOOL_CPP = """
std::vector<int> vectorBoolToInt(const std::vector<bool> vec) {
  std::vector<int> results;
  for (uint i=0; i<vec.size(); i++) {
    results.push_back(vec[i] == true);
  }
  return results;
}
"""
ROOT.gInterpreter.ProcessLine(PROCESS_VECTOR_OF_BOOL_CPP)


def get_data(tree, entry_index, method_strs):
    """Get data from chained method in `method_str` by iterating over the tree.
    This is designed for method chains that include methods that return vectors,
    since TTree.Draw can't handle them. However it is naturally slower.

    Parameters
    ----------
    tree : ROOT.TTree
        tree to iterate over
    entry_index : ind
        Entry number to get data from
    method_strs : [str]
        List of chained method string that starts with collection name
        e.g. slimmedJets.btaginfo().TrackEta()

    Yields
    ------
    {str : data}
        Data in the tree for this event. Each entry is a method, with its
        associated value(s), either a scalar or a list
    """
    tree.GetEntry(entry_index)

    this_data = OrderedDict()

    for method in method_strs:

        if "." in method:
            mparts = method.split(".")
            if len(mparts) < 2:
                raise RuntimeError("Improper tree variable, should be xxx.yyy at least")

            collection_name = mparts[0]

            # To handle any number of chained method calls, we have to build a stack
            # of methods, and of objects. The latter is updated each time the lower
            # iteration finishes.
            # Inspired by https://stackoverflow.com/a/45503317
            methods = []
            for mp in mparts[1:]:
                if mp.endswith("()"):
                    methods.append(methodcaller(mp.replace("()", "")))
                else:
                    methods.append(attrgetter(mp))

            this_data[method] = [d for d in iter_data(getattr(tree, collection_name), methods)]
        else:
            thing = getattr(tree, method)
            type_str = str(type(thing))
            if "ROOT.vector<bool>" in type_str:
                thing = ROOT.vectorBoolToInt(thing)
            if "ROOT.string" in type_str:
                this_data[method] = [str(thing)]  # don't want to iter over each character
            elif "ROOT.vector<string>" in type_str:
                this_data[method] = [str(d) for d in thing]
            else:
                try:
                    # handle iterative branches
                    this_data[method] = [d for d in thing]
                except TypeError:
                    # handle scalar branches
                    this_data[method] = thing

    return this_data


def check_tobj(tobj):
    """Check if TObject is valid, if not raise IOError"""
    if tobj == None or tobj.IsZombie():
        raise IOError("Cannot access %s" % tobj.GetName())


def parse_tree(tree):
    """Parse TTree by storing collections, types & their methods,
    and compiling list of chained methods corresponding to object getters.

    Parameters
    ----------
    tree : ROOT.TTree

    Returns
    -------
    list[BranchInfo], dict, list[str]
        List of collections in tree,
        info about classes & methods/properties in tree,
        list of chained methods
    """
    # Get top level branches
    tree_info = []
    store_branches(tree, tree_info, do_recursive=False, indent=None)

    # Since ROOT can't see beyond 2 levels of classes,
    # let's manually figure out class methods
    class_infos = OrderedDict()
    method_list = []
    for binfo in tree_info:
        classname = unvectorise_classname(binfo.classname)
        if classname not in class_infos and classname not in BUILTIN_TYPES:
            get_class_getters_info(classname, class_infos, do_recursive=True)

        # add method strings to be processed
        add_list_of_methods(binfo.name, classname, class_infos, method_list, do_properties=True)

    return tree_info, class_infos, method_list


def print_tree_summary(tree_info, class_info, label):
    print("-" * 80)
    print("%s collections:" % (label))
    print("-" * 80)
    [print(t) for t in tree_info]
    print("-" * 80)
    print("%s class info:" % (label))
    print("-" * 80)
    print(json.dumps(class_info, indent=2))
    print("-" * 80)


def get_size(obj, seen=None):
    """Recursively finds size of objects

    Taken from https://goshippo.com/blog/measure-real-size-any-python-object/
    """
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


def flatten_ntuple_write(input_filename, tree_name, output_filename, class_json_filename=None, verbose=False):
    """Convert ntuple to flattened file with awkward array table.
    All data for a given method are output as one long list, ignoring event splitting.

    Tried to output as ROOT TTree, but very difficult in PyROOT with
    variable size branches.

    Parameters
    ----------
    input_filename : std
        Input Ntuple filename
    tree_name : str
        Name of TTree inside input file
    output_filename : str
        Output filename
    class_json_filename : None, optional
        If a str, output class info dicts to this file in JSON format
    verbose : bool, optional
        If True, print class info
    """
    f_in = ROOT.TFile(input_filename)
    if f_in.IsZombie():
        raise RuntimeError("Cannot open ROOT file %s" % input_filename)
    tree = f_in.Get(tree_name)
    check_tobj(tree)

    tree_info, class_infos, method_list = parse_tree(tree)

    if verbose:
        print_tree_summary(tree_info, class_infos, 'tree')

    print(tree.GetEntries(), "entries in tree")
    print(len(method_list), "hists in tree")

    # store list of values for each method call, where each event is a dict of {method:value}
    tree_data = defaultdict(list)

    # Use tqdm for nice progressbar, disable on non-TTY
    for ind in trange(tree.GetEntries(), disable=None):
        this_data = get_data(tree, ind, method_list)
        # flatten all events into one long list per method, makes for a much
        # more compact output, we don't care about individual events
        # guess we could compare those events with the same number of entries
        # in both files? i.e. 1 or 0, but hard to do for
        # eg jets, in which jet #1 may not be the same object in both files
        # don't use items() as not iterator in python2
        for key in this_data:
            # may be a single scalar, or iterable - use extend where possible
            try:
                _ = iter(this_data[key])
                tree_data[key].extend(this_data[key])
            except TypeError:
                tree_data[key].append(this_data[key])

    print("tree_data size:", get_size(tree_data))

    # Save JSON data
    if class_infos and class_json_filename:
        with open(class_json_filename, 'w') as jf:
            json.dump(class_infos, jf, indent=2, sort_keys=True)

    is_hdf5 = "hdf5" in os.path.splitext(output_filename)[1]
    if is_hdf5:
        # Save to HDF5
        import h5py
        import numpy as np
        with h5py.File(output_filename, "w") as f:
            for k in tree_data:
                f.create_dataset(k, data=np.array(tree_data[k]),
                                 compression="gzip", compression_opts=9)
    else:
        # Save to awkward array
        # make awkward table, save with compression
        import awkward
        # Use awkeard 0.12/13/14 as 0.15 has a bug that means it can't load()
        # the file
        # And awkward 1 doesn't even allow this format
        # And the awkward 0.9 in CMSSW_10_6 is too old for this
        major, minor, _ =  awkward.version.version_info
        major = int(major)
        minor = int(minor)
        if major == 1:
            raise ImportError("Need awkward 0.12.X, you have %s" % awkward.__version__)
        elif minor > 14:
            raise ImportError("Need awkward 0.12 / 0.13 / 0.14, you have %s" % awkward.__version__)
        elif minor < 12:
            raise ImportError("Need awkward 0.12 / 0.13 / 0.14, you have %s" % awkward.__version__)

        awkd_table = awkward.fromiter([tree_data])
        awkward.save(output_filename, awkd_table, mode='w', compression=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filename",
                        help='ROOT Ntuple filename')

    output_fmts = ['.awkd', '.hdf5']
    parser.add_argument("output",
                        help="Output filename. Must be one of [%s] file extensions (.awkd recommended)" % ', '.join(output_fmts))
    default_tree = "AnalysisTree"
    parser.add_argument("--treeName",
                        help="Name of TTree, defaults to %s" % default_tree,
                        default=default_tree)
    parser.add_argument("--classJson",
                        help="Output class info JSON filename",
                        default=None)
    parser.add_argument("--verbose", "-v",
                        help="Printout extra info",
                        action='store_true')
    args = parser.parse_args()

    if not os.path.isfile(args.filename):
        raise IOError("Cannot find filename %s" % args.filename)

    if not any(x in os.path.splitext(args.output)[1] for x in output_fmts):
        raise IOError("Output file should be %s" % ', '.join(output_fmts))

    flatten_ntuple_write(input_filename=args.filename, tree_name=args.treeName,
                         output_filename=args.output, class_json_filename=args.classJson,
                         verbose=args.verbose)
