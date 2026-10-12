p='/mnt/user-data/outputs/switchboard_viz.html'; s=open(p).read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n, (s.count(a), a[:80])
    s=s.replace(a,b)

# ---------------------------------------------------------------- CSS
rep('''  body.black #hud.with-lines #word-key { visibility: visible; }
''','''  body.black #hud.with-lines #word-key { visibility: visible; }
  /* on the white single-call screen the key's words sit on small dark chips, so the light colors stay readable */
  #hud.on-call #word-key { display: block; --replaced: #e0558a; --editing: #f3a3c0; --uh: #9085e9; --um: #c2bbf5; }
  #hud.on-call #word-key span { padding: 1px 5px 2px; border-radius: 3px; background: var(--ink); }
''')
rep('''  #call { position: fixed; inset: 0; display: grid; place-items: center; padding: 24px; text-align: center; cursor: pointer; }
  #call h2 { margin: 0 0 8px; font-size: 20px; }
  #call p { margin: 0 0 4px; color: var(--muted); }''','''  /* the single-call screen */
  #call { position: fixed; inset: 0; cursor: pointer; }
  #call-svg { display: block; width: 100%; height: 100%; }
  #call-note { position: absolute; left: clamp(20px, 7vw, 90px); right: 20px; max-width: 34rem; margin: 0; color: var(--muted); }
  .piece { transition: opacity 0.2s; }
  .piece.untyped { fill: var(--paper); stroke: var(--muted); stroke-width: 1; }
  .wait { fill: none; stroke: var(--ink); stroke-width: 0.9; stroke-linecap: round; opacity: 0.8; }
  .lane-name { font: 600 9.5px var(--header-font); fill: var(--muted); text-anchor: end; dominant-baseline: central; }
  #call-svg.pointing .piece:not(.on) { opacity: 0.28; }
  /* the bubble that shows one utterance. It is dark on the white page, so the words keep the colors they have on the black screen. */
  #say { position: fixed; z-index: 8; box-sizing: border-box; width: max-content; max-width: min(27rem, calc(100vw - 24px)); padding: 9px 12px 10px;
         border-radius: 4px; background: var(--ink); color: var(--paper); pointer-events: none;
         font: 300 13.5px/1.4 var(--label-font); --replaced: #e0558a; --editing: #f3a3c0; --uh: #9085e9; --um: #c2bbf5; }
  #say .who { margin: 0 0 4px; font: 600 9.5px/1.3 var(--header-font); letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.7; }
  #say p { margin: 0; }''')

# ---------------------------------------------------------------- HTML
i=s.index('<!-- Stands in for the single-call screen until it is built. -->'); j=s.index('<!-- The "i" button in the corner')
s=s[:i]+'''<!-- The single-call screen: the drawing, a note for when the call's file cannot be read, and the bubble that shows one utterance. -->
<div id="call" hidden>
  <svg id="call-svg" aria-label="One call, utterance by utterance"></svg>
  <p id="call-note" hidden></p>
</div>
<div id="say" hidden></div>

'''+s[j:]
rep('''      <li><b>A parse of each sentence,</b> from the Penn Treebank release of Switchboard. The sentence types below are read off these parses.</li>''',
    '''      <li><b>A parse of each sentence,</b> from the Penn Treebank release of Switchboard. The sentence types below are read off these parses.</li>
      <li><b>A dialog act for each utterance:</b> what it is doing, such as a statement, a question or a backchannel. The corpus has 42 kinds; their names are shortened here.</li>''')
rep('''
  <h3 class="header">Made for this piece, by judgment</h3>''','''  <details>
    <summary><div><b>The two strands and the cord</b><span>The single call</span></div></summary>
    <p>Each bar is one utterance, as long as its number of words, placed in the order the transcript gives. The upper strand is the person who placed the call, the lower strand the person who answered. Where the other speaker comes in halfway through an utterance, it shows as two bars of the same color.</p>
    <p>Where a strand turns to cord, that person is waiting: the cord is as long as the words the other person says in the meantime. It is not silence. This release of the corpus has no timing, so the piece cannot show how long anything took, or where two people spoke at once.</p>
    <p class="note">An outlined bar is an utterance with no parse, and so no type.</p>
  </details>

  <h3 class="header">Made for this piece, by judgment</h3>''')

# ---------------------------------------------------------------- build / resize
rep('''  if (state === "wave" || state === "wave-focus" || state === "call") {   // the umbrella screen is hidden: redraw the waveform
    stageStale = true;                                               // and rebuild the umbrellas when we return to them
    return buildWave(false);
  }''','''  if (state === "call") {                                            // only the single call is showing: redraw it,
    stageStale = waveStale = true;                                   // and rebuild the other two screens when we return to them
    return drawCall(false);
  }
  if (state === "wave" || state === "wave-focus") {                  // the umbrella screen is hidden: redraw the waveform
    stageStale = true;                                               // and rebuild the umbrellas when we return to them
    return buildWave(false);
  }''')
rep('''let stageStale = false;    // true if the window was resized while the umbrella screen was hidden
''','''let stageStale = false;    // true if the window was resized while the umbrella screen was hidden
let waveStale = false;     // the same for the waveform, while the single call was showing
''')
rep('''  document.querySelector("#call").addEventListener("click", leaveCall);''',
    '''  document.querySelector("#call").addEventListener("click", () => (pinned ? hideSay() : leaveCall()));''')

# ---------------------------------------------------------------- hud text
rep('''  const onWave = state === "wave" || state === "wave-focus" || state === "call";
  hud.querySelector("h1").textContent = onWave ? focused.umbrella : "The average call, by topic";
  if (state === "focus" && focused) {''','''  const onWave = state === "wave" || state === "wave-focus";
  hud.querySelector("h1").textContent = state === "call" ? topicName(waveFocused.topic) : onWave ? focused.umbrella : "The average call, by topic";
  if (state === "call") {
    line.textContent = `${dayFormat(waveFocused.date)} \\u00b7 ${fmt(waveFocused.words)} words. Each bar is one utterance, as long as its words, in the order spoken. ` +
      "The caller is the upper strand, the person who answered the lower. A strand turns to cord while its speaker waits for the other. " +
      "Point at a bar to read it, or click empty space to go back.";
  } else if (state === "focus" && focused) {''')
rep("\\u00b7", "·", 1)

# ---------------------------------------------------------------- loading keeps the whole call
rep('''      .then(conversation => { call.picked = pickLines(conversation); },
            () => { call.picked = null; });                          // no file: the type names stay in place''',
    '''      .then(conversation => { call.conversation = conversation; call.picked = pickLines(conversation); },
            () => { call.picked = null; });                          // no file: the type names stay in place''')

# ---------------------------------------------------------------- one shared way to write colored words
rep('''    p.append("span").text("“");
    line.words.forEach(([word, kind], i) => {
      const css = kind === "fp" ? (/^um/i.test(word) ? "w-um" : "w-uh") : { rp: "w-rp", et: "w-et", fr: "w-fr" }[kind];
      p.append("span").attr("class", css ?? null).text(word);
      p.append("span").text(i < line.words.length - 1 ? " " : "”");
    });
    if (line.count)''','''    writeWords(p, line.words);
    if (line.count)''')
rep('''// Put each line level with its segment,''','''// Write a line of talk in quotation marks, one <span> per word, with each disfluent word in the color of its kind.
function writeWords(into, words) {
  into.append("span").text("“");
  words.forEach(([word, kind], i) => {
    const css = kind === "fp" ? (/^um/i.test(word) ? "w-um" : "w-uh") : { rp: "w-rp", et: "w-et", fr: "w-fr" }[kind];
    into.append("span").attr("class", css ?? null).text(word);
    into.append("span").text(i < words.length - 1 ? " " : "”");
  });
}

// Put each line level with its segment,''')

# ---------------------------------------------------------------- zoom to white now opens the call
rep('''    state = "call";
    document.body.classList.remove("black");
    waveSvg.style("display", "none");
    document.querySelector("#call-title").textContent = topicName(call.topic);
    document.querySelector("#call-meta").textContent = `Call ${call.conversation_no} · ${dayFormat(call.date)} · ${fmt(call.words)} words`;
    document.querySelector("#call").hidden = false;
    busy = false;
  });
}''','''    state = "call";
    document.body.classList.remove("black");
    waveSvg.style("display", "none");
    document.querySelector("#call").hidden = false;
    hud.classList.add("on-call");
    hud.classList.remove("faded");
    callSvg.selectAll("*").remove();
    setHudLine();
    loadLines(call).then(() => {                                     // the file was fetched when the call came into focus,
      busy = false;                                                  // so this is nearly always immediate
      if (state === "call" && waveFocused === call) drawCall(true);
    });
  });
}''')
rep('''// This is the moment the single-call screen will load its data.''','''// By the time the page has turned white the call's file is already here, so the call can be drawn at once.''')
i=s.index('function leaveCall() {'); j=s.index('// Back to the umbrella screen: the page turns white again')
s=s[:i]+'''function leaveCall() {
  if (busy || state !== "call") return;
  hideSay();
  document.querySelector("#call").hidden = true;
  hud.classList.remove("on-call");
  document.body.classList.add("black");
  waveSvg.style("display", null);
  if (waveStale) {                                                   // the window changed size meanwhile: redraw the waveform, no animation
    waveStale = false;
    return buildWave(false);
  }
  busy = true;
  state = "wave-focus";
  setHudLine();
  hud.classList.add("faded");
  flyWave(WV.dive, homeView(), 1100).on("end", () => {
    waveWorld.attr("transform", null).classed("zooming", false);
    linesBox.classed("shown", true);
    hud.classList.remove("faded");
    busy = false;
  });
}

'''+s[j:]
rep('''  if (state !== "wave") { state = "wave"; document.querySelector("#call").hidden = true;      // a resize drops any focus
                          document.body.classList.add("black"); waveSvg.style("display", null); hud.classList.remove("faded"); }''',
    '''  state = "wave";                                                    // redrawing drops any focus''')

# ---------------------------------------------------------------- the call screen itself
rep('''// ===========================================================================
// 11. THE INFO PANEL''','''// ===========================================================================
// 12. ONE CALL, UTTERANCE BY UTTERANCE
// The call is laid out like lines of text. Words run left to right and wrap
// onto as many rows as needed; each row has two strands, one per speaker.
// On a strand, a bar is an utterance (as long as its words) and a stretch of
// coiled cord is that speaker waiting while the other one talks.
// ===========================================================================
const callSvg = d3.select("#call-svg"), sayBox = d3.select("#say");
let pinned = false;                                                  // true while a bubble was opened by a click (for touch screens)

// Short names for the corpus's dialog acts (the SWBD-DAMSL tags). Only the names are ours.
const actNames = {
  "sd": "statement", "sv": "opinion", "b": "backchannel", "aa": "agreement", "%": "abandoned or unclear", "ba": "appreciation",
  "qy": "yes-no question", "qy^d": "yes-no question, as a statement", "qw": "wh- question", "qw^d": "wh- question, as a statement",
  "qo": "open question", "qh": "rhetorical question", "qrr": "or- question", "^g": "tag question", "ny": "yes answer", "nn": "no answer",
  "na": "affirmative answer", "ng": "negative answer", "no": "other answer", "arp_nd": "dispreferred answer", "ar": "rejection",
  "aap_am": "partial acceptance or maybe", "bk": "acknowledgement", "bh": "backchannel as a question", "bf": "summing up",
  "b^m": "repeating the other's phrase", "^2": "completing the other's sentence", "br": "signalling non-understanding", "h": "hedge",
  "^h": "holding before an answer", "^q": "quotation", "ad": "request or instruction", "oo_co_cc": "offer or commitment",
  "fc": "closing", "fp": "opening", "ft": "thanks", "fa": "apology", "bd": "downplaying", "t1": "talking to oneself",
  "t3": "talking to someone else", "fo_o_fw_by_bc": "other", "x": "non-verbal"
};

function drawCall(grow) {
  const call = waveFocused, conversation = call.conversation;
  setHudLine();                                                      // set the heading text first: the layout measures it
  W = window.innerWidth;
  H = window.innerHeight;
  hideSay();
  callSvg.selectAll("*").remove();
  const side = clamp(W * 0.07, 20, 90), top = hud.offsetHeight + 22 + 30, bottom = H - 24;

  const note = document.querySelector("#call-note");
  note.hidden = !!conversation;
  if (!conversation) {                                               // no file for this call: say so, and leave it there
    note.style.top = top + "px";
    note.textContent = `This call's own file (${callFolder}${call.conversation_no}.json) could not be read, so there is nothing to draw. ` +
      "The page has to be opened through a web server, with the conversations folder beside it. Click anywhere to go back.";
    return;
  }

  // 1. Every piece of talk, in the order spoken, with where it starts and ends along the call, counted in words.
  const spans = [];
  let at = 0;
  for (const turn of conversation.turns) {
    for (const piece of turn.u) {
      if (!piece.w.length) continue;                                 // laughter and other noises carry no words
      spans.push({ speaker: turn.s, start: at, end: at += piece.w.length, piece, type: keys.indexOf("stw_" + piece.st) });
    }
  }
  const total = at;
  const wholeUtterance = d3.rollup(spans, pieces => pieces.flatMap(s => s.piece.w), s => s.piece.id);

  // 2. Each speaker's waits: the stretches where the other one is talking.
  const waits = [];
  for (const speaker of ["A", "B"]) {
    let from = 0;
    for (const s of spans) {
      if (s.speaker !== speaker) continue;
      if (s.start > from) waits.push({ speaker, start: from, end: s.start });
      from = s.end;
    }
    if (from < total) waits.push({ speaker, start: from, end: total });
  }

  // 3. Rows. A word is at most 8px wide; that sets how many rows the call needs. If they would not
  //    all fit on screen, use as many rows as do fit and let the words get narrower.
  const width = W - 2 * side;
  const fits = Math.max(1, Math.floor((bottom - top) / (W < 700 ? 30 : 40)));
  const rows = clamp(Math.ceil(total * 8 / width), 1, fits);
  const perRow = total / rows, perWord = width / perRow;             // words on a row; pixels per word
  const pitch = Math.min((bottom - top) / rows, 86);                 // distance from one row to the next
  const laneHeight = clamp(pitch * 0.25, 6, 16), laneGap = laneHeight * 0.5;
  const laneTop = (row, speaker) => top + row * pitch + (speaker === "A" ? 0 : laneHeight + laneGap);

  // Cut a stretch of the call into the part that falls on each row.
  const cut = stretch => {
    const parts = [];
    for (let row = Math.floor(stretch.start / perRow); row < rows && row * perRow < stretch.end; row++) {
      const a = Math.max(stretch.start, row * perRow), b = Math.min(stretch.end, (row + 1) * perRow);
      if (b > a) parts.push({ stretch, row, x0: side + (a - row * perRow) * perWord, x1: side + (b - row * perRow) * perWord });
    }
    return parts;
  };
  const appear = part => ms(100 + 1000 * (part.stretch.start / total));  // things appear in the order spoken

  // 4. Draw: lane names, then the cords, then the bars.
  callSvg.append("g").selectAll("text").data(d3.cross(d3.range(rows), ["A", "B"])).join("text")
    .attr("class", "lane-name").attr("x", side - 7).attr("y", ([row, speaker]) => laneTop(row, speaker) + laneHeight / 2)
    .text(([row, speaker]) => speaker);

  callSvg.append("g").selectAll("path").data(waits.flatMap(cut)).join("path")
    .attr("class", "wait")
    .attr("d", part => spring(part.x0 + 1, part.x1 - 1, laneTop(part.row, part.stretch.speaker) + laneHeight / 2, laneHeight * 0.36, clamp(laneHeight * 0.4, 3, 6)))
    .style("opacity", grow ? 0 : null)
    .transition().duration(ms(300)).delay(appear).style("opacity", null);

  callSvg.append("g").selectAll("rect").data(spans.flatMap(cut)).join("rect")
    .attr("class", part => (part.stretch.type < 0 ? "piece untyped" : "piece seg t" + part.stretch.type))
    .attr("x", part => part.x0).attr("y", part => laneTop(part.row, part.stretch.speaker))
    .attr("width", part => Math.max(1, part.x1 - part.x0 - (part.x1 - part.x0 > 3 ? 1 : 0)))
    .attr("height", laneHeight)
    .on("mouseenter", function (event, part) { pinned = false; say(part.stretch, this); })
    .on("mouseleave", () => { if (!pinned) hideSay(); })
    .on("click", function (event, part) { event.stopPropagation(); say(part.stretch, this); pinned = true; })
    .style("opacity", grow ? 0 : null)
    .transition().duration(ms(300)).delay(appear).style("opacity", null);

  // The bubble: who is speaking, the sentence type, the dialog act, then the whole utterance in its own words.
  function say(span, node) {
    callSvg.classed("pointing", true).selectAll(".piece").classed("on", part => part.stretch.piece.id === span.piece.id);
    const who = span.speaker === "A" ? "Caller" : "Answerer";
    const type = span.type < 0 ? "no type" : types[span.type].short;
    sayBox.html("").property("hidden", false);
    sayBox.append("p").attr("class", "who").text(`${who} \\u00b7 ${type} \\u00b7 ${actNames[span.piece.tag] ?? span.piece.tag}`);
    writeWords(sayBox.append("p"), wholeUtterance.get(span.piece.id));
    // Under the bar if there is room, otherwise above it; never off the side of the screen.
    const bar = node.getBoundingClientRect(), box = sayBox.node();
    const under = bar.bottom + 8 + box.offsetHeight < H - 8;
    sayBox.style("left", clamp(bar.left, 12, W - box.offsetWidth - 12) + "px")
          .style("top", (under ? bar.bottom + 8 : bar.top - 8 - box.offsetHeight) + "px");
  }
}

function hideSay() {
  pinned = false;
  sayBox.property("hidden", true);
  callSvg.classed("pointing", false).selectAll(".on").classed("on", false);
}

// A coiled cord along a straight line from x0 to x1: a point moves steadily to the right while going
// round a small circle, which draws one loop per turn. pitch is the distance between loops.
function spring(x0, x1, y, radius, pitch) {
  const length = x1 - x0;
  if (length < 2) return null;
  const loops = Math.max(1, Math.round(length / pitch)), steps = loops * 12, points = [];
  for (let i = 0; i <= steps; i++) {
    const angle = (i / steps) * loops * 2 * Math.PI;
    points.push([x0 + (i / steps) * length + radius * 0.7 * Math.sin(angle), y - radius * Math.cos(angle)]);
  }
  return d3.line().curve(d3.curveBasis)(points);
}

// ===========================================================================
// 11. THE INFO PANEL''')
rep("\\u00b7", "·", 2)
# number the sections in reading order: the call screen is 11, the info panel 12
rep("// 12. ONE CALL, UTTERANCE BY UTTERANCE", "// 11. ONE CALL, UTTERANCE BY UTTERANCE")
rep("// 11. THE INFO PANEL", "// 12. THE INFO PANEL")
open(p,'w').write(s); print('patched')
