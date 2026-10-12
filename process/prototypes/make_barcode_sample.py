#!/usr/bin/env python3
"""Build the small data file behind the barcode proof of concept.

Reads the output folder written by extract_swda.py and writes one JSON file:
one record per sample conversation, one entry per utterance in spoken order.

    python make_barcode_sample.py swda_d3 barcode_sample.json
"""
import csv, json, os, sys

SAMPLE = [3111, 3038, 3688, 4378, 2314, 2597, 3727, 3082, 3467, 3403]
TYPES = ["complete_fluent", "complete_disfluent", "unfinished", "fragment", "response_token"]
DISFLUENT = {"fp", "et", "rp", "fr"}
TOPIC_FIXES = {"Middle east": "Middle East", "Tv programs": "TV programs"}


def main(src, dest):
    out = []
    for conv in SAMPLE:
        doc = json.load(open(os.path.join(src, "conversations", "%d.json" % conv)))
        utts = {}                     # utterance id -> merged record, in spoken order
        for turn in doc["turns"]:
            for piece in turn["u"]:
                u = utts.setdefault(piece["id"], {"s": turn["s"], "st": piece["st"], "w": []})
                u["w"].extend(piece["w"])
        cells = []
        for uid in sorted(utts):
            u = utts[uid]
            if not u["st"] or not u["w"]:
                continue              # laughter and other units with no parsed words
            cells.append({
                "s": u["s"], "t": TYPES.index(u["st"]), "n": len(u["w"]),
                "txt": " ".join(tok for tok, _ in u["w"]),
                "d": "".join("1" if cls in DISFLUENT else "0" for _, cls in u["w"]),
            })
        topic = doc["topic"].capitalize()
        out.append({"id": conv, "topic": TOPIC_FIXES.get(topic, topic),
                    "year": doc["date"][:4], "u": cells})
    json.dump({"types": TYPES, "conversations": out}, open(dest, "w"), separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
