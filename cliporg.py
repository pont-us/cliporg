#!/usr/bin/env python3

# cliporg: convert HTML text on the X clipboard to emacs org mode format.
#
# Useful when copy-pasting material from a web page into an org file.
#
# This utility reads HTML from the X clipboard, converts it to org mode
# syntax, and writes it back to the X clipboard (overwriting the original
# HTML with the org version).
#
# Requires xclip and pandoc.
#
# By Pontus Lurcock, 2022. Released into the public domain.

import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML clipboard contents to org-mode format"
    )
    parser.add_argument(
        "-s", "--stdout",
        help="Output to standard output, not clipboard",
        action="store_true"
    )
    args = parser.parse_args()

    # Can't user pyperclip here, since it currently (2022-09-24) only
    # handles plain text.
    xclip_in = subprocess.run(
        ["xclip", "-selection", "primary", "-target", "text/html", "-out"],
        check=True,
        capture_output=True
    )

    pandoc = subprocess.run(
        # pandoc makes some unnecessary string substitutions, e.g. "…" ->
        # "...", but there seems to be no way to disable this as of
        # 2022-10-23. See escapeString in Org.hs in pandoc source.
        ["pandoc", "--from=html", "--to=org", "--wrap=none"],
        input=xclip_in.stdout,
        check=True,
        capture_output=True
    )

    if args.stdout:
        sys.stdout.write(pandoc.stdout.decode())
    else:
        subprocess.run(
        # "-loops 2" is specified because in practice (at least on my
        # system) something seems to read the clipboard as soon as it's
        # updated, so "-loops 2" is required to keep xclip running until
        # the user pastes from the clipboard.
        ["xclip", "-target", "UTF8_STRING", "-in", "-verbose",
         "-selection", "clipboard", "-loops", "2"],
        check=True,
        input=pandoc.stdout
    )
    

if __name__ == "__main__":
    main()
