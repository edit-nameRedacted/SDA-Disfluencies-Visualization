"""How many parsed sentences of each type contain a verb. Usage: python verb_check2.py ../../pipeline/corpus/swda.zip"""
import sys, os, re, collections, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline"))
import extract_swda as X
meta, rows = X.load(sys.argv[1])
VERB = re.compile(r"\((VB[DGNPZ]?|MD|BES|HVS) [^\s()]+\)")
c = collections.Counter(); roots = collections.Counter(); ex = collections.defaultdict(list); noverb = []
for conv, rs in rows.items():
    for r in rs:
        ts = (r.get("trees") or "").strip()
        if not ts: continue
        for t in ts.split("|||"):
            kind, n, *_ = X.classify_tree(t)
            if not kind: continue
            body = X.strip_edited(t)
            verb = bool(VERB.search(body))
            c[(kind, verb)] += 1
            m = re.match(r"\(\s*(\S+)", t); root = re.sub(r"[-=].*", "", m.group(1)) if m else "?"
            words = " ".join(w for p, w in re.findall(r"\(([^\s()]+) ([^\s()]+)\)", body) if p not in X.TREE_SKIP_POS)
            if kind == "fragment" and verb:
                roots[root] += 1; ex[root].append(words)
            if kind.startswith("complete") and not verb:
                noverb.append(words)
for k in ("complete_fluent","complete_disfluent","unfinished","fragment"):
    a, b = c[(k, True)], c[(k, False)]
    print(f"{k:20s} trees {a+b:6d}  with a verb {100*a/max(1,a+b):5.1f}%")
rng = random.Random(1)
print(roots.most_common(8))
for root, _ in roots.most_common(5):
    print(root, "|", " || ".join(rng.sample(ex[root], 6)))
print("complete, no verb:", " || ".join(rng.sample(noverb, 12)))
