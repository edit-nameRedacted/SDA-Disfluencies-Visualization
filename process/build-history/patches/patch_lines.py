p='/mnt/user-data/outputs/switchboard_viz.html'; s=open(p).read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n, (s.count(a), a[:80])
    s=s.replace(a,b)

# ---------------------------------------------------------------- CSS
rep('''  body.black { --paper: #0c0c0c; --ink: #f8f7f3; --muted: #a3a29a;
               --fluent: #3987e5; --unfinished: #d95926; --fragment: #199e70; --response: #6f6e68; }
''','''  body.black { --paper: #0c0c0c; --ink: #f8f7f3; --muted: #a3a29a;
               --fluent: #3987e5; --unfinished: #d95926; --fragment: #199e70; --response: #6f6e68;
               --replaced: #e0558a; --editing: #f3a3c0; --uh: #9085e9; --um: #c2bbf5; }
''')
rep('''  .wvalue, .topic, .wdetail text { font-family: var(--label-font); font-weight: 300; fill: var(--ink); }''',
    '''  .wvalue, .topic { font-family: var(--label-font); font-weight: 300; fill: var(--ink); }''')
rep('''  .wdetail text { font-size: 12.5px; }
  .wdetail .pct { font-weight: 600; }
  .wdetail line { stroke: var(--muted); }
''','''  .wdetail line { stroke: var(--muted); }
''')
rep('''  /* text laid over the stage */''','''  /* the lines of talk beside a call in focus: ordinary HTML laid over the drawing, so long lines can wrap */
  #lines { position: fixed; inset: 0; pointer-events: none; opacity: 0; transition: opacity 0.4s; }
  #lines.shown { opacity: 1; }
  #lines p { position: absolute; margin: 0; width: max-content; box-sizing: border-box; padding-left: 3.3em; text-indent: -3.3em;
             font: 300 13.5px/1.35 var(--label-font); color: var(--ink); }
  #lines .pct { display: inline-block; width: 2.8em; margin-right: 0.5em; text-indent: 0; font-weight: 600; font-variant-numeric: tabular-nums; }
  #lines .count { color: var(--muted); margin-left: 0.6em; }
  .w-rp { color: var(--replaced); text-decoration: line-through; }
  .w-et { color: var(--editing); }
  .w-fr { color: var(--cutoff); }
  .w-uh { color: var(--uh); }
  .w-um { color: var(--um); }
  #word-key { display: none; margin: 8px 0 0; font: 300 12.5px/1.35 var(--label-font); color: var(--muted); }
  body.black #word-key { display: block; visibility: hidden; }
  body.black #hud.with-lines #word-key { visibility: visible; }

  /* text laid over the stage */''')

# ---------------------------------------------------------------- HTML
rep('''  <ul id="legend"></ul>
</div>''','''  <ul id="legend"></ul>
  <p id="word-key">Disfluent words in the lines: <span class="w-rp">replaced</span> · <span class="w-et">editing term</span> · <span class="w-fr">cut-off</span> · <span class="w-uh">uh</span> · <span class="w-um">um</span></p>
</div>
<div id="lines"></div>''')

# ---------------------------------------------------------------- settings
rep('''const dataFile = "conversations.csv";
''','''const dataFile = "conversations.csv";
// The folder of per-call files, also written by extract_swda.py: one <call number>.json each.
// A call's file is fetched when the call is put in focus, so the page must come from a web server.
const callFolder = "conversations/";
''')

# ---------------------------------------------------------------- hud text
rep('''    line.textContent = describeCall(waveFocused) + " Click the bar again to open the call, or click anywhere else to go back.";''',
    '''    line.textContent = describeCall(waveFocused) + (waveFocused.picked ? " Beside it, in the callers' own words, is a typical line of each kind." : "") +
      " Click the bar again to open the call, or click anywhere else to go back.";''')
rep('''Each bar is one call: complete sentences rise above the line, everything else hangs below it. ` +''',
    '''Each bar is one call: fluent, complete sentences rise above the line and everything else hangs below it. ` +''')

# ---------------------------------------------------------------- midline split
rep('''// A call's bar straddles a midline: its complete sentences rise above the line
// (those with a disfluency in white next to the line, the fluent ones in blue
// at the tip) and the three kinds that are not sentences hang below it.''','''// A call's bar straddles a midline: its fluent, complete sentences rise above
// the line in blue, and everything else hangs below it, starting with the
// complete sentences that carry a disfluency, in white, next to the line.''')
rep('''const above = [1, 0];            // types drawn above the midline, nearest the line first
const below = [2, 3, 4];         // types drawn below it, nearest the line first''','''const above = [0];               // types drawn above the midline, nearest the line first
const below = [1, 2, 3, 4];      // types drawn below it, nearest the line first''')
rep('''  const s = call.segments[0];                                        // the white segment, just above the midline''',
    '''  const s = call.segments.find(s => s.type === inkType);             // the white segment, just below the midline''')

# ---------------------------------------------------------------- build: detail group keeps only the leaders
rep('''  const detail = waveWorld.append("g").attr("class", "wdetail")      // share labels for the call in focus
    .selectAll("g").data(d3.range(keys.length)).join("g");
  detail.append("line");
  const text = detail.append("text").attr("dy", "0.35em");
  text.append("tspan").attr("class", "pct");
  text.append("tspan").attr("class", "what").attr("dx", "0.5em");
''','''  waveWorld.append("g").attr("class", "wdetail")                     // leaders from the call in focus to its lines of talk
    .selectAll("line").data(d3.range(keys.length)).join("line");
  linesBox.classed("shown", false).selectAll("p").data(d3.range(keys.length)).join("p");
  hud.classList.remove("with-lines");
''')

# ---------------------------------------------------------------- focus
i=s.index('function focusCall(call) {'); j=s.index('function unfocusCall() {')
s=s[:i]+'''function focusCall(call) {
  state = "wave-focus";
  waveFocused = call;
  setHudLine();
  waveWorld.classed("has-focus", true);
  waveWorld.selectAll(".wbar").classed("is-focused", other => other === call);
  waveWorld.selectAll(".wdetail line").data(call.segments);
  writeLines(call);                                                  // shares and type names at once ...
  linesBox.classed("shown", true);
  loadLines(call).then(() => {                                       // ... and the callers' words as soon as the file arrives
    if (waveFocused !== call) return;
    writeLines(call);
    setHudLine();
    placeCallDetail();
  });
  // Stretch the row until a slot is 56px wide (or keep the current stretch if it is wider),
  // and slide it so the call sits left of centre, leaving room for its lines.
  const k = Math.max(zoomT.k, WV.focusZoom);
  const screenX = W < 700 ? 0.22 : 0.36;
  const target = d3.zoomIdentity.translate(screenX * W - k * WV.x(call.slot + 0.5), 0).scale(k);
  waveSvg.transition("stretch").duration(ms(700)).call(WV.zoom.transform, target);
}

// ---------------------------------------------------------------------------
// The lines of talk. Each call has its own file, holding every utterance word by
// word. From it we pick one example line per sentence type:
//   - response tokens: the wording used most often in the call ("yeah", "uh-huh");
//   - every other type: the utterance whose length is the median for that type in
//     the call, so it is neither a long nor a short example. Ties go to the earlier one.
// ---------------------------------------------------------------------------
const linesBox = d3.select("#lines");
const responseType = 4;

// Fetch the call's file once and keep what was picked on the call's own row.
function loadLines(call) {
  if (!call.loading) {
    call.loading = d3.json(`${callFolder}${call.conversation_no}.json`)
      .then(conversation => { call.picked = pickLines(conversation); },
            () => { call.picked = null; });                          // no file: the type names stay in place
  }
  return call.loading;
}

function pickLines(conversation) {
  // An utterance is cut into pieces when the other speaker comes in halfway. Pieces share an id; join them back together.
  const utterances = new Map();
  for (const turn of conversation.turns) {
    for (const piece of turn.u) {
      if (!utterances.has(piece.id)) utterances.set(piece.id, { type: keys.indexOf("stw_" + piece.st), words: [] });
      utterances.get(piece.id).words.push(...piece.w);               // each word is a pair: [the word, its class]
    }
  }
  return types.map((type, i) => {
    const group = [...utterances.values()].filter(u => u.type === i && u.words.length);
    if (!group.length) return null;
    if (i === responseType) {
      const wording = u => u.words.map(word => word[0]).join(" ").toLowerCase();
      const [commonest, count] = d3.greatest(d3.rollups(group, same => same.length, wording), entry => entry[1]);
      return { words: group.find(u => wording(u) === commonest).words, count, of: group.length };
    }
    const median = d3.median(group, u => u.words.length);
    return { words: d3.least(group, u => Math.abs(u.words.length - median)).words };
  });
}

// Fill the five paragraphs for a call: its share of each type, then the picked line with its
// disfluent words colored by kind, or the type's name while there is no line to show.
function writeLines(call) {
  hud.classList.toggle("with-lines", !!call.picked);
  linesBox.selectAll("p").data(call.segments).each(function (s) {
    const p = d3.select(this).html("");
    p.append("span").attr("class", "pct").text(pct(s.share));
    const line = call.picked && call.picked[s.type];
    if (!line) return p.append("span").text(types[s.type].short);
    p.append("span").text("\\u201c");
    line.words.forEach(([word, kind], i) => {
      const css = kind === "fp" ? (/^um/i.test(word) ? "w-um" : "w-uh") : { rp: "w-rp", et: "w-et", fr: "w-fr" }[kind];
      p.append("span").attr("class", css ?? null).text(word);
      p.append("span").text(i < line.words.length - 1 ? " " : "\\u201d");
    });
    if (line.count) p.append("span").attr("class", "count").text(`${line.count} of ${line.of} response tokens`);
  });
}

// Put each line level with its segment, to the right of the call in focus, and tie the two with a leader.
function placeCallDetail() {
  const call = waveFocused, edge = call.cx + WV.barWidth / 2, left = edge + 14;
  const paragraphs = linesBox.selectAll("p").style("left", left + "px").style("max-width", Math.max(140, Math.min(430, W - left - 12)) + "px");
  // Top to bottom, each line starts level with its segment, or just under the line before it.
  // If the last one would run off the screen, the lines are pushed back up from the bottom.
  const order = d3.sort(paragraphs.nodes().map(node => ({ node, s: d3.select(node).datum(), height: node.offsetHeight })), item => item.s.mid);
  let floor = -Infinity;
  for (const item of order) { item.top = Math.max(WV.mid + item.s.mid - 9, floor); floor = item.top + item.height + 5; }
  let ceiling = H - 8;
  for (const item of order.slice().reverse()) { item.top = Math.min(item.top, ceiling - item.height); ceiling = item.top - 5; }
  for (const item of order) { item.node.style.top = item.top + "px"; item.s.at = item.top + 9; }
  waveWorld.selectAll(".wdetail line")
    .attr("x1", edge + 2).attr("y1", s => WV.mid + s.mid).attr("x2", edge + 10).attr("y2", s => s.at);
  // Calls and topic names that would sit under the lines step out while this call is in focus.
  const right = left + d3.max(order, item => item.node.offsetWidth) + 10;
  waveWorld.selectAll(".wbar").classed("is-covered", other => other !== call && other.cx > call.cx && other.cx - WV.barWidth / 2 < right);
  waveWorld.selectAll(".topic").filter(topic => topic.cx > call.cx && topic.cx - 12 < right).style("opacity", 0);
}

'''+s[j:]
rep("\\u201c", "“", 1); rep("\\u201d", "”", 1)

rep('''  waveWorld.selectAll(".is-covered").classed("is-covered", false);
  setHudLine();
  resetWaveZoom(700);''','''  waveWorld.selectAll(".is-covered").classed("is-covered", false);
  linesBox.classed("shown", false);
  hud.classList.remove("with-lines");
  setHudLine();
  resetWaveZoom(700);''')
rep('''  waveWorld.classed("zooming", true);
  hud.classList.add("faded");
  flyWave(homeView(), WV.dive, 1300)''','''  waveWorld.classed("zooming", true);
  linesBox.classed("shown", false);
  hud.classList.add("faded");
  flyWave(homeView(), WV.dive, 1300)''')
rep('''    waveWorld.attr("transform", null).classed("zooming", false);
    hud.classList.remove("faded");
    busy = false;''','''    waveWorld.attr("transform", null).classed("zooming", false);
    linesBox.classed("shown", true);
    hud.classList.remove("faded");
    busy = false;''')
rep('''// First click on a call: focus (the row stretches, and the call's shares appear).''','''// First click on a call: focus (the row stretches, and lines from the call appear).''')
open(p,'w').write(s); print('patched')
