#!/usr/bin/env python

"""
Parse the github patch and provide relevant info
e.g. files changed, new files, deleted files

Each file in the diff is represented by a FileDiff object with meta info.
The FileDiff object holds a list of changes in the file, each one represented by
a ContentsChange object.
Each ContentsChange object holds the relevant lines of text, each represented by
a Line object. This also stores if the Line is same, only in new, or only in old.
"""


import sys


class FileDiff(object):
    """Store all changes and info for one file in the diff"""

    def __init__(self, old_filename, new_filename, old_hash=None, new_hash=None, mode=-1, is_new=False, changes=None):
        self.old_filename = old_filename
        self.new_filename = new_filename
        self.old_hash = old_hash
        self.new_hash = new_hash
        self.mode = mode
        self.is_new = is_new
        self.changes = changes or []


class ContentsChange(object):
    """Store one change in a file"""

    def __init__(self, old_loc, new_loc, lines=None):
        self.old_loc = old_loc
        self.new_loc = new_loc
        self.lines = lines or []

    def get_new_lines(self):
        for line in self.lines:
            if line.is_new_line():
                yield line

    def get_old_lines(self):
        for line in self.lines:
            if line.is_new_line():
                yield line


class LineChange(object):
    """Store info about a line change in a diff"""

    def __init__(self, line):
        if len(line) == 0:
            raise IndexError("LineChange needs a line at least length 1")
        self.line_start = line[0]
        if len(line) > 1:
            self.line_contents = line[1:]
        else:
            self.line_contents = ""

    def is_common_line(self):
        return self.line_start == " "

    def is_new_line(self):
        return self.line_start == "+"

    def is_old_line(self):
        return self.line_start == "-"


def parse_diff(filename):
    """Parse the diff, returning a FileDiff object for each changed file in the diff"""

    START_OF_DIFF = "diff --git"

    diff_files = []
    with open(filename) as f:
        current_file = None
        current_change = None
        # use iterator as we sometimes want to advance forward a line only
        # inside certain bits of logic
        fiter = iter(f)
        line = next(fiter).strip()
        try:
            while True:
                if line.startswith(START_OF_DIFF):
                    parts = line.split()
                    # is this the actual old/new filenames? 
                    # what about the --- and +++
                    old_filename = parts[2].strip().lstrip("a/")
                    new_filename = parts[3].strip().lstrip("b/")

                    # take care of previous iteration
                    if current_change:
                        current_file.changes.append(current_change)
                        current_change = None
                    if current_file:
                        diff_files.append(current_file)

                    # now deal with this new file
                    current_file = FileDiff(old_filename, new_filename)

                    line = next(fiter).strip()
                    if line.startswith('new file'):
                        # new file mode 100755
                        parts = line.split()
                        current_file.mode = int(parts[-1].strip())
                        current_file.is_new = True
                        line = next(fiter).strip()

                    if line.startswith('index'):
                        # index 00000000..17e9cf72
                        # index c76bc0ee..9ab85598 100755
                        parts = line.split()
                        if ".." not in line or len(parts) < 2:
                            raise IndexError("The index line is incorrect format")
                        current_file.old_hash, current_file.new_hash = parts[1].split("..")
                        if len(parts) == 3:
                            current_file.mode = int(parts[-1].strip())

                    line = next(fiter).strip()

                elif line.startswith("--- "):
                    parts = line.split()
                    current_file.old_filename = parts[-1].lstrip('a/')
                    line = next(fiter).strip()

                elif line.startswith("+++ "):
                    parts = line.split()
                    current_file.new_filename = parts[-1].lstrip('b/')
                    line = next(fiter).strip()

                else:
                    # parsing file info done, now for actual changes
                    while not line.startswith(START_OF_DIFF):
                        if line.startswith("@@"):
                            if current_change:
                                current_file.changes.append(current_change)
                            parts = line.split()
                            # @@ -138,6 +136,6 @@ time scram b $MAKEFLAGS
                            old_loc = [int(i.lstrip("-+")) for i in parts[1].split(",")]
                            new_loc = [int(i.lstrip("-+")) for i in parts[2].split(",")]
                            current_change = ContentsChange(old_loc, new_loc)
                            # get the bit of string after the 2nd @@
                            if line.count("@@") == 2 and not line.endswith("@@"):
                                line = line[2:]
                                pos = line.index("@@")
                                this_line = LineChange(line[pos+2:].rstrip("\n"))
                                current_change.lines.append(this_line)
                            line = next(fiter)  # don't .strip() as we need first space
                        else:
                            # the actual contents of the diff
                            this_line = LineChange(line.rstrip("\n"))
                            current_change.lines.append(this_line)
                            line = next(fiter)  # don't .strip() as we need first space

        except StopIteration:
            if current_change:
                current_file.changes.append(current_change)
            if current_file:
                diff_files.append(current_file)

    return diff_files


def main(in_args):
    diff_files = parse_diff(in_args[0])

    for f in diff_files:
        print(f.new_filename, f.is_new, f.mode, f.old_hash, f.new_hash)
        for c in f.changes:
            print(c.old_loc, c.new_loc)
            # for l in c.get_new_lines():
                # print(l)
            # for l in c.lines:
                # print(l.line_contents.rstrip("\n"))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
