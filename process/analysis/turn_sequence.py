import pandas as pd, numpy as np, json, os, warnings
import statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
sp = pd.read_csv("analysis_speaker_slots.csv")
calls = sorted(set(sp.conversation_no))
meta = {(r.conversation_no, r.speaker): r for r in sp.itertuples()}
DISF = {"rp", "fr", "et"}        # non-filler disfluencies
rows = []
for c in calls:
    conv = json.load(open(f"out/swda_d3/conversations/{c}.json"))
    turns = []
    for t in conv["turns"]:
        words = [(w, k) for u in t["u"] for w, k in u["w"]]
        if words: turns.append((t["s"], words))
    for (s0, w0), (s1, w1) in zip(turns, turns[1:]):
        if s0 == s1 or len(w1) < 4: continue          # next turn by the other speaker, at least 4 words
        um0 = any(k == "fp" and w.lower().startswith("um") for w, k in w0)
        uh0 = any(k == "fp" and w.lower().startswith("uh") for w, k in w0)
        prev = "both" if um0 and uh0 else "um" if um0 else "uh" if uh0 else "none"
        m = meta.get((c, s1)); pm = meta.get((c, s0))
        if m is None or pm is None: continue
        n = len(w1)
        rows.append({"conv": c, "spk": m.caller_id, "sex": m.sex, "partner_sex": pm.sex, "prev": prev,
                     "prev_len": np.log(len(w0)), "next_len": np.log(n),
                     "other_disf": 100 * sum(k in DISF for _, k in w1) / n,
                     "fill": 100 * sum(k == "fp" for _, k in w1) / n,
                     "any_other": int(any(k in DISF for _, k in w1))})
d = pd.DataFrame(rows)
print("turn pairs", len(d)); print(d.prev.value_counts())
print("\nNext turn by the other speaker, by what the previous turn held (raw means):")
print(d.groupby(["prev"])[["other_disf", "fill", "any_other"]].mean().round(3))
print("\nSplit by sex of the um/uh user (previous speaker):")
print(d[d.prev.isin(["um", "uh", "none"])].groupby(["partner_sex", "prev"])[["other_disf", "fill"]].mean().round(2).unstack())
for y in ["other_disf", "fill"]:
    m = smf.mixedlm(f"{y} ~ C(prev, Treatment('none')) + prev_len + next_len + C(sex) + C(partner_sex)", d, groups=d.spk).fit()
    ks = [k for k in m.params.index if "prev," in k]
    print(y, "|", ", ".join(f"{k.split('T.')[1][:-1]} {m.params[k]:+.2f} (p={m.pvalues[k]:.3f})" for k in ks))
    m2 = smf.mixedlm(f"{y} ~ C(prev, Treatment('none')) * C(partner_sex) + prev_len + next_len + C(sex)", d[d.prev.isin(['um','uh','none'])], groups=d[d.prev.isin(['um','uh','none'])].spk).fit()
    ks = [k for k in m2.params.index if ":" in k]
    print("   interaction with previous speaker's sex:", ", ".join(f"{k} {m2.params[k]:+.2f} (p={m2.pvalues[k]:.3f})" for k in ks))
