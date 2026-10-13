import pandas as pd, numpy as np, warnings, glob
import statsmodels.formula.api as smf
from scipy.stats import chi2
warnings.filterwarnings("ignore")
t = pd.read_csv("repair/utterance_timing.csv")
rep = pd.read_csv("repair/repair_initiations.csv")
resp = pd.read_csv("repair/responses.csv", usecols=["conversation_no", "utterance", "speaker"])
sp = pd.read_csv("analysis_speaker_slots.csv")
# mid-word breaks per speaker, from MS98 (fragments marked x[yz]-), using the channel pairing chosen
match = pd.read_csv("repair/call_timing_match.csv").set_index("conversation_no")
frag = {}
for c in sp.conversation_no.unique():
    sw = match.loc[c, "channels_swapped"]
    for side in "AB":
        ch = {"A": "B", "B": "A"}[side] if sw else side
        f = glob.glob(f"ms98/swb_ms98_transcriptions/*/{c}/sw{c}{ch}-ms98-a-word.text")[0]
        toks = [l.split()[3] for l in open(f, encoding="latin-1") if len(l.split()) >= 4]
        words = [w for w in toks if not w.startswith("[") or w.startswith("[laughter-")]
        frag[(c, side)] = (sum(1 for w in words if w.endswith("-") and len(w) > 1), len(words))
g = t.dropna(subset=["gap_before"])
per = g.groupby(["conversation_no", "speaker"]).agg(transitions=("gap_before", "size"),
        long_gap=("gap_before", lambda x: (x > 1).mean()), median_gap=("gap_before", "median"))
ins = t.dropna(subset=["start"]).groupby(["conversation_no", "speaker"]).agg(pauses=("long_pauses_inside", "sum"), tw=("matched", "sum"))
oir = rep.groupby(["conversation_no", "speaker"]).size().rename("oir")
nresp = resp.groupby(["conversation_no", "speaker"]).size().rename("responses")
d = sp.set_index(["conversation_no", "speaker"]).join([per, ins, oir, nresp]).reset_index()
d["oir"] = d.oir.fillna(0)
d["oir_per100"] = 100 * d.oir / d.responses
d["long_gap_pct"] = 100 * d.long_gap
d["pauses_per100w"] = 100 * d.pauses / d.tw
d["midword_per100w"] = [100 * frag[(c, s)][0] / max(1, frag[(c, s)][1]) for c, s in zip(d.conversation_no, d.speaker)]
d.to_csv("repair/speaker_difficulty.csv", index=False)
sig = ["long_gap_pct", "pauses_per100w", "midword_per100w", "oir_per100", "restarts", "fillers", "repeats"]
print(d[sig].describe().loc[["mean", "50%"]].round(2))
print("\nCorrelation between signals across speakers-in-calls (Spearman):")
print(d[sig].corr(method="spearman").round(2))
print("\nTopic effect (likelihood ratio, speaker random intercept; controls age, sex, partner sex):")
for y in sig:
    dd = d.dropna(subset=[y])
    base = smf.mixedlm(f"{y} ~ age10 + C(sex) + C(partner_sex)", dd, groups=dd.caller_id).fit(reml=False)
    full = smf.mixedlm(f"{y} ~ age10 + C(sex) + C(partner_sex) + C(topic)", dd, groups=dd.caller_id).fit(reml=False)
    lr = 2 * (full.llf - base.llf); df = dd.topic.nunique() - 1
    tm = dd.groupby("topic")[y].agg(["mean", "size"]); tm = tm[tm["size"] >= 20].sort_values("mean")
    print(f"  {y:16s} chi2={lr:6.1f} df={df} p={chi2.sf(lr, df):.4f} | low: {tm.index[0].title()} {tm['mean'].iloc[0]:.2f}, {tm.index[1].title()} {tm['mean'].iloc[1]:.2f} | high: {tm.index[-1].title()} {tm['mean'].iloc[-1]:.2f}, {tm.index[-2].title()} {tm['mean'].iloc[-2]:.2f}")
