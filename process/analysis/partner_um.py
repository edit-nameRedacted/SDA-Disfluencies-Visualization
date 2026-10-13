import pandas as pd, numpy as np, json, warnings, collections
import statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
sp = pd.read_csv("analysis_speaker_slots.csv")
full = pd.read_csv("out/swda_d3/speakers.csv")
p = full[["conversation_no", "speaker", "words", "uh", "um", "w_rp", "w_fr", "w_et", "w_yk"]].copy()
p["speaker"] = p.speaker.map({"A": "B", "B": "A"})   # partner's row, keyed to the speaker it talks to
p = p.rename(columns={c: "p_" + c for c in ["words", "uh", "um", "w_rp", "w_fr", "w_et", "w_yk"]})
d = sp.merge(p, on=["conversation_no", "speaker"])
d["p_um100"] = 100 * d.p_um / d.p_words; d["p_uh100"] = 100 * d.p_uh / d.p_words
d["p_other100"] = 100 * (d.p_w_rp + d.p_w_fr + d.p_w_et) / d.p_words
d["own_nofill"] = 100 * (d.w_rp + d.w_fr + d.w_et) / d.words     # speaker's disfluency without fillers
print("slots", len(d))
print(d[["p_um100", "p_uh100", "p_other100", "total", "own_nofill"]].corr().round(2).loc[["p_um100", "p_uh100", "p_other100"], ["total", "own_nofill"]])
for y in ["total", "own_nofill", "fillers", "repeats"]:
    for f in [f"{y} ~ C(partner_sex) + C(sex) + age10",
              f"{y} ~ C(partner_sex) + C(sex) + age10 + p_um100 + p_uh100 + p_other100"]:
        m = smf.mixedlm(f, d, groups=d.caller_id).fit()
        keys = [k for k in m.params.index if k.startswith(("C(partner", "p_"))]
        print(y, "|", ", ".join(f"{k.replace('C(partner_sex)[T.MALE]','partner male')} {m.params[k]:+.2f} (p={m.pvalues[k]:.3f})" for k in keys))
    print()
