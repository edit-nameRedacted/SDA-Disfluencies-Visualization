#!/usr/bin/env python3
"""Give every utterance of the dialog-act corpus a start and end time, from the
Mississippi State (MS98) word alignments of Switchboard.

The two sources transcribe the same calls but were corrected separately, so their
words differ here and there. For each call and each speaker (channel A or B), the
script lines up the two word sequences with Python's difflib (longest matching
blocks) after normalising both sides the same way:

  - lower case, punctuation stripped
  - MS98 word fragments "h[ow]-" become "h-"; SWDA fragments are already "h-"
  - MS98 "[laughter-yeah]" (a word said while laughing) becomes "yeah"
  - MS98 "because_1" (a pronunciation variant) becomes "because"
  - MS98 non-speech ([silence], [noise], [laughter], [vocalized-noise]) is kept
    aside as timed gaps, not words

Some calls have channels A and B the other way round in one source; both pairings
are tried and the one matching more words is kept (call_timing_match.csv records it).
Calls where under 80% of words match get no times at all.

An utterance's start is the start time of its first matched word and its end the end
time of its last matched word. Utterances with no matched word get no times.

Written per utterance (utterance_timing.csv):
  start, end            seconds from the start of the recording
  matched, words        how many of its words were matched to a timed word
  silence_inside        seconds of MS98 [silence] between its first and last word
  long_pauses_inside    silences inside of 0.5 s or more
  gap_before            for an utterance that starts a response (the speaker changed in
                        the transcript): its start minus the end of the other speaker's
                        stretch of speech (a run of words between MS98 silences) that began
                        last before it. Negative: it started while the other was still
                        talking. Read off the MS98 timings alone; only given when the
                        utterance's first word was matched inside a run of at least two
                        matching words, so a lone "uh-huh" matched to the wrong
                        occurrence cannot produce a gap. Left blank when the timings show
                        this speaker talked more recently than the other (the turn in
                        between, often a backchannel, was not timed).

Usage:  python align_timing.py --data output --ms98 corpus/swb_ms98_transcriptions --out output/utterance_timing.csv
Standard library only.
"""
import argparse
import collections
import csv
import difflib
import glob
import json
import os
import re

NONSPEECH = {"[silence]", "[noise]", "[laughter]", "[vocalized-noise]"}


def norm_ms98(token):
    t = token.lower()
    m = re.match(r"^\[laughter-(.+)\]$", t)
    if m:
        t = m.group(1)
    t = re.sub(r"_\d+$", "", t)                      # because_1 -> because
    t = re.sub(r"\[[^\]]*\]-$", "-", t)              # h[ow]- -> h-
    t = re.sub(r"^-\[[^\]]*\]", "-", t)              # -[th]at -> -at
    t = re.sub(r"[\[\]{}]", "", t)
    return t.strip(".,?!")


def norm_swda(word):
    return word.lower().strip(".,?!{}[]()/#")


def ms98_tokens(path):
    """Timed words, timed silences, and stretches of speech (runs of words between silences)."""
    words, silences, runs = [], [], []
    for line in open(path, encoding="latin-1"):
        p = line.split()
        if len(p) < 4:
            continue
        start, end, tok = float(p[1]), float(p[2]), " ".join(p[3:])
        if tok.lower() == "[silence]":
            silences.append((start, end))
            continue
        if tok.lower() in NONSPEECH:
            continue
        words.append((norm_ms98(tok), start, end))
        if runs and runs[-1][1] >= start - 1e-6 and not (silences and silences[-1][0] >= runs[-1][1] - 1e-6):
            runs[-1][1] = end
        else:
            runs.append([start, end])
    return words, silences, runs


def gap_from(runs, t):
    """Seconds from the end of the other speaker's speech to time t. The relevant stretch
    is the last one that began before t. Negative: t falls inside it (overlap)."""
    last = None
    for a, b in runs:
        if a < t:
            last = (a, b)
        else:
            break
    return None if last is None else t - last[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="output")
    ap.add_argument("--ms98", default=os.path.join("corpus", "swb_ms98_transcriptions"))
    ap.add_argument("--out", default=os.path.join("output", "utterance_timing.csv"))
    ap.add_argument("--calls-out", default=os.path.join("output", "call_timing_match.csv"))
    ap.add_argument("--min-match", type=float, default=0.8,
                    help="calls whose words match below this share get no times at all")
    args = ap.parse_args()

    typed = set()
    with open(os.path.join(args.data, "utterances.csv"), newline="", encoding="utf8") as f:
        for r in csv.DictReader(f):
            if r["sentence_type"]:
                typed.add(r["conversation_no"])

    rows, report, call_report = [], collections.Counter(), []
    for call in sorted(typed, key=int):
        with open(os.path.join(args.data, "conversations", "%s.json" % call), encoding="utf8") as f:
            conv = json.load(f)
        order, utt_words, speaker_of = [], collections.defaultdict(list), {}
        for turn in conv["turns"]:
            for piece in turn["u"]:
                if piece["id"] not in speaker_of:
                    order.append(piece["id"])
                    speaker_of[piece["id"]] = turn["s"]
                utt_words[piece["id"]].extend(norm_swda(w) for w, _ in piece["w"] if norm_swda(w))
        # Some calls have the two channels the other way round in one of the sources, so try
        # both pairings and keep the one that matches more words.
        best = None
        for pairing in ({"A": "A", "B": "B"}, {"A": "B", "B": "A"}):
            timing, n_words, n_matched, ok, runs_of = {}, 0, 0, True, {}
            for side in ("A", "B"):
                files = glob.glob(os.path.join(args.ms98, "*", call, "sw%s%s-ms98-a-word.text" % (call, pairing[side])))
                if not files:
                    ok = False
                    break
                ms_words, silences, runs = ms98_tokens(files[0])
                runs_of[side] = runs
                seq, owner = [], []
                for uid in order:
                    if speaker_of[uid] == side:
                        for w in utt_words[uid]:
                            seq.append(w); owner.append(uid)
                sm = difflib.SequenceMatcher(None, seq, [w for w, _, _ in ms_words], autojunk=False)
                matched = {}
                for a, b, n in sm.get_matching_blocks():
                    for k in range(n):
                        matched[a + k] = ms_words[b + k] + (n,)    # keep the length of the matching block
                n_words += len(seq); n_matched += len(matched)
                by_utt = collections.defaultdict(list)
                for i, uid in enumerate(owner):
                    if i in matched:
                        by_utt[uid].append(matched[i])
                for uid in order:
                    if speaker_of[uid] != side:
                        continue
                    hits = by_utt.get(uid, [])
                    rec = {"words": len(utt_words[uid]), "matched": len(hits)}
                    if hits:
                        s0, e0 = hits[0][1], hits[-1][2]
                        inside = [(a, b) for a, b in silences if a >= s0 and b <= e0]
                        rec.update(start=round(s0, 3), end=round(e0, 3), start_sure=int(hits[0][3] >= 2),
                                   silence_inside=round(sum(b - a for a, b in inside), 3),
                                   long_pauses_inside=sum(1 for a, b in inside if b - a >= 0.5))
                    timing[uid] = rec
            if ok and (best is None or n_matched > best[2]):
                best = (timing, n_words, n_matched, pairing["A"] != "A", runs_of)
        if best is None:
            report["channel missing"] += 1
            continue
        timing, n_words, n_matched, swapped, runs_of = best
        share = n_matched / max(1, n_words)
        report["words"] += n_words; report["matched"] += n_matched
        report["swapped"] += swapped
        call_report.append({"conversation_no": call, "words": n_words, "matched_share": round(share, 3),
                            "channels_swapped": int(swapped), "usable": int(share >= args.min_match)})
        if share < args.min_match:
            report["calls below threshold"] += 1
            timing = {}                                    # too poor a match to trust any time in this call
        prev_speaker = None
        for uid in order:
            rec = timing.get(uid, {"words": len(utt_words[uid]), "matched": 0})
            sp = speaker_of[uid]
            other = "B" if sp == "A" else "A"
            gap = ""
            if prev_speaker is not None and sp != prev_speaker and rec.get("start_sure"):
                g = gap_from(runs_of.get(other, []), rec["start"])
                own = gap_from([r for r in runs_of.get(sp, []) if r[1] <= rec["start"] + 1e-6], rec["start"])
                # If this speaker talked more recently than the other did, the timings show no
                # change of speaker here (the other's turn in between was not timed), so no gap.
                if g is not None and not (own is not None and g > 0 and own < g):
                    gap = round(g, 3)
            rows.append({"conversation_no": call, "utterance": uid, "speaker": sp,
                         "start": rec.get("start", ""), "end": rec.get("end", ""),
                         "words": rec["words"], "matched": rec["matched"],
                         "silence_inside": rec.get("silence_inside", ""),
                         "long_pauses_inside": rec.get("long_pauses_inside", ""),
                         "gap_before": gap})
            if utt_words[uid]:
                prev_speaker = sp

    with open(args.out, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(args.calls_out, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(call_report[0])); w.writeheader(); w.writerows(call_report)
    timed = sum(1 for r in rows if r["start"] != "")
    print("calls:", len(typed), "| utterances:", len(rows), "| with times:", timed,
          "| words matched: %.1f%%" % (100 * report["matched"] / max(1, report["words"])),
          "| channels missing:", report["channel missing"], "| calls with channels swapped:", report["swapped"],
          "| calls below match threshold:", report["calls below threshold"])


if __name__ == "__main__":
    main()
