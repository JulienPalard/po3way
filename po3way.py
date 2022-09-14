#!/usr/bin/env python3

"""git custom merge driver for po files.

# Usage

In a `.gitattributes` files in your repo, write:

    *.po merge=po3way

In your .git/config or .gitconfig:

    [merge "po3way"]
        name = po file merge driver
        driver = po3way --git-merge-driver -- %A %O %B
"""

import argparse
from pathlib import Path
import re
from tempfile import mkdtemp
from shutil import rmtree
from subprocess import run, PIPE
import sys


__version__ = "0.1"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--git-merge-driver",
        action="store_true",
        help="Work as a git merge driver by leaving the result of the merge "
        "in the local file.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Do not delete temporary working directory for later introspection.",
    )
    parser.add_argument("local", type=Path)
    parser.add_argument("base", type=Path)
    parser.add_argument("remote", type=Path)
    return parser.parse_args()


def unwrap(text):
    lines = text.split("\n")
    output = []
    for line in lines:
        if not line:
            output.append("")
            continue
        if line[0] == line[-1] == '"':
            output[-1] += "\x1e" + line
        else:
            output.append(line)
    return "\n".join(output)


def rewrap(text):
    return text.replace("\x1e", "\n")


def get_header(text, header):
    for line in text.splitlines():
        if header in line:
            return line


def is_pot_local(text):
    """Tell if the pot is fresher in local or remote.

    Given a conflicting po file returns:
    - True if the pot if fresher in 'local'.
    - False if the pot is fresher in 'remote'.
    - None if it can't tell.
    """
    header_match = re.search(
        "^<<<<<<<.*?$(.*?POT-Creation-Date.*?)\n^>>>>>>>.*?$",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    if header_match is None:
        return False, text
    header = header_match.group(1)
    header = re.sub(
        r"^\|\|\|\|\|\|\|.*^=======", "=======", header, flags=re.DOTALL | re.MULTILINE
    )
    local, remote = re.split("^=======\n", header, maxsplit=1, flags=re.MULTILINE)
    if "POT-Creation-Date" not in local or "POT-Creation-Date" not in remote:
        return None
    return get_header(local, "POT-Creation-Date") > get_header(
        remote, "POT-Creation-Date"
    )


def simple_merge(text, pot_is_local):
    """Automatically merge simple conflicts like:

    <<<<<<< /tmp/tmp2g34f2cz/local.po
    #: library/exceptions.rst:732
    #, fuzzy
    ||||||| /tmp/tmp2g34f2cz/base.po
    #: library/exceptions.rst:724
    #, fuzzy
    =======
    #: library/exceptions.rst:724
    >>>>>>> /tmp/tmp2g34f2cz/remote.po
    """
    qty = 0
    if pot_is_local:
        # Keep line number from local, the rest from remote.
        text, qty = re.subn(
            r"""^<<<<<<<\ [^\n]*\n
                (\#:[^\n]+)\n
                \#,\ fuzzy\n
                (?:\|\|\|\|\|\|\|\ [^\n]*\n
                   \#:\ [^\n]*\n
                   \#,\ fuzzy\n)?
                ^=======\n
                \#:\ [^\n]*\n
                ^>>>>>>>[^\n]*$""",
            r"\1",
            text,
            flags=re.MULTILINE | re.VERBOSE,
        )
    return text, qty


def merge_header(text):
    header_match = re.search(
        "^<<<<<<<.*?$(.*?PO-Revision-Date.*?)\n^>>>>>>>.*?$",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    if header_match is None:
        return False, text
    header = header_match.group(1)
    header = re.sub(
        r"^\|\|\|\|\|\|\|.*^=======", "=======", header, flags=re.DOTALL | re.MULTILINE
    )
    old, new = re.split("^=======\n", header, maxsplit=1, flags=re.MULTILINE)
    if "PO-Revision-Date" not in old or "PO-Revision-Date" not in new:
        return False, text
    if "POT-Creation-Date" not in old or "POT-Creation-Date" not in new:
        return False, text
    if get_header(old, "PO-Revision-Date").replace("YEAR", "0000") > get_header(
        new, "PO-Revision-Date"
    ):
        old, new = new, old
    pot_creation_date = max(
        get_header(old, "POT-Creation-Date"), get_header(new, "POT-Creation-Date")
    )
    new = new.replace(get_header(new, "POT-Creation-Date"), pot_creation_date)
    return True, text[: header_match.start()] + new + text[header_match.end() :]


def main():
    args = parse_args()
    tmpdir_name = mkdtemp()
    tmpdir = Path(tmpdir_name)

    (tmpdir / "local.po").write_text(unwrap(args.local.read_text()))
    (tmpdir / "base.po").write_text(unwrap(args.base.read_text()))
    (tmpdir / "remote.po").write_text(unwrap(args.remote.read_text()))
    git_merge_file = run(
        [
            "git",
            "merge-file",
            "-p",
            str(tmpdir / "local.po"),
            str(tmpdir / "base.po"),
            str(tmpdir / "remote.po"),
        ],
        check=False,
        encoding="UTF-8",
        stdout=PIPE,
    )
    merged = rewrap(git_merge_file.stdout)
    if args.debug:
        (tmpdir / "git-merge-file").write_text(merged)
    pot_is_local = is_pot_local(merged)
    has_merged, merged = merge_header(merged)
    if pot_is_local is not None:
        merged, qty_merged = simple_merge(merged, pot_is_local)
        git_merge_file.returncode -= qty_merged
    if git_merge_file.returncode > 0 and has_merged:
        git_merge_file.returncode -= 1
    if args.git_merge_driver:
        args.local.write_text(merged)
    else:
        print(merged, end="")
    if not args.debug:
        rmtree(tmpdir_name)
    sys.exit(git_merge_file.returncode)


if __name__ == "__main__":
    main()
