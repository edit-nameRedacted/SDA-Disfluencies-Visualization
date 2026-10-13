#!/usr/bin/env python3
"""Fold the timing and repair results into the files the page reads.

Run after extract_swda.py, align_timing.py and detect_repair.py. It adds, by rule:

To each call's conversations/<id>.json, on the pieces of talk:
  "g"   on the first piece of an utterance that starts a response: the gap before it
        in seconds (negative: it started while the other speaker was still talking).
        From utterance_timing.csv, column gap_before.
  "pz"  long pauses (0.5 s or more) inside the piece, as [index of the word before the
        pause within this piece, seconds]. From utterance_timing.csv, column pauses.
  "ri"  on the first piece of an utterance flagged as a repair initiation:
        {"r": rule, "s": strength, "t": id of the trouble-source utterance}.
        From repair_initiations.csv.

To conversations.csv, five columns per call (only for calls with timings):
  effort_words   words in utterances holding a filled pause (uh, um), a repeated or
                 reworded stretch, or a cut-off word: the corpus's own marks
  pause_words    words in utterances holding a silence of 0.5 s or more between two words
  long_gaps      changes of speaker with a gap of 1 s or more
  transitions    changes of speaker with a measured gap
  repair_inits   utterances flagged as repair initiations

Usage:  python add_timing.py --data output --timing output/utterance_timing.csv --repair output/repair_initiations.csv
The files in --data are rewritten in place; running it again gives the same result.
Standard library only.
"""
import argparse
import collections
import csv
import json
import os

EFFORT_CLASSES = {"fp", "rp", "fr"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="output")
    ap.add_argument("--timing", default=os.path.join("output", "utterance_timing.csv"))
    ap.add_argument("--repair", default=os.path.join("output", "repair_initiations.csv"))
    args = ap.parse_args()

    timing = collections.defaultdict(dict)
    with open(args.timing, newline="", encoding="utf8") as f:
        for r in csv.DictReader(f):
            timing[r["conversation_no"]][int(r["utterance"])] = r
    repairs = collections.defaultdict(dict)
    with open(args.repair, newline="", encoding="utf8") as f:
        for r in csv.DictReader(f):
            repairs[r["conversation_no"]][int(r["utterance"])] = r

    per_call = {}
    for call, utts in timing.items():
        path = os.path.join(args.data, "conversations", "%s.json" % call)
        with open(path, encoding="utf8") as f:
            doc = json.load(f)
        seen, offset = set(), collections.Counter()      # words of each utterance already passed
        effort, pause, words_of, classes_of = 0, 0, collections.Counter(), collections.defaultdict(set)
        for turn in doc["turns"]:
            for piece in turn["u"]:
                for key in ("g", "pz", "ri"):
                    piece.pop(key, None)
                uid, t = piece["id"], utts.get(piece["id"])
                n = len(piece["w"])
                first = uid not in seen
                seen.add(uid)
                words_of[uid] += n
                classes_of[uid].update(cls for _, cls in piece["w"])
                if t:
                    if first and t["gap_before"] != "":
                        piece["g"] = round(float(t["gap_before"]), 2)
                    if t["pauses"]:
                        pz = []
                        for item in t["pauses"].split(";"):
                            k, sec = item.split(":")
                            k = int(k) - offset[uid]
                            if 0 <= k < n - 1:                     # a pause between two words of this piece
                                pz.append([k, float(sec)])
                        if pz:
                            piece["pz"] = pz
                rep = repairs[call].get(uid)
                if rep and first:
                    piece["ri"] = {"r": rep["rule"], "s": rep["strength"], "t": int(rep["trouble_utterance"])}
                offset[uid] += n
        for uid, n in words_of.items():
            if classes_of[uid] & EFFORT_CLASSES:
                effort += n
            t = utts.get(uid)
            if t and t["long_pauses_inside"] not in ("", "0"):
                pause += n
        gaps = [float(t["gap_before"]) for t in utts.values() if t["gap_before"] != ""]
        per_call[call] = {"effort_words": effort, "pause_words": pause,
                          "long_gaps": sum(1 for g in gaps if g >= 1.0), "transitions": len(gaps),
                          "repair_inits": len(repairs[call])}
        with open(path, "w", encoding="utf8") as f:
            json.dump(doc, f, separators=(",", ":"))

    path = os.path.join(args.data, "conversations.csv")
    with open(path, newline="", encoding="utf8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = [c for c in reader.fieldnames if c not in ("effort_words", "pause_words", "long_gaps", "transitions", "repair_inits")]
    fields += ["effort_words", "pause_words", "long_gaps", "transitions", "repair_inits"]
    for r in rows:
        extra = per_call.get(r["conversation_no"], {})
        for c in ("effort_words", "pause_words", "long_gaps", "transitions", "repair_inits"):
            r[c] = extra.get(c, "")
    with open(path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("calls updated:", len(per_call))


if __name__ == "__main__":
    main()
