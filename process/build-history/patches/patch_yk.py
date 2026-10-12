import sys, re
path = sys.argv[1]
s = open(path, encoding="utf-8").read()

def swap(old, new, count=1):
    global s
    found = s.count(old)
    assert found == count, (found, count, old[:70])
    s = s.replace(old, new)

# ---- colours -------------------------------------------------------------------------------
swap("    --cutoff: #eda100;\n    --uh: #6250d6;", "    --cutoff: #eda100;\n    --youknow: #0e9aa7;\n    --uh: #6250d6;")
swap("--replaced: #e0558a; --editing: #f3a3c0; --uh: #9085e9; --um: #c2bbf5;",
     "--replaced: #e0558a; --editing: #f3a3c0; --youknow: #3cc6c9; --uh: #9085e9; --um: #c2bbf5;", 3)
swap("  .kind.k3 { fill: var(--uh); }\n  .kind.k4 { fill: var(--um); }",
     "  .kind.k3 { fill: var(--youknow); }\n  .kind.k4 { fill: var(--uh); }\n  .kind.k5 { fill: var(--um); }")
swap("  .w-fr { color: var(--cutoff); }\n", "  .w-fr { color: var(--cutoff); }\n  .w-yk { color: var(--youknow); }\n")

# ---- the key under the legend ---------------------------------------------------------------
swap('<span class="w-fr">cut-off</span> · <span class="w-uh">uh</span>',
     '<span class="w-fr">cut-off</span> · <span class="w-yk">you know</span> · <span class="w-uh">uh</span>')

# ---- settings -------------------------------------------------------------------------------
swap("""// The order is the stacking order, bottom to top: three kinds that come from repairs,
// then the two filled pauses.""",
"""// The order is the stacking order, bottom to top: three kinds that come from repairs,
// then "you know", then the two filled pauses.""")
swap("""  { label: "“Uh”",                       short: "“Uh”",           count: call => call.uh },""",
"""  { label: "“You know”",                 short: "“You know”",     count: call => call.w_yk },
  { label: "“Uh”",                       short: "“Uh”",           count: call => call.uh },""")

# ---- the strip's labels: any number of kinds, evenly spaced around the middle ---------------
swap("""    const at = -centre + (2 - i) * px(17);                           // five labels, evenly spaced around the same middle""",
     """    const at = -centre + (halfSpan - i) * px(17);                    // the labels, evenly spaced around the same middle""")
swap("""  let foot = centre - barHeight * d.disfluent / 200;                 // so the block starts half its own height below that""",
     """  let foot = centre - barHeight * d.disfluent / 200;                 // so the block starts half its own height below that
  const halfSpan = (kinds.length - 1) / 2;                           // with six kinds: 2.5 label steps above and below the middle""")
swap("  const labelsTop = -centre - 2 * px(17);", "  const labelsTop = -centre - halfSpan * px(17);")

# ---- words in a line of talk ----------------------------------------------------------------
swap("""{ rp: "w-rp", et: "w-et", fr: "w-fr" }[kind]""", """{ rp: "w-rp", et: "w-et", fr: "w-fr", yk: "w-yk" }[kind]""")

# ---- info panel: sentence types -------------------------------------------------------------
a = s.index("    <p>The corpus has no such category. A script reads the parse of each sentence and gives it one type:</p>")
b = s.index("  </details>", a)
s = s[:a] + """    <p>The corpus has no such category. A script gives every utterance one type, in two steps.</p>
    <p><b>Step 1: read the parse.</b> Each sentence in the utterance has a parse in the corpus. Its top label decides a first type:</p>
    <table>
      <tr><th>Complete sentence</th><td>The parse is a clause (top label S, SQ, SBARQ or SINV) that the annotators did not mark as unfinished. A clause that opens with "because" and has a full sentence after it counts too.</td></tr>
      <tr><th>Unfinished clause</th><td>The parse is a clause the annotators marked as unfinished (the tag -UNF, outside any repair).</td></tr>
      <tr><th>Response token</th><td>The parse is an interjection (top label INTJ): "yeah", "uh-huh", "right".</td></tr>
      <tr><th>Fragment</th><td>Anything else: a noun phrase, a prepositional phrase, a clause opening with "if" or "when" that stands alone. Nearly all of these have no main verb.</td></tr>
    </table>
    <p>Where an utterance holds more than one parsed sentence, it takes the type of the longest.</p>
    <p><b>Step 2: three corrections,</b> applied in this order:</p>
    <ol>
      <li>An utterance of linking words only ("and", "but", "so", "or", "because"), with or without an "uh" or "um", is a <b>fragment</b>.</li>
      <li>A fragment the transcribers marked as abandoned is an <b>unfinished clause</b>: the speaker started something and dropped it ("what I-").</li>
      <li>A complete sentence is <b>with a disfluency</b> if it holds any repair or any disfluent word (the six kinds in the next entry). Otherwise it is <b>fluent</b>.</li>
    </ol>
    <p>Words are then counted by the type of the utterance they sit in.</p>
    <p class="note">The step 2 corrections were added after a trial in which 30 utterances were coded by hand and compared with the script. The revised rules have not yet been checked against a full hand-coded sample.</p>
""" + s[b:]

# ---- info panel: disfluent words ------------------------------------------------------------
swap("<b>Disfluent words, and their five kinds</b>", "<b>Disfluent words, and their six kinds</b>")
a = s.index("    <p>A word counts as disfluent if the corpus marks it as one of four things.")
b = s.index("  </details>", a)
s = s[:a] + """    <p>A word counts as disfluent if the corpus marks it as one of five things. The marks are the corpus's. The plain names, the choice of "you know" from among the discourse markers, and the split of filled pauses into two, are ours.</p>
    <table>
      <tr><th>Repeated or reworded</th><td>The part of a repair that gets redone: the words a speaker says and then says again ("about, uh, about") or changes ("we were, I was"). The corpus calls this the reparandum.</td></tr>
      <tr><th>Editing term</th><td>Words that flag a repair, nearly always "I mean".</td></tr>
      <tr><th>Cut-off word</th><td>A word broken off before its end, outside a repair.</td></tr>
      <tr><th>"You know"</th><td>The two words, where the corpus marks them as a discourse marker. "You know" said as part of a sentence ("you know the one") is not counted. Other discourse markers, such as "well" and "like", are not counted either.</td></tr>
      <tr><th>"Uh" and "um"</th><td>Filled pauses, split by which of the two was said.</td></tr>
    </table>
    <p>Rates are these words per 100 words spoken.</p>
""" + s[b:]

open(path, "w", encoding="utf-8").write(s)
print("patched", path)
