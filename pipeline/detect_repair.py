#!/usr/bin/env python3
"""Find other-initiated repair in the Switchboard dialog-act corpus, by fixed rules.

An other-initiated repair has three parts (Schegloff, Jefferson & Sacks 1977):
  trouble source   something speaker Y said
  initiation       speaker X signals trouble with it ("huh?", "Southwest where?")
  repair           Y's next utterance, which says it again or differently

This script looks at every utterance U that starts X's response to Y (the first
utterance by X after an utterance by Y) and flags U as a repair initiation when one
of these rules fires. Rules are checked in order; the first that fires is recorded.

  R1 tag      the corpus tags U as signal-non-understanding (act tag br...).
  R2 open     U is nothing but an open-class initiator, once fillers and "oh",
              "well", "I'm sorry" style openers are set aside: what, huh, pardon,
              excuse me, sorry, say again, come again, what was that, what did you
              say, I didn't hear / catch that. These do not say what the trouble is.
              U must be marked as a question ("?"): a "Huh." or "I'm sorry." with a
              full stop is a reaction or an apology, not a request to repeat.
  R3 repeat   U is short (1 to 5 words, fillers aside), is marked as a question
              ("?" in the transcript), and is made only of words from the last 12
              words of Y's turn, plus at most one question word and "a", "the", "oh"
              ("Amarillo?", "Southwest where?", "a hundred?"). It must repeat at least
              one content word. News receipts that only repeat a short frame
              ("you did?", "is it?") are left out.
  R4 check    U opens with "you mean", "do you mean", "you're saying" or
              "you said" and is marked as a question.

Then one check on the reply, for open requests only (U is nothing but "what?", "huh?",
"pardon?" and the like, whether it fired R1 or R2): it counts only if Y's next
utterance answers it, by repeating at least one content word of the trouble source
(saying it again), by opening with "I said", "I mean", "it's" or "that's" (explaining),
or by being a short reply of 1 to 6 words that is not just "yeah", "uh-huh", "right"
(saying what was meant: "Dead Zone"). A "huh" followed by Y simply
carrying on with something new is a reaction ("huh!"), not a request. This check was
added after a first round of hand coding.

R1 and R2 are "strong"; R3, R4 and R2's "what's that?" are "candidate" (they
also catch checks of understanding and requests for more that are not trouble). Nothing here is labelled by a person or a
model: each flag can be traced to the rule and the words that fired it.

For each flag the script records the trouble source (Y's utterance just before U),
the repair (Y's next utterance after U) and how many of the repair's content words
repeat the trouble source.

Usage:  python detect_repair.py --data output --out output/repair_initiations.csv
Reads conversations/<id>.json and utterances.csv written by extract_swda.py.
Standard library only.
"""
import argparse
import collections
import csv
import json
import os
import re

FILLERS = {"uh", "um", "oh", "well", "i'm", "sorry", "i", "beg", "your", "excuse", "me"}
OPEN_INITIATORS = {
    ("what",), ("huh",), ("pardon",), ("pardon", "me"), ("excuse", "me"), ("sorry",),
    ("i'm", "sorry"), ("say", "again"), ("say", "that", "again"), ("come", "again"),
    ("what", "was", "that"), ("what's", "that"), ("what", "did", "you", "say"),
    ("i", "beg", "your", "pardon"), ("beg", "your", "pardon"), ("say", "what"),
    ("i", "didn't", "hear", "you"), ("i", "didn't", "catch", "that"), ("i", "didn't", "hear", "that"),
    ("what", "huh"), ("huh", "what"), ("i'm", "sorry", "what"), ("sorry", "what"),
}
QUESTION_WORDS = {"what", "where", "who", "when", "which", "how", "why", "whose"}
# Words that never count as "content" when checking for a repeat.
FUNCTION_WORDS = set("""a an the and but so or of to in on at for with from by about as is are was were be been
being am do does did have has had i you he she it we they me him her us them my your his its our their this
that these those there here not no yes yeah oh uh um well just like really very then too also it's that's
i'm you're he's she's we're they're don't didn't can't won't isn't wasn't aren't weren't do did know mean
okay right huh what where who when which how why""".split())
NEWS_RECEIPT_FRAMES = re.compile(r"^(oh )?(really|you did|you do|you are|you were|is it|is that right|"
                                 r"is that so|did you|do you|are you|was it|it is|it was|they did|they do|"
                                 r"he did|she did|oh yeah|yeah)$")
CHECK_OPENERS = re.compile(r"^(oh |well |so |uh |um )*(you mean|do you mean|you're saying|are you saying|you said)\b")


def words_of(piece_words):
    return [w.lower().strip(".,?!") for w, _ in piece_words if w.strip(".,?!")]


def load_utterances(data, call, text_by_id):
    """All utterances of a call in spoken order: id, speaker, act tag, words, transcript text."""
    with open(os.path.join(data, "conversations", "%s.json" % call), encoding="utf8") as f:
        conv = json.load(f)
    joined = collections.OrderedDict()
    for turn in conv["turns"]:
        for piece in turn["u"]:
            entry = joined.setdefault(piece["id"], {"id": piece["id"], "speaker": turn["s"], "tag": piece["tag"], "words": []})
            entry["words"].extend(words_of(piece["w"]))
    out = []
    for u in joined.values():
        u["text"] = text_by_id.get(u["id"], "")
        out.append(u)
    return out


def core(words):
    """The words with fillers and polite openers set aside."""
    return tuple(w for w in words if w not in FILLERS or w in ("what", "huh"))


def content(words):
    return {w for w in words if w not in FUNCTION_WORDS and not w.endswith("-") and len(w) > 1}


def classify(u, trouble):
    words = u["words"]
    if not words:
        return None, ""
    if u["tag"].startswith("br"):
        return "R1 tag", u["tag"]
    c = core(words)
    if " ".join(words) in ("uh huh", "um hum", "uh hum"):
        return None, ""                                    # a backchannel written as two words
    stripped = tuple(w for w in words if w not in ("uh", "um", "oh", "well"))
    is_question = "?" in u["text"]
    if is_question and (c in OPEN_INITIATORS or stripped in OPEN_INITIATORS):
        return "R2 open", " ".join(stripped)
    plain = " ".join(stripped)
    if is_question and CHECK_OPENERS.match(" ".join(words)):
        return "R4 check", plain
    if is_question and 1 <= len(stripped) <= 5 and not NEWS_RECEIPT_FRAMES.match(plain):
        tail = trouble["words"][-12:]
        shared = content(stripped) & content(tail)
        extra = [w for w in stripped if w not in tail and w not in ("a", "an", "the", "oh")]
        if shared and len(extra) <= 1 and all(w in QUESTION_WORDS for w in extra):
            return "R3 repeat", " ".join(sorted(shared))
    return None, ""


RESPONSE_ONLY = {"yeah", "yes", "uh-huh", "huh-uh", "right", "okay", "no", "sure", "um-hum", "yep", "oh", "uh", "um", "well", "mm"}


def is_open(u):
    """U is nothing but an open-class initiator, fillers aside."""
    words = u["words"]
    stripped = tuple(w for w in words if w not in ("uh", "um", "oh", "well"))
    return core(words) in OPEN_INITIATORS or stripped in OPEN_INITIATORS


def reply_answers(trouble, reply):
    """The reply says the trouble source again (a shared content word) or is a short answer."""
    if reply is None:
        return False
    if content(reply["words"]) & content(trouble["words"]):
        return True
    words = [w for w in reply["words"] if w not in ("uh", "um", "oh", "well")]
    if " ".join(words[:2]) in ("i said", "i mean", "it's", "it is", "that's", "that is") or words[:1] in (["it's"], ["that's"]):
        return True                                        # an explanation: "it's an Italian needlework"
    return 1 <= len(words) <= 6 and not all(w in RESPONSE_ONLY for w in words)


def strength(rule, fired_on):
    """R1 and R2 are strong, except "what's that" / "what was that", which also ask for
    more information about something new ("I've got a good recipe." "Oh what's that?")."""
    if not rule:
        return ""
    if rule == "R1 tag" or (rule == "R2 open" and fired_on not in ("what's that", "what was that")):
        return "strong"
    return "candidate"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="output")
    ap.add_argument("--out", default=os.path.join("output", "repair_initiations.csv"))
    ap.add_argument("--responses", default=None, help="optional: also write every response-opening utterance (for sampling)")
    args = ap.parse_args()

    texts = collections.defaultdict(dict)
    typed_calls = set()
    with open(os.path.join(args.data, "utterances.csv"), newline="", encoding="utf8") as f:
        for r in csv.DictReader(f):
            texts[r["conversation_no"]][int(r["order"])] = r["text"]
            if r["sentence_type"]:
                typed_calls.add(r["conversation_no"])

    flags, responses = [], []
    for call in sorted(typed_calls, key=int):
        us = load_utterances(args.data, call, texts[call])
        for i in range(1, len(us)):
            u, prev = us[i], us[i - 1]
            if u["speaker"] == prev["speaker"] or not u["words"]:
                continue                                   # only the first utterance of a response
            trouble = next((us[k] for k in range(i - 1, -1, -1) if us[k]["speaker"] != u["speaker"] and us[k]["words"]), None)
            if trouble is None:
                continue
            rule, fired_on = classify(u, trouble)
            repair = next((us[k] for k in range(i + 1, len(us)) if us[k]["speaker"] == trouble["speaker"] and us[k]["words"]), None)
            if rule and is_open(u) and not reply_answers(trouble, repair):
                rule, fired_on = None, ""                          # an open "huh" the other just talked past
            row = {"conversation_no": call, "utterance": u["id"], "speaker": u["speaker"], "act_tag": u["tag"],
                   "rule": rule or "", "strength": strength(rule, fired_on),
                   "fired_on": fired_on, "trouble_utterance": trouble["id"], "trouble": " ".join(trouble["words"]),
                   "initiation": " ".join(u["words"]),
                   "repair_utterance": repair["id"] if repair else "", "repair": " ".join(repair["words"]) if repair else ""}
            if repair and rule:
                rc = content(repair["words"])
                row["repair_repeats_share"] = round(len(rc & content(trouble["words"])) / len(rc), 3) if rc else ""
            else:
                row["repair_repeats_share"] = ""
            responses.append(row)
            if rule:
                flags.append(row)

    fields = list(flags[0])
    with open(args.out, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(flags)
    if args.responses:
        with open(args.responses, "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(responses)
    print("response-opening utterances:", len(responses))
    print("flagged:", len(flags), dict(collections.Counter(r["rule"] for r in flags)))


if __name__ == "__main__":
    main()
