import pandas as pd, numpy as np, warnings
import statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
conv = pd.read_csv("out/swda_d3/conversations.csv")
stw = [c for c in conv if c.startswith("stw_")]
parsed = set(conv.loc[conv[stw].sum(axis=1) > 0, "conversation_no"])
sp = pd.read_csv("out/swda_d3/speakers.csv")
sp = sp[sp.conversation_no.isin(parsed) & (sp.words >= 100)].copy()
per = lambda col: 100 * col / sp.words
sp["fillers"] = per(sp.uh + sp.um)
sp["uh100"] = per(sp.uh); sp["um100"] = per(sp.um)
sp["repeats"] = per(sp.w_rp)          # repeated or reworded words (reparandum)
sp["cutoffs"] = per(sp.w_fr)
sp["restarts"] = per(sp.utt_abandoned)  # abandoned utterances per 100 words
sp["youknow"] = per(sp.w_yk)
sp["editing"] = per(sp.w_et)
sp["total"] = per(sp.w_fp + sp.w_rp + sp.w_fr + sp.w_et)   # excludes "you know", closer to Bortfeld's categories
sp["age10"] = (sp.age - 40) / 10
sp["role"] = np.where(sp.speaker == "A", "caller", "answerer")
sp["band"] = pd.cut(sp.age, [0, 29, 39, 49, 59, 99], labels=["20s", "30s", "40s", "50s", "60+"])
print("speaker slots", len(sp), "people", sp.caller_id.nunique())
print("\nRaw means per 100 words, by age band (slot-level):")
print(sp.groupby("band", observed=True)[["total", "fillers", "uh100", "um100", "repeats", "restarts", "cutoffs", "youknow"]].mean().round(2).assign(n=sp.groupby("band", observed=True).size()))
print("\nBy sex:"); print(sp.groupby("sex")[["total", "fillers", "uh100", "um100", "repeats", "restarts", "youknow"]].mean().round(2))
print("\nBy role:"); print(sp.groupby("role")[["total", "fillers", "repeats", "restarts", "youknow"]].mean().round(2))
rows = []
for y in ["total", "fillers", "uh100", "um100", "repeats", "restarts", "cutoffs", "youknow"]:
    m = smf.mixedlm(f"{y} ~ age10 + C(sex) + C(role, Treatment('answerer')) + C(partner_sex)", sp, groups=sp.caller_id).fit(reml=True)
    p = m.params; pv = m.pvalues
    rows.append({"outcome": y, "mean": sp[y].mean().round(2),
                 "age_per_decade": f"{p['age10']:+.2f} (p={pv['age10']:.3f})",
                 "male_vs_female": f"{p['C(sex)[T.MALE]']:+.2f} (p={pv['C(sex)[T.MALE]']:.3f})",
                 "caller_vs_answerer": f"{p[[k for k in p.index if 'role' in k][0]]:+.2f} (p={pv[[k for k in p.index if 'role' in k][0]]:.3f})",
                 "partner_male": f"{p['C(partner_sex)[T.MALE]']:+.2f} (p={pv['C(partner_sex)[T.MALE]']:.3f})",
                 "speaker_sd": round(float(np.sqrt(m.cov_re.iloc[0, 0])), 2), "resid_sd": round(float(np.sqrt(m.scale)), 2)})
pd.set_option("display.width", 220)
print("\nMixed models, random intercept per speaker:"); print(pd.DataFrame(rows).to_string(index=False))
# um share
sp2 = sp[(sp.uh + sp.um) > 0].copy(); sp2["um_share"] = sp2.um / (sp2.uh + sp2.um)
m = smf.mixedlm("um_share ~ age10 + C(sex) + C(role, Treatment('answerer'))", sp2, groups=sp2.caller_id).fit()
print("\num share of fillers:", sp2.groupby("sex").um_share.mean().round(3).to_dict(), "| age per decade", round(m.params["age10"], 3), "p", round(m.pvalues["age10"], 4), "| male", round(m.params["C(sex)[T.MALE]"], 3), "p", round(m.pvalues["C(sex)[T.MALE]"], 4))
# correlation across speakers: fillers vs repeats (person means)
pm = sp.groupby("caller_id")[["fillers", "repeats", "restarts", "youknow"]].mean()
print("\nCorrelation of person means (Spearman):"); print(pm.corr(method="spearman").round(2))
sp.to_csv("analysis_speaker_slots.csv", index=False)
