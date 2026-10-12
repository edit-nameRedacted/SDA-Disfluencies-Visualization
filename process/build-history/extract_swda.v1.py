#!/usr/bin/env python3
"""
extract_swda.py - turn the Switchboard Dialog Act corpus (SwDA) into D3-ready files.

Input : swda.zip from https://github.com/cgpotts/swda  (or the unzipped folder)
Output: a folder of flat tables plus one JSON file per conversation, organised
        for a three-level zoom: conversations > turns > utterances (> words).

    python extract_swda.py --input swda.zip --out swda_d3
    python extract_swda.py --download --out swda_d3      # fetches swda.zip first

Standard library only (Python 3.8+). Runs in well under a minute.

FILES WRITTEN
  conversations.csv       one row per conversation   (zoom level 1)
  turns.csv               one row per turn           (zoom level 2, flat)
  speakers.csv            one row per speaker per conversation (rate comparisons)
  utterances.csv          one row per utterance      (zoom level 3, flat)
  sentence_units.csv      one row per parsed sentence (parsed subset only)
  fluency_by_length.csv   disfluency by utterance / turn length (fluency curve)
  conversations/<id>.json one conversation, nested: turns > utterances > words
                          (load on click; holds zoom levels 2 and 3)
  summary.json            corpus totals, for checking a run
  schema.json             column and code definitions

Every table stores COUNTS (numerators and denominators). Compute rates in D3 so
that filtered or grouped views pool correctly.

DEFINITIONS
  utterance      a dialog-act unit: one SwDA row plus any later rows tagged "+"
                 (the same speaker continuing after an interruption).
  turn           SwDA's utterance_index: a stretch of talk by one speaker.
  piece          the part of an utterance that falls inside one turn. About 8%
                 of rows continue an utterance begun in an earlier turn, so in
                 the nested JSON each turn lists pieces, each pointing to its
                 utterance (id) and flagged c=1 when it is a continuation.

HOW THE LEVELS ADD UP
  Word counts belong to the turn the words were spoken in. Utterance counts
  (utterances, utt_*, mt_*, st_*) belong to the turn where the utterance
  starts. Words-by-type (mtw_*, stw_*) use the type of the whole utterance.
  Summing turns therefore gives exactly the conversation row, and summing
  the pieces of a turn gives exactly the turn row.
  word classes   fp  filled pause (uh, um and rare variants)
                 et  editing term ("I mean", "excuse me")          {E ...}
                 rp  reparandum: words replaced by a repair        [ rp + repair ]
                 fr  word fragment outside a reparandum ("th-")
                 ij  other interjection in filler markup ("oh", "huh")
                 dm  discourse marker ("well", "you know")          {D ...}
                 cj  utterance-linking conjunction ("and", "but")   {C ...}
                 as  aside                                          {A ...}
                 p   plain
  disfluent word fp, et, rp or fr.
  markup_type    one label per utterance, first match wins:
                 nonverbal > abandoned > disfluent > backchannel > fluent
  sentence_type  from the Treebank parse (about 650 conversations):
                 complete_fluent, complete_disfluent, unfinished,
                 response_token, fragment
"""
import argparse
import collections
import csv
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

SWDA_URL = "https://github.com/cgpotts/swda/raw/master/swda.zip"

# ----------------------------------------------------------------------------
# Markup tokenizer
# ----------------------------------------------------------------------------
TOKEN = re.compile(r"""
    (?P<nonspeech><<[^>]*>>|<[^>]*>)   |   # <laughter>, <<long pause>>
    (?P<brace_open>\{[A-Za-z])         |   # {F {D {E {C {A
    (?P<brace_close>\})                |
    (?P<paren>\(\(|\)\))               |   # (( uncertain transcription ))
    (?P<cont>--)                       |   # continuation marker
    (?P<abandon>-\s*/)                 |   # -/  abandoned slash unit
    (?P<slash>/)                       |   # /   end of slash unit
    (?P<overlap>\#)                    |   # #   overlapping speech
    (?P<rep_open>\[)                   |   # [   repair start
    (?P<rep_close>\])                  |   # ]   repair end
    (?P<ip>\+)                         |   # +   interruption point
    (?P<word>-?[A-Za-z0-9']+(?:-[A-Za-z0-9']+)*-?)
""", re.X)

FILLED_PAUSES = {"uh", "um", "er", "eh", "ah", "hm", "hum", "uh-", "um-"}
DISFLUENT = ("fp", "et", "rp", "fr")
WORD_CLASSES = ("p", "cj", "dm", "ij", "as", "fp", "et", "rp", "fr")
BRACE_CLASS = {"F": "ij", "D": "dm", "C": "cj", "A": "as"}
BACKCHANNEL_TAGS = {"b", "bh", "bk"}
SUBSTANTIVE_TAGS = {"sd", "sv", "qy", "qw", "qo", "qh", "qy^d", "qw^d", "qrr",
                    "ad", "oo_co_cc"}
EDUCATION = {"0": "less than high school", "1": "less than college",
             "2": "college", "3": "more than college", "9": "unknown"}
SENTENCE_TYPES = ("complete_fluent", "complete_disfluent", "unfinished",
                  "response_token", "fragment")
MARKUP_TYPES = ("fluent", "disfluent", "abandoned", "backchannel", "nonverbal")


def damsl_tag(tag):
    """Collapse a fine-grained SwDA tag to the standard ~42-class set
    (same rules as the corpus's own swda.py)."""
    tag = re.split(r"\s*[,;]\s*", tag)[0]
    if tag in ("qy^d", "qw^d", "b^m"):
        return tag
    if tag == "nn^e":
        return "ng"
    if tag == "ny^e":
        return "na"
    tag = re.sub(r"(.)\^.*", r"\1", tag)
    tag = re.sub(r"[\(\)@*]", "", tag)
    if tag in ("qr", "qy"):
        return "qy"
    if tag in ("fe", "ba"):
        return "ba"
    if tag in ("oo", "co", "cc"):
        return "oo_co_cc"
    if tag in ("fx", "sv"):
        return "sv"
    if tag in ("aap", "am"):
        return "aap_am"
    if tag in ("arp", "nd"):
        return "arp_nd"
    if tag in ("fo", "o", "fw", '"', "by", "bc"):
        return "fo_o_fw_by_bc"
    return tag


def parse_row(text, stack):
    """Classify every word in one SwDA row.

    `stack` is the speaker's open-repair stack and is modified in place: one
    False per open "[" that has not reached its "+", True once it has. A word
    is a reparandum while any enclosing repair is still before its "+".

    Returns (words, flags) where words is a list of (token, class).
    """
    text = re.sub(r"\*\[\[.*?\]\]", " ", text)      # annotator comments
    text = re.sub(r"\*\[\[.*$", " ", text)
    braces = []
    words = []
    flags = collections.Counter()
    for m in TOKEN.finditer(text):
        kind, value = m.lastgroup, m.group()
        if kind == "brace_open":
            braces.append(value[1].upper())
        elif kind == "brace_close":
            if braces:
                braces.pop()
        elif kind == "rep_open":
            stack.append(False)
            flags["repairs"] += 1
        elif kind == "ip":
            if stack:
                stack[-1] = True
            flags["ip"] += 1
        elif kind == "rep_close":
            if stack:
                stack.pop()
        elif kind in ("abandon", "overlap"):
            flags[kind] += 1
        elif kind == "word":
            low = value.lower()
            brace = braces[-1] if braces else None
            in_reparandum = any(not passed for passed in stack)
            is_fragment = len(low) > 1 and (low.endswith("-") or low.startswith("-"))
            if (brace == "F" and low in FILLED_PAUSES) or (brace is None and low in ("uh", "um")):
                cls = "fp"
            elif brace == "E":
                cls = "et"
            elif in_reparandum:
                cls = "rp"
            elif is_fragment:
                cls = "fr"
            elif brace in BRACE_CLASS:
                cls = BRACE_CLASS[brace]
            else:
                cls = "p"
            words.append((value, cls))
    return words, flags


# ----------------------------------------------------------------------------
# Treebank parse -> sentence type
# ----------------------------------------------------------------------------
TREE_SKIP_POS = ("-DFL-", "-NONE-", ",", ".", ":", "``", "''")


def strip_edited(tree):
    """Remove (EDITED ...) subtrees so an unfinished reparandum does not make
    the whole sentence count as unfinished."""
    out, i = [], 0
    while i < len(tree):
        if tree.startswith("(EDITED", i):
            depth, j = 0, i
            while j < len(tree):
                if tree[j] == "(":
                    depth += 1
                elif tree[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            i = j + 1
        else:
            out.append(tree[i])
            i += 1
    return "".join(out)


def classify_tree(tree):
    """Return (sentence_type, n_words, has_repair, has_filled_pause)."""
    root = re.match(r"\(\s*(\S+)", tree)
    root = re.sub(r"[-=].*", "", root.group(1)) if root else "?"
    leaves = re.findall(r"\(([^\s()]+) ([^\s()]+)\)", tree)
    words = [w for pos, w in leaves if pos not in TREE_SKIP_POS]
    if not words:
        return None, 0, False, False
    edited = "(EDITED" in tree
    filled = bool(re.search(r"\(UH (uh|um)\)", tree, re.I))
    fragment_word = any(w.endswith("-") and len(w) > 1 for w in words)
    unfinished = "-UNF" in strip_edited(tree) or "N_S" in tree
    is_clause = root in ("S", "SQ", "SBARQ", "SINV")
    if is_clause and not unfinished:
        kind = "complete_disfluent" if (edited or filled or fragment_word) else "complete_fluent"
    elif is_clause:
        kind = "unfinished"
    elif root == "INTJ":
        kind = "response_token"
    else:
        kind = "fragment"
    return kind, len(words), edited, filled


# ----------------------------------------------------------------------------
# Reading the corpus
# ----------------------------------------------------------------------------
def open_corpus(path):
    """Yield (name, text-file-handle) for every CSV in a zip or folder."""
    if os.path.isdir(path):
        for folder, _, files in sorted(os.walk(path)):
            if "__MACOSX" in folder:
                continue
            for name in sorted(files):
                if name.endswith(".csv") and not name.startswith("._"):
                    full = os.path.join(folder, name)
                    with open(full, newline="", encoding="utf-8", errors="replace") as fh:
                        yield name, fh
    else:
        with zipfile.ZipFile(path) as zf:
            for name in sorted(zf.namelist()):
                base = os.path.basename(name)
                if "__MACOSX" in name or not base.endswith(".csv") or base.startswith("._"):
                    continue
                with zf.open(name) as raw:
                    yield base, io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")


def load(path):
    metadata, rows = {}, collections.defaultdict(list)
    for name, fh in open_corpus(path):
        reader = csv.DictReader(fh)
        if name == "swda-metadata.csv":
            for r in reader:
                metadata[int(r["conversation_no"])] = r
        elif name.endswith(".utt.csv"):
            for r in reader:
                rows[int(r["conversation_no"])].append(r)
    if not rows:
        sys.exit("No transcript files found in %s" % path)
    for conv in rows:
        rows[conv].sort(key=lambda r: int(r["transcript_index"]))
    return metadata, rows


# ----------------------------------------------------------------------------
# Per-conversation processing
# ----------------------------------------------------------------------------
def turn_counts(turn):
    """Counts for one turn, built so that turns sum to their conversation."""
    c = collections.Counter()
    for piece in turn["pieces"]:
        u = piece["utt"]
        classes = collections.Counter(cls for _, cls in piece["word_list"])
        n = len(piece["word_list"])
        c["words"] += n
        for cls in WORD_CLASSES:
            c["w_" + cls] += classes[cls]
        c["disfluent_words"] += sum(classes[k] for k in DISFLUENT)
        fps = [w.lower() for w, cls in piece["word_list"] if cls == "fp"]
        c["uh"] += sum(1 for w in fps if w.startswith("uh"))
        c["um"] += sum(1 for w in fps if w.startswith("um"))
        c["repairs"] += piece["repairs"]
        c["mtw_" + u["markup_type"]] += n
        if u["sentence_type"]:
            c["stw_" + u["sentence_type"]] += n
        if not piece["cont"]:                 # the utterance starts in this turn
            c["utterances"] += 1
            c["utt_with_disfluency"] += int(u["has_disfluency"])
            c["utt_with_filled_pause"] += int(u["w_fp"] > 0)
            c["utt_abandoned"] += int(u["abandoned"])
            c["utt_overlap"] += int(u["overlap"])
            c["utt_closing"] += int(u["damsl"] == "fc")
            c["mt_" + u["markup_type"]] += 1
            if u["sentence_type"]:
                c["st_" + u["sentence_type"]] += 1
    return c


def type_words(counts, prefix, types):
    """{type: words} for the types that occur, for compact JSON."""
    return {t: counts[prefix + t] for t in types if counts[prefix + t]}


def process_conversation(conv, rows):
    """Return (utterances, sentence_units, turns) for one conversation.

    turns is a list in spoken order. Each turn holds its pieces (one per SwDA
    row), its own has_disfluency / abandoned flags, and its counts."""
    stacks = {"A": [], "B": []}
    turns = {}
    last_unit = {}
    utterances = []
    tree_info = {}          # tree number -> dict
    for r in rows:
        caller = r["caller"].strip().lstrip("@")[:1] or "A"
        tag = r["act_tag"].strip()
        stack = stacks.setdefault(caller, [])
        is_continuation = tag.startswith("+")
        if not is_continuation:
            stack.clear()   # a repair left open by an annotation slip must not leak
        words, flags = parse_row(r["text"] or "", stack)
        row_disfluent = (any(cls in DISFLUENT for _, cls in words)
                         or flags["repairs"] > 0 or flags["ip"] > 0)
        turn_no = int(r["utterance_index"])
        turn = turns.get(turn_no)
        if turn is None:
            turn = turns[turn_no] = {
                "conversation_no": conv, "turn": turn_no, "order": len(turns),
                "speaker": caller, "transcript_index": int(r["transcript_index"]),
                "pieces": [], "has_disfluency": False, "abandoned": False}
        turn["has_disfluency"] = turn["has_disfluency"] or row_disfluent
        turn["abandoned"] = turn["abandoned"] or flags["abandon"] > 0 or tag.startswith("%")

        continues = is_continuation and caller in last_unit
        if continues:
            u = last_unit[caller]
            u["parts"] += 1
        else:
            u = {
                "conversation_no": conv, "order": len(utterances),
                "transcript_index": int(r["transcript_index"]),
                "turn": int(r["utterance_index"]), "speaker": caller,
                "act_tag": tag, "damsl": damsl_tag(tag), "parts": 1,
                "word_list": [], "text": [], "trees": [],
                "repairs": 0, "ips": 0, "abandon_marks": 0, "overlap_marks": 0,
            }
            utterances.append(u)
            last_unit[caller] = u
        u["word_list"].extend(words)
        u["text"].append((r["text"] or "").strip())
        u["repairs"] += flags["repairs"]
        u["ips"] += flags["ip"]
        u["abandon_marks"] += flags["abandon"]
        u["overlap_marks"] += flags["overlap"]
        turn["pieces"].append({"utt": u, "cont": continues, "word_list": words,
                               "repairs": flags["repairs"]})

        numbers = (r.get("ptb_treenumbers") or "").strip()
        trees = (r.get("trees") or "").strip()
        if numbers and trees:
            ns, ts = numbers.split("|||"), trees.split("|||")
            if len(ns) == len(ts):
                for n, t in zip(ns, ts):
                    if n not in tree_info:
                        kind, n_words, edited, filled = classify_tree(t)
                        if kind is None:
                            continue
                        tree_info[n] = {
                            "conversation_no": conv, "tree": n,
                            "transcript_index": int(r["transcript_index"]),
                            "turn": int(r["utterance_index"]), "speaker": caller,
                            "words": n_words, "sentence_type": kind,
                            "has_repair": int(edited), "has_filled_pause": int(filled),
                        }
                    if n not in u["trees"]:
                        u["trees"].append(n)

    for u in utterances:
        counts = collections.Counter(cls for _, cls in u["word_list"])
        for cls in WORD_CLASSES:
            u["w_" + cls] = counts[cls]
        u["words"] = len(u["word_list"])
        u["disfluent_words"] = sum(counts[c] for c in DISFLUENT)
        fps = [w.lower() for w, cls in u["word_list"] if cls == "fp"]
        u["uh"] = sum(1 for w in fps if w.startswith("uh"))
        u["um"] = sum(1 for w in fps if w.startswith("um"))
        u["has_disfluency"] = u["disfluent_words"] > 0 or u["repairs"] > 0 or u["ips"] > 0
        u["abandoned"] = u["abandon_marks"] > 0 or u["act_tag"].startswith("%")
        u["overlap"] = u["overlap_marks"] > 0
        if u["words"] == 0:
            u["markup_type"] = "nonverbal"
        elif u["abandoned"]:
            u["markup_type"] = "abandoned"
        elif u["has_disfluency"]:
            u["markup_type"] = "disfluent"
        elif u["damsl"] in BACKCHANNEL_TAGS:
            u["markup_type"] = "backchannel"
        else:
            u["markup_type"] = "fluent"
        # sentence type: take the largest parsed sentence attached to the utterance
        known = [tree_info[n] for n in u["trees"] if n in tree_info]
        u["sentence_type"] = max(known, key=lambda t: t["words"])["sentence_type"] if known else ""
        u["text"] = " ".join(u["text"])
    units = sorted(tree_info.values(), key=lambda t: (t["transcript_index"], int(t["tree"]) if t["tree"].isdigit() else 0))
    turn_list = list(turns.values())
    for turn in turn_list:
        turn["counts"] = turn_counts(turn)
    return utterances, units, turn_list


# ----------------------------------------------------------------------------
# Writers
# ----------------------------------------------------------------------------
COUNT_COLUMNS = (
    ["words", "utterances", "disfluent_words"]
    + ["w_" + c for c in WORD_CLASSES]
    + ["uh", "um", "repairs", "utt_with_disfluency", "utt_with_filled_pause",
       "utt_abandoned", "utt_overlap", "utt_closing"]
    + ["mt_" + t for t in MARKUP_TYPES] + ["mtw_" + t for t in MARKUP_TYPES]
    + ["st_" + t for t in SENTENCE_TYPES] + ["stw_" + t for t in SENTENCE_TYPES]
)


def rate(num, den, scale=100.0):
    return round(scale * num / den, 3) if den else ""


def speaker_meta(meta, caller, year):
    side = "from" if caller == "A" else "to"
    if not meta:
        return {"caller_id": "", "sex": "", "birth_year": "", "age": "",
                "dialect": "", "education_code": "", "education": ""}
    birth = meta.get(side + "_caller_birth_year", "")
    age = year - int(birth) if (birth.isdigit() and year) else ""
    edu = meta.get(side + "_caller_education", "")
    return {"caller_id": meta.get(side + "_caller", ""),
            "sex": meta.get(side + "_caller_sex", ""),
            "birth_year": birth, "age": age,
            "dialect": meta.get(side + "_caller_dialect_area", ""),
            "education_code": edu, "education": EDUCATION.get(edu, "")}


def write_schema(out):
    schema = {
        "word_classes": {
            "p": "plain", "cj": "utterance-linking conjunction {C}",
            "dm": "discourse marker {D}", "ij": "interjection such as oh/huh {F}",
            "as": "aside {A}", "fp": "filled pause (uh, um)",
            "et": "editing term {E}", "rp": "reparandum (replaced by a repair)",
            "fr": "word fragment outside a reparandum"},
        "disfluent_word_classes": list(DISFLUENT),
        "markup_type": "nonverbal > abandoned > disfluent > backchannel > fluent (first match wins)",
        "sentence_type": "Treebank-based, parsed conversations only: " + ", ".join(SENTENCE_TYPES),
        "count_columns": {
            "words": "all words", "utterances": "dialog-act units",
            "disfluent_words": "fp + et + rp + fr",
            "w_<class>": "words in that class", "uh / um": "filled pauses by form",
            "repairs": "number of [ ... + ... ] repairs opened",
            "utt_with_disfluency": "utterances with a disfluent word or any part of a repair",
            "utt_with_filled_pause": "utterances with at least one filled pause",
            "utt_abandoned": "abandoned (-/) or tagged %",
            "utt_overlap": "utterances containing an overlap mark (#)",
            "utt_closing": "utterances tagged conventional closing (fc)",
            "mt_<type> / mtw_<type>": "utterances / words by markup_type",
            "st_<type> / stw_<type>": "utterances / words by sentence_type (blank type excluded)"},
        "speakers": "A is the caller who placed the call (from_caller), B the one who answered",
        "levels": "words count in the turn where spoken; utterance counts in the turn "
                  "where the utterance starts; turns sum exactly to their conversation",
        "turns_csv": {
            "order": "position of the turn in the conversation (0-based)",
            "pieces": "utterance pieces in the turn",
            "continues_previous": "1 if the turn opens by continuing an earlier utterance",
            "has_disfluency / abandoned": "judged from this turn's own words and marks"},
        "conversation_json": {
            "counts": "conversation totals: words, utterances, turns, disfluent words, "
                      "mtw / stw = words by markup_type / sentence_type",
            "turns[]": {"t": "turn number", "i": "turn order", "s": "speaker",
                        "n": "words", "d": "disfluent words", "fp": "filled pauses",
                        "rep": "repairs", "dis": "1 if the turn has a disfluency",
                        "ab": "1 if the turn has an abandoned utterance",
                        "mtw": "words by markup_type", "stw": "words by sentence_type",
                        "u": "utterance pieces, in spoken order"},
            "turns[].u[]": {"id": "utterance id (= order in utterances.csv)",
                            "c": "1 if this piece continues an utterance from an earlier turn",
                            "tag": "collapsed dialog act", "n": "words in this piece",
                            "d": "disfluent words in this piece",
                            "mt": "markup_type of the whole utterance",
                            "st": "sentence_type of the whole utterance, or null",
                            "ov": "1 if the utterance has an overlap mark",
                            "w": "[token, class] pairs in spoken order"}},
    }
    with open(os.path.join(out, "schema.json"), "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--input", default="swda.zip", help="swda.zip or the unzipped swda folder")
    ap.add_argument("--out", default="swda_d3", help="output folder")
    ap.add_argument("--download", action="store_true", help="download swda.zip from GitHub if --input is missing")
    ap.add_argument("--no-json", action="store_true", help="skip the per-conversation JSON files")
    ap.add_argument("--no-text", action="store_true", help="leave the transcript text out of utterances.csv")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        if not args.download:
            sys.exit("Input %s not found. Download swda.zip from %s or pass --download." % (args.input, SWDA_URL))
        print("Downloading", SWDA_URL)
        urllib.request.urlretrieve(SWDA_URL, args.input)

    metadata, rows = load(args.input)
    os.makedirs(args.out, exist_ok=True)
    json_dir = os.path.join(args.out, "conversations")
    if not args.no_json:
        os.makedirs(json_dir, exist_ok=True)

    utt_cols = ["conversation_no", "order", "transcript_index", "turn", "speaker",
                "act_tag", "damsl", "parts", "words", "disfluent_words"] + \
               ["w_" + c for c in WORD_CLASSES] + \
               ["uh", "um", "repairs", "has_disfluency", "abandoned", "overlap",
                "markup_type", "sentence_type"] + ([] if args.no_text else ["text"])
    unit_cols = ["conversation_no", "tree", "transcript_index", "turn", "speaker",
                 "words", "sentence_type", "has_repair", "has_filled_pause"]
    turn_meta_cols = ["conversation_no", "turn", "order", "speaker", "transcript_index",
                      "pieces", "continues_previous", "has_disfluency", "abandoned"]
    turn_rate_cols = ["disfluent_per_100_words", "filled_pauses_per_100_words"]
    conv_meta_cols = ["conversation_no", "date", "year", "topic", "minutes", "has_parse", "turns"]
    conv_rate_cols = ["disfluent_per_100_words", "filled_pauses_per_100_words",
                      "repairs_per_100_words", "pct_utt_with_disfluency",
                      "pct_units_complete_fluent", "pct_words_complete_fluent"]
    spk_meta_cols = ["conversation_no", "speaker", "caller_id", "sex", "birth_year", "age",
                     "dialect", "education_code", "education", "topic", "partner_sex"]
    spk_rate_cols = ["disfluent_per_100_words", "filled_pauses_per_100_words",
                     "uh_per_100_words", "um_per_100_words", "repairs_per_100_words"]

    totals = collections.Counter()
    length_table = collections.defaultdict(collections.Counter)   # (unit, length) -> counts
    unit_totals = collections.Counter()
    unit_word_totals = collections.Counter()

    f_utt = open(os.path.join(args.out, "utterances.csv"), "w", newline="", encoding="utf-8")
    f_unit = open(os.path.join(args.out, "sentence_units.csv"), "w", newline="", encoding="utf-8")
    f_conv = open(os.path.join(args.out, "conversations.csv"), "w", newline="", encoding="utf-8")
    f_turn = open(os.path.join(args.out, "turns.csv"), "w", newline="", encoding="utf-8")
    f_spk = open(os.path.join(args.out, "speakers.csv"), "w", newline="", encoding="utf-8")
    w_utt = csv.DictWriter(f_utt, utt_cols, extrasaction="ignore")
    w_unit = csv.DictWriter(f_unit, unit_cols, extrasaction="ignore")
    w_conv = csv.DictWriter(f_conv, conv_meta_cols + COUNT_COLUMNS + conv_rate_cols, extrasaction="ignore")
    w_spk = csv.DictWriter(f_spk, spk_meta_cols + COUNT_COLUMNS + spk_rate_cols, extrasaction="ignore")
    w_turn = csv.DictWriter(f_turn, turn_meta_cols + COUNT_COLUMNS + turn_rate_cols, extrasaction="ignore")
    for w in (w_utt, w_unit, w_conv, w_turn, w_spk):
        w.writeheader()

    for conv in sorted(rows):
        utterances, units, turns = process_conversation(conv, rows[conv])
        meta = metadata.get(conv, {})
        day = (meta.get("talk_day") or "").zfill(6)
        year = 1900 + int(day[:2]) if day.strip("0") else 0
        date = "%d-%s-%s" % (year, day[2:4], day[4:6]) if year else ""
        topic = meta.get("topic_description", "")

        conv_counts = collections.Counter()
        spk_counts = {"A": collections.Counter(), "B": collections.Counter()}
        for turn in turns:
            c = turn["counts"]
            conv_counts.update(c)
            spk_counts.setdefault(turn["speaker"], collections.Counter()).update(c)
            totals.update(c)
            turn_row = {k: turn[k] for k in ("conversation_no", "turn", "order", "speaker", "transcript_index")}
            turn_row.update({
                "pieces": len(turn["pieces"]),
                "continues_previous": int(turn["pieces"][0]["cont"]),
                "has_disfluency": int(turn["has_disfluency"]),
                "abandoned": int(turn["abandoned"]),
                "disfluent_per_100_words": rate(c["disfluent_words"], c["words"]),
                "filled_pauses_per_100_words": rate(c["w_fp"], c["words"]),
            })
            turn_row.update({k: c[k] for k in COUNT_COLUMNS})
            w_turn.writerow(turn_row)
            # fluency curve: turns
            if c["words"] > 0:
                cell = length_table[("turn", c["words"])]
                cell["n"] += 1
                cell["with_disfluency"] += int(turn["has_disfluency"])
                cell["abandoned"] += int(turn["abandoned"])
                cell["clean"] += int(not turn["has_disfluency"] and not turn["abandoned"])
        for u in utterances:
            row = dict(u)
            for key in ("has_disfluency", "abandoned", "overlap"):
                row[key] = int(u[key])
            w_utt.writerow(row)
            # fluency curve: utterances
            if u["words"] > 0:
                for unit_name in ("utterance",) + (("utterance_substantive",) if u["damsl"] in SUBSTANTIVE_TAGS else ()):
                    cell = length_table[(unit_name, u["words"])]
                    cell["n"] += 1
                    cell["with_disfluency"] += int(u["has_disfluency"])
                    cell["abandoned"] += int(u["abandoned"])
                    cell["clean"] += int(not u["has_disfluency"] and not u["abandoned"])
        for s in units:
            w_unit.writerow(s)
            unit_totals[s["sentence_type"]] += 1
            unit_word_totals[s["sentence_type"]] += s["words"]

        st_units = sum(conv_counts["st_" + t] for t in SENTENCE_TYPES)
        st_words = sum(conv_counts["stw_" + t] for t in SENTENCE_TYPES)
        conv_row = {"conversation_no": conv, "date": date, "year": year or "", "topic": topic,
                    "minutes": meta.get("length", ""), "has_parse": int(bool(units)),
                    "turns": len(turns)}
        conv_row.update({c: conv_counts[c] for c in COUNT_COLUMNS})
        conv_row.update({
            "disfluent_per_100_words": rate(conv_counts["disfluent_words"], conv_counts["words"]),
            "filled_pauses_per_100_words": rate(conv_counts["w_fp"], conv_counts["words"]),
            "repairs_per_100_words": rate(conv_counts["repairs"], conv_counts["words"]),
            "pct_utt_with_disfluency": rate(conv_counts["utt_with_disfluency"], conv_counts["utterances"]),
            "pct_units_complete_fluent": rate(conv_counts["st_complete_fluent"], st_units),
            "pct_words_complete_fluent": rate(conv_counts["stw_complete_fluent"], st_words),
        })
        w_conv.writerow(conv_row)
        totals["conversations"] += 1
        totals["conversations_with_parse"] += int(bool(units))
        totals["turns"] += len(turns)

        speakers_json = {}
        for caller in ("A", "B"):
            sm = speaker_meta(meta, caller, year)
            other = speaker_meta(meta, "B" if caller == "A" else "A", year)
            c = spk_counts.get(caller, collections.Counter())
            spk_row = {"conversation_no": conv, "speaker": caller, "topic": topic,
                       "partner_sex": other["sex"]}
            spk_row.update(sm)
            spk_row.update({k: c[k] for k in COUNT_COLUMNS})
            spk_row.update({
                "disfluent_per_100_words": rate(c["disfluent_words"], c["words"]),
                "filled_pauses_per_100_words": rate(c["w_fp"], c["words"]),
                "uh_per_100_words": rate(c["uh"], c["words"]),
                "um_per_100_words": rate(c["um"], c["words"]),
                "repairs_per_100_words": rate(c["repairs"], c["words"]),
            })
            w_spk.writerow(spk_row)
            speakers_json[caller] = dict(sm, words=c["words"], utterances=c["utterances"])

        if not args.no_json:
            doc = {
                "conversation_no": conv, "date": date, "topic": topic,
                "has_parse": bool(units), "speakers": speakers_json,
                "counts": {
                    "words": conv_counts["words"], "utterances": conv_counts["utterances"],
                    "turns": len(turns), "disfluent_words": conv_counts["disfluent_words"],
                    "mtw": type_words(conv_counts, "mtw_", MARKUP_TYPES),
                    "stw": type_words(conv_counts, "stw_", SENTENCE_TYPES)},
                "turns": [{
                    "t": turn["turn"], "i": turn["order"], "s": turn["speaker"],
                    "n": turn["counts"]["words"], "d": turn["counts"]["disfluent_words"],
                    "fp": turn["counts"]["w_fp"], "rep": turn["counts"]["repairs"],
                    "dis": int(turn["has_disfluency"]), "ab": int(turn["abandoned"]),
                    "mtw": type_words(turn["counts"], "mtw_", MARKUP_TYPES),
                    "stw": type_words(turn["counts"], "stw_", SENTENCE_TYPES),
                    "u": [{
                        "id": piece["utt"]["order"], "c": int(piece["cont"]),
                        "tag": piece["utt"]["damsl"], "n": len(piece["word_list"]),
                        "d": sum(1 for _, cls in piece["word_list"] if cls in DISFLUENT),
                        "mt": piece["utt"]["markup_type"],
                        "st": piece["utt"]["sentence_type"] or None,
                        "ov": int(piece["utt"]["overlap"]),
                        "w": [[w, cls] for w, cls in piece["word_list"]],
                    } for piece in turn["pieces"]],
                } for turn in turns],
            }
            with open(os.path.join(json_dir, "%d.json" % conv), "w", encoding="utf-8") as fh:
                json.dump(doc, fh, separators=(",", ":"))

    for fh in (f_utt, f_unit, f_conv, f_turn, f_spk):
        fh.close()

    with open(os.path.join(args.out, "fluency_by_length.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["unit", "length_words", "n", "with_disfluency", "abandoned", "clean"])
        for (unit_name, length) in sorted(length_table):
            cell = length_table[(unit_name, length)]
            w.writerow([unit_name, length, cell["n"], cell["with_disfluency"], cell["abandoned"], cell["clean"]])

    n_units = sum(unit_totals.values())
    n_unit_words = sum(unit_word_totals.values())
    summary = {
        "conversations": totals["conversations"],
        "conversations_with_parse": totals["conversations_with_parse"],
        "turns": totals["turns"], "utterances": totals["utterances"], "words": totals["words"],
        "word_class_pct": {c: rate(totals["w_" + c], totals["words"]) for c in WORD_CLASSES},
        "disfluent_words_pct": rate(totals["disfluent_words"], totals["words"]),
        "filled_pauses": totals["w_fp"], "uh": totals["uh"], "um": totals["um"],
        "repairs": totals["repairs"],
        "utterances_with_disfluency_pct": rate(totals["utt_with_disfluency"], totals["utterances"]),
        "utterances_with_filled_pause_pct": rate(totals["utt_with_filled_pause"], totals["utterances"]),
        "utterances_abandoned_pct": rate(totals["utt_abandoned"], totals["utterances"]),
        "markup_type_pct_of_utterances": {t: rate(totals["mt_" + t], totals["utterances"]) for t in MARKUP_TYPES},
        "sentence_units": n_units,
        "sentence_type_pct_of_units": {t: rate(unit_totals[t], n_units) for t in SENTENCE_TYPES},
        "sentence_type_pct_of_words": {t: rate(unit_word_totals[t], n_unit_words) for t in SENTENCE_TYPES},
        "utterance_level_sentence_type_pct_of_utterances": {
            t: rate(totals["st_" + t], sum(totals["st_" + x] for x in SENTENCE_TYPES)) for t in SENTENCE_TYPES},
        "utterance_level_sentence_type_pct_of_words": {
            t: rate(totals["stw_" + t], sum(totals["stw_" + x] for x in SENTENCE_TYPES)) for t in SENTENCE_TYPES},
    }
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    write_schema(args.out)

    print("Wrote", args.out)
    print("  conversations: %d (%d with parses)" % (summary["conversations"], summary["conversations_with_parse"]))
    print("  turns: %d   utterances: %d   words: %d" % (summary["turns"], summary["utterances"], summary["words"]))
    print("  disfluent words: %s%%   filled pauses: %d   repairs: %d" % (
        summary["disfluent_words_pct"], summary["filled_pauses"], summary["repairs"]))
    print("  utterances with a disfluency: %s%%" % summary["utterances_with_disfluency_pct"])
    print("  sentence types, percent of parsed sentences:", summary["sentence_type_pct_of_units"])


if __name__ == "__main__":
    main()
