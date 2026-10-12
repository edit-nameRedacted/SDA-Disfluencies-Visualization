# Build a lookup of every utterance's plain words -> (call, order, speaker, type) from the new data.
import json, os, csv, collections, pickle, sys
data = sys.argv[1]
types = {}
with open(os.path.join(data, "utterances.csv"), newline="", encoding="utf8") as f:
    for r in csv.DictReader(f):
        types[(int(r["conversation_no"]), int(r["order"]))] = r["sentence_type"]
index = collections.defaultdict(list)
for name in os.listdir(os.path.join(data, "conversations")):
    call = int(name[:-5])
    conv = json.load(open(os.path.join(data, "conversations", name), encoding="utf8"))
    joined = collections.OrderedDict()
    for turn in conv["turns"]:
        for piece in turn["u"]:
            if piece["w"]:
                e = joined.setdefault(piece["id"], [turn["s"], []]); e[1].extend(w for w, _ in piece["w"])
    for uid, (s, ws) in joined.items():
        index[" ".join(ws).lower()].append((call, uid, s, types.get((call, uid), "")))
pickle.dump(dict(index), open("plain_index.pkl", "wb"))
print(len(index))
