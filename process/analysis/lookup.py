import pickle, sys
idx = pickle.load(open("plain_index.pkl", "rb"))
for q in sys.argv[1:]:
    hits = idx.get(q.lower(), [])
    print(f"{q!r:55s} {len(hits)}  " + ", ".join(sorted({h[3] for h in hits})))
