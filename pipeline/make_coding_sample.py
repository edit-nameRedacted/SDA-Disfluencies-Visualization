#!/usr/bin/env python3
"""Draw a blind sample of utterances for hand coding the five sentence types.

Reads the files written by extract_swda.py and writes two CSV files:

  coding_sample.csv   what the coder sees: each utterance in plain words, with the
                      two utterances before it and the one after it for context,
                      and an empty "code" column. It does not contain the script's type.
  coding_key.csv      the answer key: which call and utterance each item is, and the
                      type the script gave it. Keep it closed until coding is done.

The sample is stratified: the same number of utterances from each of the script's
five types, so that rare types are checked as carefully as common ones. Items are
then put in random order. The draw uses a fixed seed, so running this again on the
same data gives exactly the same sample.

Usage:  python make_coding_sample.py --data swda_d3 --out . --per-type 60 --seed 19911103

A second sample that shares no utterance with an earlier one: pass the earlier key,
and a new seed. The second sample after the rule revision was drawn with
        python make_coding_sample.py --data swda_d3 --out sample2 --seed 20261011 --exclude coding_key.csv
Needs only the Python standard library.
"""
import argparse
import collections
import csv
import json
import os
import random

TYPES = ("complete_fluent", "complete_disfluent", "unfinished", "fragment", "response_token")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="swda_d3", help="folder written by extract_swda.py")
    ap.add_argument("--out", default=".", help="where to write the two CSV files")
    ap.add_argument("--per-type", type=int, default=60, help="utterances to draw from each type")
    ap.add_argument("--seed", type=int, default=19911103)
    ap.add_argument("--exclude", action="append", default=[],
                    help="an earlier coding_key.csv whose utterances must not be drawn again (can be given more than once)")
    args = ap.parse_args()

    # 0. Utterances already used in an earlier sample.
    used = set()
    for path in args.exclude:
        with open(path, newline="", encoding="utf8") as f:
            used |= {(int(r["conversation_no"]), int(r["utterance_order"])) for r in csv.DictReader(f)}

    # 1. Every typed utterance with at least one word, grouped by the script's type.
    by_type = collections.defaultdict(list)
    population = collections.Counter()
    with open(os.path.join(args.data, "utterances.csv"), newline="", encoding="utf8") as f:
        for row in csv.DictReader(f):
            if row["sentence_type"] in TYPES and int(row["words"]) > 0 \
                    and (int(row["conversation_no"]), int(row["order"])) not in used:
                by_type[row["sentence_type"]].append((int(row["conversation_no"]), int(row["order"]), row["speaker"]))
                population[row["sentence_type"]] += 1

    # 2. Draw the same number from each type, then shuffle everything together.
    rng = random.Random(args.seed)
    drawn = []
    for kind in TYPES:
        pool = sorted(by_type[kind])
        for call, order, speaker in rng.sample(pool, args.per_type):
            drawn.append({"conversation_no": call, "order": order, "speaker": speaker, "script_type": kind})
    rng.shuffle(drawn)

    # 3. The plain words of each utterance and its neighbours, from the call's own file.
    calls = {}

    def utterances_of(call):
        """All utterances of a call that have words, in spoken order: (id, speaker, words)."""
        if call not in calls:
            with open(os.path.join(args.data, "conversations", "%d.json" % call), encoding="utf8") as f:
                conversation = json.load(f)
            joined = collections.OrderedDict()                 # an utterance cut in two by the other speaker is joined back
            for turn in conversation["turns"]:
                for piece in turn["u"]:
                    if piece["w"]:
                        entry = joined.setdefault(piece["id"], [turn["s"], []])
                        entry[1].extend(word for word, _ in piece["w"])
            calls[call] = [(uid, speaker, " ".join(words)) for uid, (speaker, words) in joined.items()]
        return calls[call]

    def line(entry):
        return "%s: %s" % (entry[1], entry[2]) if entry else ""

    sample, key = [], []
    for number, item in enumerate(drawn, start=1):
        utterances = utterances_of(item["conversation_no"])
        at = next(i for i, u in enumerate(utterances) if u[0] == item["order"])
        get = lambda i: utterances[i] if 0 <= i < len(utterances) else None
        sample.append({"item": number, "before_2": line(get(at - 2)), "before_1": line(get(at - 1)),
                       "utterance": line(utterances[at]), "after_1": line(get(at + 1)), "code": "", "notes": ""})
        key.append({"item": number, "conversation_no": item["conversation_no"], "utterance_order": item["order"],
                    "speaker": item["speaker"], "script_type": item["script_type"],
                    "words": len(utterances[at][2].split())})

    for name, rows in (("coding_sample.csv", sample), ("coding_key.csv", key)):
        with open(os.path.join(args.out, name), "w", newline="", encoding="utf8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    print("Drew %d utterances (%d per type) from %d typed utterances." % (len(drawn), args.per_type, sum(population.values())))
    print("Typed utterances by type:", dict(population))


if __name__ == "__main__":
    main()
