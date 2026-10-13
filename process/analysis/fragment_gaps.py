"""What follows a broken-off word in the MS98 word alignments: straight on, a silence, or a filler, and for how long."""
import os, glob, csv, collections, statistics
root = "ms98/swb_ms98_transcriptions"
conv = {r["conversation_no"] for r in csv.DictReader(open("out/swda_d3/conversations.csv")) if sum(float(r[c]) for c in r if c.startswith("stw_")) > 0}
FILL = {"uh", "um", "uh-huh", "um-hum"}
cases = []; missing = 0
for c in sorted(conv):
    files = glob.glob(f"{root}/*/{c}/sw{c}[AB]-ms98-a-word.text")
    if len(files) != 2: missing += 1; continue
    for f in files:
        toks = []
        for line in open(f, encoding="latin-1"):
            p = line.split()
            if len(p) >= 4: toks.append((p[0], float(p[1]), float(p[2]), " ".join(p[3:]).lower()))
        for i, (seg, s, e, w) in enumerate(toks):
            if not (w.endswith("-") and len(w) > 1 and not w.startswith("[")): continue
            j = i + 1; sil = 0.0; fill = []; other = False
            while j < len(toks) and toks[j][0] == seg:
                w2 = toks[j][3]
                if w2 == "[silence]": sil += toks[j][2] - toks[j][1]
                elif w2 in ("uh", "um"): fill.append(w2)
                elif w2.startswith("[") or w2.startswith("<"): other = True
                else: break
                j += 1
            if j >= len(toks) or toks[j][0] != seg:
                kind = "segment ends (no continuation)"; gap = None
            else:
                gap = toks[j][1] - e
                kind = ("filler" if fill else "silence" if sil > 0 else "noise/laughter" if other else "straight on")
            cases.append({"call": c, "kind": kind, "gap": gap, "sil": sil, "fill": "+".join(fill)})
print("calls with both channels:", len(conv) - missing, "missing:", missing)
n = len(cases); k = collections.Counter(x["kind"] for x in cases)
print("broken-off words:", n)
for kind, v in k.most_common(): print(f"  {kind:32s} {v:6d}  {100*v/n:5.1f}%")
cont = [x for x in cases if x["gap"] is not None]
print("\ncontinued within the same stretch of speech:", len(cont))
for kind in ("straight on", "silence", "filler", "noise/laughter"):
    g = [x["gap"] for x in cont if x["kind"] == kind]
    if g: print(f"  {kind:15s} n={len(g):5d} ({100*len(g)/len(cont):4.1f}%)  gap median {1000*statistics.median(g):5.0f} ms, IQR {1000*statistics.quantiles(g,n=4)[0]:4.0f}-{1000*statistics.quantiles(g,n=4)[2]:4.0f} ms")
fl = collections.Counter(x["fill"] for x in cont if x["kind"] == "filler"); print("  fillers used:", fl.most_common(5))
sil = [x["sil"] for x in cont if x["kind"] == "silence"]
print("  silence-only gaps: share under 200 ms", round(sum(s < .2 for s in sil) / len(sil), 2), "| over 500 ms", round(sum(s > .5 for s in sil) / len(sil), 2))
