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
# By Pontus Lurcock, 2022-2026. Released into the public domain.

import sys
import subprocess
import argparse
import tempfile
import os
import unicodedata


def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML clipboard contents to org-mode format"
    )
    parser.add_argument(
        "-s",
        "--stdout",
        help="Output to standard output, not clipboard",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--remove-links",
        help="Remove hyperlinks (i.e. turn them into normal text)",
        action="store_true",
    )
    args = parser.parse_args()

    # Can't user pyperclip here, since it currently (2022-09-24) only
    # handles plain text.
    xclip_in = subprocess.run(
        ["xclip", "-selection", "primary", "-target", "text/html", "-out"],
        check=True,
        capture_output=True,
    )

    # TODO: run xclip_in.stdout through bs4 to remove Wikipedia reference
    #   links. They look like <sup id=cite_ref-foo-bar class=reference>
    #   <a href=#cite_note-foo-bar>[3]</a></sup>
    #   Unfortunately impossible in pandoc.

    with tempfile.TemporaryDirectory() as tmpdir:
        pandoc_args = ["pandoc", "--from=html", "--to=org", "--wrap=none"]
        if args.remove_links:
            path = os.path.join(tmpdir, "filter.lua")
            with open(path, "w") as fh:
                fh.write(
                    "function Link(el)\n" "    return el.content\n" "end\n"
                )
            pandoc_args.append("--lua-filter=" + path)

        pandoc = subprocess.run(
            # pandoc makes some unnecessary string substitutions, e.g. "…" ->
            # "...", but there seems to be no way to disable this as of
            # 2022-10-23. See escapeString in Org.hs in pandoc source.
            pandoc_args,
            # pandoc output sometimes seems to resist NFC normalization.
            # I'm not sure why. See "Magaleña" in
            # https://www.cervezavictoria.es/en/the-beer-of-malaga for
            # an example. Applying NFC normalization before pandoc
            # conversion seems to get around this.
            input=unicodedata.normalize(
                "NFC", xclip_in.stdout.decode()
            ).encode(),
            check=True,
            capture_output=True,
        )

    # A second NFC normalization is probably unnecessary, but no harm
    # in applying it just in case something got denormalized in the
    # pandoc conversion. In the same step, we remove soft hyphens.
    result = unicodedata.normalize("NFC", pandoc.stdout.decode()).replace(
        "\N{SOFT HYPHEN}", ""
    )

    if args.stdout:
        sys.stdout.write(result)
    else:
        subprocess.run(
            # "-loops 2" is specified because in practice (at least on my
            # system) something seems to read the clipboard as soon as it's
            # updated, so "-loops 2" is required to keep xclip running until
            # the user pastes from the clipboard.
            [
                "xclip",
                "-target",
                "UTF8_STRING",
                "-in",
                "-verbose",
                "-selection",
                "clipboard",
                "-loops",
                "2",
            ],
            check=True,
            input=result.encode(),
        )


if __name__ == "__main__":
    main()
