#!/usr/bin/env python3
"""Copy the files the page reads from the extraction output into site/.

The page needs only two things: conversations.csv, and one JSON file per call
for the calls that have sentence types (the 650 calls with Treebank parses).
extract_swda.py writes much more than that (all 1,155 calls, and the
utterance, turn and speaker tables), so this script picks out what the page
uses and leaves the rest in pipeline/output/.

Usage:  python publish_site.py --data output --site ../site
Needs only the Python standard library.
"""
import argparse
import csv
import os
import shutil


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="output", help="folder written by extract_swda.py")
    ap.add_argument("--site", default=os.path.join("..", "site"), help="the site folder holding index.html")
    args = ap.parse_args()

    with open(os.path.join(args.data, "conversations.csv"), newline="", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    # A call has sentence types when any of its stw_ (sentence-type word) columns is above zero.
    typed = [r["conversation_no"] for r in rows
             if sum(float(r[c] or 0) for c in r if c.startswith("stw_")) > 0]

    target = os.path.join(args.site, "conversations")
    os.makedirs(target, exist_ok=True)
    shutil.copy(os.path.join(args.data, "conversations.csv"), args.site)
    for number in typed:
        shutil.copy(os.path.join(args.data, "conversations", number + ".json"), target)
    print("Copied conversations.csv and %d call files into %s" % (len(typed), args.site))


if __name__ == "__main__":
    main()
