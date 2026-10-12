p='/mnt/user-data/outputs/switchboard_viz.html'; s=open(p).read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n, (s.count(a), a[:80])
    s=s.replace(a,b)

# ================================================================ 1. the cue becomes a bracket
rep('''  /* the cue written on a bar in focus, saying what a second click does. It pulses slowly. */
  .cue { animation: cue 2.6s ease-in-out infinite; }
  .detail text.cue { fill: var(--paper); text-anchor: middle; dominant-baseline: central; }
  .wcue { fill: var(--ink); font-size: 9.5px; text-anchor: end; }
  @keyframes cue { 50% { opacity: 0.45; } }
''','''  /* the cue beside a bar in focus: a thin bracket with a line of text across its middle, saying
     what a second click does. The text has an outline in the page color, which breaks the bracket behind it. */
  .cue path { fill: none; stroke: var(--ink); }
  .cue text { font-family: var(--label-font); font-weight: 300; fill: var(--ink); text-transform: uppercase; letter-spacing: 0.16em;
              text-anchor: middle; dominant-baseline: central; paint-order: stroke; stroke: var(--paper); stroke-linejoin: round; }
  .wdetail .cue path { stroke-width: 1; }
  .wdetail .cue text { font-size: 9.5px; stroke-width: 7px; }
''')
rep('''// What is written on a bar in focus, to say that a second click opens it.''',
    '''// What is written across the bracket beside a bar in focus, to say that a second click opens it.''')
rep('''  bars.append("g").attr("class", "detail")                            // 2. the cue, written up the ink segment
    .append("text").attr("class", "header cue").text(umbrellaCue);
''','''  const cue = bars.append("g").attr("class", "detail cue");           // 2. the cue: a bracket left of the bar, with text across it
  cue.append("path");
  cue.append("text").text(umbrellaCue);
''')
rep('''
  // The cue runs up the middle of the ink segment. In the header style a line of text is about
  // 0.75 font-sizes per letter long, so the size is brought down if the segment is short.
  const ink = segmentsOf(d)[inkType];
  const cueSize = Math.min(13, ((ink.y1 - ink.y0) * k - 20) / (0.75 * umbrellaCue.length), L.barWidth * k * 0.6);
  bar.select(".cue").attr("transform", `translate(0,${ink.mid}) rotate(-90)`).attr("font-size", px(cueSize));
''','''
  // The cue: a bracket as tall as the bar, standing to the left of the bar's name, with the
  // text written across its middle.
  const nameSize = parseFloat(getComputedStyle(bar.select(".name").node()).fontSize);
  const bracketX = -edge - 6 - nameSize - px(16), tick = px(6);
  bar.select(".cue path").attr("stroke-width", px(1))
    .attr("d", `M${bracketX + tick},${-barHeight}H${bracketX}V0H${bracketX + tick}`);
  bar.select(".cue text").attr("font-size", px(10)).attr("stroke-width", px(8))
    .attr("transform", `translate(${bracketX},${-barHeight / 2}) rotate(-90)`);
''')
rep('''    ? -edge - 6 - 13 - px(10)                                        // clear of the name''',
    '''    ? bracketX - px(14)                                              // clear of the bracket''')
rep('''  const left = Math.min(-edge - 6 - 14, stripBox.x), right = Math.max(sharesRight(), stripBox.x + stripBox.width);''',
    '''  const left = Math.min(bracketX - px(8), stripBox.x), right = Math.max(sharesRight(), stripBox.x + stripBox.width);''')
rep('''  waveWorld.select(".wdetail").append("text").attr("class", "header cue wcue").text(callCue);   // and the cue beside it''',
    '''  const cue = waveWorld.select(".wdetail").append("g").attr("class", "cue");   // and the cue: a bracket with text across it
  cue.append("path");
  cue.append("text").text(callCue);''')
rep('''  // The cue is written down the gap on the call's left, beside its white segment.
  waveWorld.select(".wcue").attr("transform", `translate(${call.cx - WV.barWidth / 2 - 5},${WV.mid + 8}) rotate(-90)`);
''','''  // The cue: a bracket as tall as the call's bar, in the gap on its left, with the text across its middle.
  const bracketX = call.cx - WV.barWidth / 2 - 8;
  const top = WV.mid + d3.min(call.segments, s => s.y), bottom = WV.mid + d3.max(call.segments, s => s.y + s.height);
  waveWorld.select(".cue path").attr("d", `M${bracketX + 5},${top}H${bracketX}V${bottom}H${bracketX + 5}`);
  waveWorld.select(".cue text").attr("transform", `translate(${bracketX},${(top + bottom) / 2}) rotate(-90)`);
''')

# ================================================================ 2. the info button and panel
rep('''  #hud { position: fixed; top: 22px; left: clamp(20px, 7vw, 90px); right: 20px; max-width: 36rem;''',
    '''  #hud { position: fixed; top: 22px; left: clamp(20px, 7vw, 90px); right: 64px; max-width: 36rem;''')
rep('''  #loader { position: fixed;''','''  /* the "i" button in the corner and the panel it opens */
  #info-button { position: fixed; top: 16px; right: 18px; z-index: 12; width: 30px; height: 30px; padding: 0; border-radius: 50%;
                 border: 1px solid var(--ink); background: var(--paper); color: var(--ink); cursor: pointer;
                 font: italic 600 16px/1 Georgia, "Times New Roman", serif; }
  #info-button[aria-expanded="true"] { font: 400 18px/1 var(--header-font); }
  #info-button:focus-visible { outline: 2px solid var(--fluent); outline-offset: 2px; }
  #info-backdrop { position: fixed; inset: 0; z-index: 10; }
  #info { position: fixed; top: 0; right: 0; bottom: 0; z-index: 11; box-sizing: border-box; width: min(29rem, 100vw);
          padding: 22px 22px 28px; overflow-y: auto; background: var(--paper); color: var(--ink);
          border-left: 1px solid var(--ink); font-size: 13.5px; line-height: 1.5; }
  #info h2 { margin: 0 44px 10px 0; font-size: 15px; line-height: 1.3; }
  #info h3 { margin: 22px 0 6px; font-size: 11px; color: var(--muted); }
  #info p { margin: 0 0 10px; }
  #info ul { margin: 0 0 10px; padding-left: 1.1em; }
  #info li { margin-bottom: 4px; }
  #info details { border-top: 1px solid color-mix(in srgb, var(--ink) 22%, transparent); }
  #info details:last-of-type { border-bottom: 1px solid color-mix(in srgb, var(--ink) 22%, transparent); }
  #info summary { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; cursor: pointer; list-style: none; }
  #info summary::-webkit-details-marker { display: none; }
  #info summary::after { content: "+"; flex: none; color: var(--muted); }
  #info details[open] summary::after { content: "\\2212"; }
  #info summary b { font-weight: 600; }
  #info summary span { display: block; color: var(--muted); }
  #info table { width: 100%; margin: 0 0 10px; border-collapse: collapse; font-size: 12.5px; }
  #info th, #info td { padding: 5px 10px 5px 0; text-align: left; vertical-align: top;
                       border-top: 1px solid color-mix(in srgb, var(--ink) 12%, transparent); }
  #info th { font-weight: 600; white-space: nowrap; }
  #info code { font-size: 12px; }
  #info .note { color: var(--muted); }

  #loader { position: fixed;''')

rep('''<!-- Shown only when the page cannot fetch the data file by itself''','''<!-- The "i" button in the corner, and the panel it opens: what comes from the corpus, what was made for
     this piece, and the rule behind each thing that was made. Each rule is a <details> block that opens on a click. -->
<button id="info-button" type="button" aria-label="About the data" aria-expanded="false" aria-controls="info">i</button>
<div id="info-backdrop" hidden></div>
<aside id="info" hidden>
  <h2 class="header">What is measured, and what was made</h2>
  <p>The talk, the topics and the marks on each word come from the Switchboard corpus: telephone calls between strangers, recorded in 1991 and 1992 and annotated by people. The categories you see in the bars were made for this piece. Each one is produced by a fixed rule, written out below, so the same files always give the same picture. No category was assigned case by case, by a person or by an AI model. One thing is a judgment call: which topics sit under which umbrella.</p>

  <h3 class="header">From the corpus, as annotated</h3>
  <details>
    <summary><div><b>The words, topics, dates and annotations</b><span>Used as they are</span></div></summary>
    <ul>
      <li><b>The words of each call</b> and who said them: the Switchboard transcripts.</li>
      <li><b>Topic:</b> the prompt the two callers were given. It is not a coding of what they went on to say.</li>
      <li><b>Date</b> of the call.</li>
      <li><b>Disfluency marks on words:</b> filled pauses, editing terms, repairs (with the part that gets redone marked off) and cut-off words, from the corpus's disfluency annotation.</li>
      <li><b>A parse of each sentence,</b> from the Penn Treebank release of Switchboard. The sentence types below are read off these parses.</li>
    </ul>
  </details>

  <h3 class="header">Made for this piece, by rule</h3>
  <details>
    <summary><div><b>The five sentence types</b><span>The colors of every bar</span></div></summary>
    <p>The corpus has no such category. A script reads the parse of each sentence and gives it one type:</p>
    <table>
      <tr><th>Complete, fluent</th><td>The parse is a clause (its top label is S, SQ, SBARQ or SINV), it is not marked unfinished, and it has none of the three marks in the next row.</td></tr>
      <tr><th>Complete, with a disfluency</th><td>The same, but it contains at least one of: a repair (an EDITED node in the parse), an "uh" or "um", or a cut-off word.</td></tr>
      <tr><th>Unfinished clause</th><td>The parse is a clause that the annotators marked as unfinished (the tag -UNF, outside any repair).</td></tr>
      <tr><th>Response token</th><td>The parse is an interjection (top label INTJ): "yeah", "uh-huh", "right".</td></tr>
      <tr><th>Fragment</th><td>Anything else: a noun phrase, a prepositional phrase, and so on.</td></tr>
    </table>
    <p>Where an utterance holds more than one parsed sentence, it takes the type of the longest. Words are then counted by the type of the utterance they sit in.</p>
    <p class="note">These rules have not been checked against hand coding.</p>
  </details>
  <details>
    <summary><div><b>Disfluent words, and their five kinds</b><span>The thin column beside an umbrella; the colored words in a line of talk</span></div></summary>
    <p>A word counts as disfluent if the corpus marks it as one of four things. The marks are the corpus's; the plain names, and the split of filled pauses into two, are ours.</p>
    <table>
      <tr><th>Repeated or reworded</th><td>The part of a repair that gets redone: the words a speaker says and then says again ("about, uh, about") or changes ("we were, I was"). The corpus calls this the reparandum.</td></tr>
      <tr><th>Editing term</th><td>Words that flag a repair, nearly always "I mean".</td></tr>
      <tr><th>Cut-off word</th><td>A word broken off before its end, outside a repair.</td></tr>
      <tr><th>"Uh" and "um"</th><td>Filled pauses, split by which of the two was said.</td></tr>
    </table>
    <p>Rates are these words per 100 words spoken.</p>
  </details>
  <details>
    <summary><div><b>The 650 calls</b><span>Which calls are in the piece</span></div></summary>
    <p>This release of the corpus holds 1,155 calls. Only 650 of them come with parses, and without a parse a sentence cannot be given a type, so the piece shows those 650.</p>
  </details>
  <details>
    <summary><div><b>The average call</b><span>The umbrella bars</span></div></summary>
    <p>A bar's height is the mean number of words per call among the calls under that umbrella. Each segment is the mean number of those words that sit in one sentence type.</p>
  </details>
  <details>
    <summary><div><b>The order of calls on the black screen</b><span>Why each topic looks like a hump</span></div></summary>
    <p>Topics run in alphabetical order. Inside a topic the calls are sorted by length and dealt alternately to the left and the right, so the longest land in the middle. Bar heights share one scale within an umbrella, not across umbrellas.</p>
  </details>
  <details>
    <summary><div><b>The lines of talk</b><span>The quotes beside a call in focus</span></div></summary>
    <p>Each quote is chosen by rule from that call's own utterances of that type.</p>
    <ul>
      <li><b>Response tokens:</b> the wording used most often in the call.</li>
      <li><b>The other four types:</b> the utterance whose length in words is closest to the median for that type in the call. If two are equally close, the earlier one.</li>
    </ul>
    <p class="note">A quote is typical in length only. It does not claim to be typical of what was said.</p>
  </details>

  <h3 class="header">Made for this piece, by judgment</h3>
  <details>
    <summary><div><b>The ten topic umbrellas</b><span>Which topics are grouped together</span></div></summary>
    <p>The corpus lists 64 topic prompts among these calls and does not group them. The grouping below was decided by hand, and a different grouping would move calls between bars.</p>
    <ul id="info-umbrellas"></ul>
    <p class="note">A few topic names are abbreviated in the corpus and are spelled out here.</p>
  </details>

  <p class="note" style="margin-top:18px">The sentence types and word marks are computed by <code>extract_swda.py</code>; everything else is computed in this page. Running the script again on the corpus reproduces every data file exactly.</p>
</aside>

<!-- Shown only when the page cannot fetch the data file by itself''')

rep('''  document.addEventListener("keydown", event => { if (event.key === "Escape") goBack(); });''',
    '''  document.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    if (!infoPanel.hidden) showInfo(false); else goBack();              // Escape closes the info panel first
  });''')
rep('''function debounce(fn, wait) {''','''// ===========================================================================
// 11. THE INFO PANEL
// The text of the panel is in the HTML near the top of this file. Here it is
// opened and closed, and the list of umbrellas is written from the same table
// the bars are built from, so the two cannot drift apart.
// ===========================================================================
const infoButton = document.querySelector("#info-button");
const infoPanel = document.querySelector("#info"), infoBackdrop = document.querySelector("#info-backdrop");

function showInfo(open) {
  infoPanel.hidden = infoBackdrop.hidden = !open;
  infoButton.setAttribute("aria-expanded", open);
  infoButton.textContent = open ? "\\u00d7" : "i";
}
infoButton.addEventListener("click", () => showInfo(infoPanel.hidden));
infoBackdrop.addEventListener("click", () => showInfo(false));          // a click outside the panel only closes it

d3.select("#info-umbrellas").selectAll("li").data(Object.entries(umbrellas)).join("li").each(function ([name, topics]) {
  d3.select(this).append("b").text(name + ": ");
  d3.select(this).append("span").text(topics.map(topicName).sort(d3.ascending).join(", "));
});

function debounce(fn, wait) {''')
rep("\\u00d7", "×", 1)
open(p,'w').write(s); print('patched')
