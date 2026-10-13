#!/usr/bin/env python3
"""Draw a blind sample for hand-checking the repair-initiation detector.

Reads the response file written by detect_repair.py (--responses): one row for every
utterance that opens a speaker's response. Draws four groups, so that both kinds of
error can be measured:

  flagged     every utterance flagged by R2, R3 or R4, and up to 60 flagged by R1
              (does the rule catch real repair initiations?)
  near miss   60 unflagged responses of 1 to 6 words marked as questions
              (where missed initiations are most likely to hide)
  other       60 unflagged responses drawn at random from the rest
              (how many initiations hide in ordinary talk?)

Items are shuffled. The coder sees the other speaker's line before, the line to code,
and the other speaker's line after, with no rule or tag. A fixed seed makes the
draw repeatable.

Usage:  python make_repair_sample.py --responses output/repair_responses.csv --utterances output/utterances.csv --out .
Standard library only.
"""
import argparse
import csv
import os
import random


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--responses", required=True)
    ap.add_argument("--utterances", required=True)
    ap.add_argument("--out", default=".")
    ap.add_argument("--seed", type=int, default=20261013)
    ap.add_argument("--per-group", type=int, default=60)
    args = ap.parse_args()

    question = {}
    with open(args.utterances, newline="", encoding="utf8") as f:
        for r in csv.DictReader(f):
            question[(r["conversation_no"], r["order"])] = "?" in r["text"]
    with open(args.responses, newline="", encoding="utf8") as f:
        rows = list(csv.DictReader(f))

    rng = random.Random(args.seed)
    r1 = sorted((r for r in rows if r["rule"] == "R1 tag"), key=lambda r: (int(r["conversation_no"]), int(r["utterance"])))
    groups = {
        "flagged": [r for r in rows if r["rule"] in ("R2 open", "R3 repeat", "R4 check")] + rng.sample(r1, min(args.per_group, len(r1))),
    }
    unflagged = [r for r in rows if not r["rule"] and r["repair"]]
    near = [r for r in unflagged if question[(r["conversation_no"], r["utterance"])] and 1 <= len(r["initiation"].split()) <= 6]
    groups["near miss"] = rng.sample(sorted(near, key=lambda r: (int(r["conversation_no"]), int(r["utterance"]))), args.per_group)
    chosen = {(r["conversation_no"], r["utterance"]) for g in groups.values() for r in g}
    rest = [r for r in unflagged if (r["conversation_no"], r["utterance"]) not in chosen]
    groups["other"] = rng.sample(sorted(rest, key=lambda r: (int(r["conversation_no"]), int(r["utterance"]))), args.per_group)

    items = [(g, r) for g, rs in groups.items() for r in rs]
    rng.shuffle(items)
    other = {"A": "B", "B": "A"}
    sample, key = [], []
    for n, (g, r) in enumerate(items, start=1):
        sample.append({"item": n,
                       "before": "%s: %s" % (other[r["speaker"]], r["trouble"]),
                       "line": "%s: %s" % (r["speaker"], r["initiation"]),
                       "after": "%s: %s" % (other[r["speaker"]], r["repair"]),
                       "code": "", "notes": ""})
        key.append({"item": n, "conversation_no": r["conversation_no"], "utterance": r["utterance"],
                    "group": g, "rule": r["rule"], "strength": r["strength"], "act_tag": r["act_tag"]})
    for name, out in (("repair_coding_sample.csv", sample), ("repair_coding_key.csv", key)):
        with open(os.path.join(args.out, name), "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("items:", len(items), {g: len(rs) for g, rs in groups.items()})


if __name__ == "__main__":
    main()
