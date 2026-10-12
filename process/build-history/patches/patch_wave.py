p='/mnt/user-data/outputs/switchboard_viz.html'; s=open(p).read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n, (s.count(a), a[:80])
    s=s.replace(a,b)

# ------------------------------------------------------------------ CSS
rep('''  body.black { background: var(--ink); color: var(--paper); }
''','''  /* On the black screen the two page colors trade places, so everything drawn in "ink" turns
     white by itself. The hues are stepped for the dark background. */
  body.black { --paper: #0c0c0c; --ink: #f8f7f3; --muted: #a3a29a;
               --fluent: #3987e5; --unfinished: #d95926; --fragment: #199e70; --response: #6f6e68; }
''')
rep('''  #stage { position: fixed; inset: 0; width: 100%; height: 100%; display: block; }
''','''  #stage, #wave { position: fixed; inset: 0; width: 100%; height: 100%; display: block; }
''')
rep('''  /* text laid over the stage */''','''  /* the waveform screen */
  .midline { stroke: var(--muted); stroke-width: 1; opacity: 0.55; }
  .wbar { cursor: pointer; transition: opacity 0.4s; }
  .wbar:focus { outline: none; }
  .wbar:focus-visible .hit { stroke: var(--ink); stroke-width: 1; stroke-dasharray: 3 3; }
  .wvalue, .topic, .wdetail text { font-family: var(--label-font); font-weight: 300; fill: var(--ink); }
  .wvalue { font-size: 10.5px; text-anchor: middle; font-variant-numeric: tabular-nums; }
  .topic { font-size: 11.5px; fill: var(--muted); pointer-events: none; }
  .wvalue, .topic, .wdetail, .midline { transition: opacity 0.4s; }
  .wdetail { opacity: 0; pointer-events: none; }
  .wdetail text { font-size: 12.5px; }
  .wdetail .pct { font-weight: 600; }
  .wdetail line { stroke: var(--muted); }
  #wave-world.has-focus .wbar:not(.is-focused) { opacity: 0.3; }
  #wave-world.has-focus .wbar.is-covered { opacity: 0; pointer-events: none; }
  #wave-world.has-focus .wdetail { opacity: 1; }
  #wave-world.zooming .wvalue, #wave-world.zooming .topic, #wave-world.zooming .wdetail, #wave-world.zooming .midline { opacity: 0 !important; }

  /* text laid over the stage */''')
rep('''  #next { position: fixed; inset: 0; display: grid; place-items: center; padding: 24px; text-align: center; cursor: pointer; color: var(--paper); }
  #next h2 { margin: 0 0 8px; font-size: 20px; }
  #next p { margin: 0 0 4px; opacity: 0.75; }''','''  #call { position: fixed; inset: 0; display: grid; place-items: center; padding: 24px; text-align: center; cursor: pointer; }
  #call h2 { margin: 0 0 8px; font-size: 20px; }
  #call p { margin: 0 0 4px; color: var(--muted); }''')

# ------------------------------------------------------------------ HTML
rep('''<svg id="stage" aria-label="Switchboard calls"><g id="world"></g></svg>
''','''<svg id="stage" aria-label="Switchboard calls"><g id="world"></g></svg>
<svg id="wave" aria-label="The calls under one umbrella" style="display:none"><g id="wave-world"></g></svg>
''')
i=s.index('<!-- Stands in for the waveform screen until it is built. -->'); j=s.index('<!-- Shown only when the page cannot fetch')
s=s[:i]+'''<!-- Stands in for the single-call screen until it is built. -->
<div id="call" hidden>
  <div>
    <h2 id="call-title" class="header"></h2>
    <p id="call-meta"></p>
    <p>The call itself, utterance by utterance, goes here next.</p>
    <p>Click anywhere to go back.</p>
  </div>
</div>

'''+s[j:]

# ------------------------------------------------------------------ settings
rep('''// ===========================================================================
// 1. LOAD''','''// Topic labels in the corpus are in capitals and a few are cut short. The names listed
// here are spelled out by hand; every other topic is simply put in sentence case.
const topicNames = {
  "AIDS": "AIDS", "TV PROGRAMS": "TV programs", "LATIN AMERICA": "Latin America", "MIDDLE EAST": "Middle East",
  "SOVIET UNION": "Soviet Union", "VIETNAM WAR": "Vietnam War", "WEATHER CLIMATE": "Weather and climate",
  "RECIPES/FOOD/COOKING": "Recipes, food and cooking", "PUERTO RICAN STTEHD": "Puerto Rican statehood",
  "SVGS & LOAN BAILOUT": "Savings & loan bailout", "UNIVERSAL HEALTH INS": "Universal health insurance",
  "UNIVERSAL PBLIC SERV": "Universal public service"
};
const topicName = topic => topicNames[topic] ?? topic[0] + topic.slice(1).toLowerCase();

// ===========================================================================
// 1. LOAD''')

# ------------------------------------------------------------------ shared variables
rep('''let data;                  // ten rows, one per umbrella''','''let calls;                 // one row per call (the 650 with sentence types)
let data;                  // ten rows, one per umbrella''')
rep('''let state = "opening";     // opening -> umbrellas -> focus -> black''','''let state = "opening";     // opening -> umbrellas -> focus -> wave -> wave-focus -> call''')

# ------------------------------------------------------------------ prepare
rep('''  const calls = rows.filter(row => row.has_parse === 1);
''','''  calls = rows.filter(row => row.has_parse === 1);
''')
rep('''  calls.forEach(call => { call.umbrella = umbrellaOf.get(call.topic) ?? "Other"; });
''','''  calls.forEach(call => {
    call.umbrella = umbrellaOf.get(call.topic) ?? "Other";
    call.total = d3.sum(keys, key => call[key]);                     // words that sit in a typed sentence
    call.kinds = kinds.map(kind => 100 * kind.count(call) / call.words);
  });
''')
rep('''  document.querySelector("#next").addEventListener("click", leaveBlack);
''','''  waveSvg.on("click", goBack);
  document.querySelector("#call").addEventListener("click", leaveCall);
''')

# ------------------------------------------------------------------ build
rep('''function build() {
  world.interrupt("fly");
  setHudLine();''','''function build() {
  if (state === "wave" || state === "wave-focus" || state === "call") {   // the umbrella screen is hidden: redraw the waveform
    stageStale = true;                                               // and rebuild the umbrellas when we return to them
    return buildWave(false);
  }
  stageStale = false;
  world.interrupt("fly");
  setHudLine();''')
rep('''let ringTimer = null;
''','''let ringTimer = null;
let stageStale = false;    // true if the window was resized while the umbrella screen was hidden
''')
rep('''  hud.classList.toggle("faded", opening || state === "black");''','''  hud.classList.toggle("faded", opening);''')

# ------------------------------------------------------------------ zoom to black and back
i=s.index('function zoomToBlack(d) {'); j=s.index('function toUmbrellas(duration) {')
s=s[:i]+'''function zoomToBlack(d) {
  busy = true;
  const s = segmentsOf(d)[inkType];                                  // the ink segment, in the middle of the bar
  const inkHeight = s.y1 - s.y0;
  world.classed("zooming", true);
  hud.classList.add("faded");
  // Aim at the middle of the segment and zoom until it covers the whole screen.
  const target = [L.x(d.umbrella), L.base + s.mid, Math.min(L.barWidth, inkHeight * W / H) * 0.8];
  flyTo(target, 1300).on("end", () => enterWave(d));
}

function goBack() {
  if (busy) return;
  if (state === "focus") toUmbrellas(750);
  else if (state === "wave") (zoomT.k > 1.02 ? resetWaveZoom(600) : leaveWave());
  else if (state === "wave-focus") unfocusCall();
  else if (state === "call") leaveCall();
}

'''+s[j:]

# ------------------------------------------------------------------ hud text
i=s.index('function setHudLine() {'); j=s.index('function debounce(fn, wait) {')
s=s[:i]+'''// The heading and the sentence under it, for the current state.
const dayFormat = d3.utcFormat("%-d %B %Y");
const describeCall = call =>
  `${topicName(call.topic)} \\u00b7 ${dayFormat(call.date)} \\u00b7 ${fmt(call.words)} words, ${rate1(d3.sum(call.kinds))} of every 100 disfluent.`;

function setHudLine(hovered) {
  const line = document.querySelector("#hud-line");
  const onWave = state === "wave" || state === "wave-focus" || state === "call";
  hud.querySelector("h1").textContent = onWave ? focused.umbrella : "The average call, by topic";
  if (state === "focus" && focused) {
    line.textContent = `${focused.umbrella}: ${focused.calls} calls on ${focused.topics} topics, ${fmt(focused.total)} words in the average call. ` +
      "Click the bar again to open its calls, or click anywhere else to go back.";
  } else if (state === "wave-focus" && waveFocused) {
    line.textContent = describeCall(waveFocused) + " Click the bar again to open the call, or click anywhere else to go back.";
  } else if (onWave) {
    line.textContent = hovered ? describeCall(hovered)
      : `${focused.calls} calls on ${focused.topics} topics. Each bar is one call: complete sentences rise above the line, everything else hangs below it. ` +
        "Scroll to widen, click a call to look closer, or click empty space to go back.";
  } else {
    line.textContent = "Bar height is the average number of words in a call. Only the blue part at the foot is spoken in complete, fluent sentences. Click a bar to look closer.";
  }
}

// ===========================================================================
// 9. THE WAVEFORM
// Every call under one umbrella, on a black page. Topics run left to right in
// alphabetical order. Inside a topic the calls are arranged short, long, short,
// so each topic makes one hump and the row looks like a recording of speech.
// A call's bar straddles a midline: its complete sentences rise above the line
// (those with a disfluency in white next to the line, the fluent ones in blue
// at the tip) and the three kinds that are not sentences hang below it.
// ===========================================================================
const waveSvg = d3.select("#wave"), waveWorld = d3.select("#wave-world");
const GAP = 2.4;                 // empty slots before each topic, where its name goes
const above = [1, 0];            // types drawn above the midline, nearest the line first
const below = [2, 3, 4];         // types drawn below it, nearest the line first
let WV = null;                   // the waveform on screen: its calls, topics, scales and zoom
let zoomT = d3.zoomIdentity;     // how far the row is stretched sideways (k) and shifted (x)
let waveFocused = null;          // the call in focus

// Put one umbrella's calls in order and give each a slot number along the row.
function prepareWave(d) {
  const groups = d3.groups(calls.filter(call => call.umbrella === d.umbrella), call => call.topic)
    .sort((a, b) => d3.ascending(topicName(a[0]), topicName(b[0])));
  const order = [], topics = [];
  let slot = 0;
  for (const [topic, group] of groups) {
    slot += GAP;
    topics.push({ name: topicName(topic), slot, count: group.length });
    for (const call of humpOrder(group)) { call.slot = slot++; order.push(call); }
  }
  return { calls: order, topics, slots: slot + 1 };
}

// Short, long, short: sort by length, then deal the calls alternately to the left
// and right ends, so the longest land in the middle.
function humpOrder(group) {
  const left = [], right = [];
  d3.sort(group, call => call.total).forEach((call, i) => (i % 2 ? right.unshift(call) : left.push(call)));
  return left.concat(right);
}

// The five rectangles of one call, in pixels measured from the midline (up is negative).
function waveSegments(call) {
  const out = [];
  let reach = 0;
  for (const type of above) {
    const height = call[keys[type]] * WV.perWord;
    out.push({ type, share: call[keys[type]] / call.total, y: -(reach + height), height: Math.max(0.5, height - 1), mid: -(reach + height / 2) });
    reach += height;
  }
  reach = 0;
  for (const type of below) {
    const height = call[keys[type]] * WV.perWord;
    out.push({ type, share: call[keys[type]] / call.total, y: reach + 1, height: Math.max(0.5, height - 1), mid: reach + height / 2 });
    reach += height;
  }
  return out;
}

// The umbrella's black segment has filled the screen: swap the page to black and bring up its calls.
function enterWave(d) {
  state = "wave";
  document.body.classList.add("black");
  svg.style("visibility", "hidden");
  waveSvg.style("display", null);
  WV = prepareWave(d);
  buildWave(true);
  hud.classList.remove("faded");
}

// Draw the waveform for the current window size. "grow" plays the bars rising out of the midline.
function buildWave(grow) {
  if (state !== "wave") { state = "wave"; document.querySelector("#call").hidden = true;      // a resize drops any focus
                          document.body.classList.add("black"); waveSvg.style("display", null); hud.classList.remove("faded"); }
  waveFocused = null;
  zoomT = d3.zoomIdentity;
  setHudLine();                                                      // set the heading text first: the layout measures it
  W = window.innerWidth;
  H = window.innerHeight;

  // One scale for height, shared by every call: words -> pixels. The midline sits where
  // the tallest upper half and the deepest lower half both fit.
  const side = clamp(W * 0.05, 12, 70);
  const top = hud.offsetHeight + 22 + 34, bottom = H - 30;
  const tallest = d3.max(WV.calls, call => d3.sum(above, type => call[keys[type]]));
  const deepest = d3.max(WV.calls, call => d3.sum(below, type => call[keys[type]]));
  WV.perWord = (bottom - top) / (tallest + deepest);
  WV.mid = top + tallest * WV.perWord;
  WV.x = d3.scaleLinear().domain([0, WV.slots]).range([side, W - side]);   // slot number -> pixels, before any zooming
  const slotWidth = WV.x(1) - WV.x(0);
  WV.focusZoom = Math.max(1, 56 / slotWidth);                        // stretch at which a slot is 56px wide

  waveWorld.interrupt("fly").attr("transform", null).attr("class", null);
  waveWorld.selectAll("*").remove();

  waveWorld.append("line").attr("class", "midline")
    .attr("x1", 0).attr("x2", W).attr("y1", WV.mid + 0.5).attr("y2", WV.mid + 0.5);

  waveWorld.append("g").selectAll("text").data(WV.topics).join("text")   // topic names, written up the gap before each hump
    .attr("class", "topic").text(topic => topic.name);

  const bars = waveWorld.append("g").selectAll("g").data(WV.calls).join("g")
    .attr("class", "wbar")
    .attr("tabindex", 0).attr("role", "button")
    .attr("aria-label", call => `${topicName(call.topic)}, ${dayFormat(call.date)}: ${fmt(call.words)} words`)
    .on("click", (event, call) => { event.stopPropagation(); pickCall(call); })
    .on("keydown", (event, call) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); pickCall(call); } })
    .on("mouseenter", (event, call) => { if (state === "wave") setHudLine(call); })
    .on("mouseleave", () => { if (state === "wave") setHudLine(); });

  bars.each(function (call) { call.segments = waveSegments(call); });
  bars.append("rect").attr("class", "hit")                           // an invisible click target, a little larger than the bar
    .attr("y", call => call.segments[above.length - 1].y - 14)
    .attr("height", call => d3.sum(call.segments, s => s.height + 1) + 28);
  bars.append("g").attr("class", "segs")                             // squashed flat onto the midline until the bars grow
    .attr("transform", grow ? "scale(1,0.001)" : "scale(1,1)")
    .selectAll("rect").data(call => call.segments).join("rect")
      .attr("class", s => "seg t" + s.type)
      .attr("y", s => s.y).attr("height", s => s.height);
  bars.append("text").attr("class", "wvalue")                        // the call's length in words, shown once bars are wide enough
    .attr("y", call => call.segments[above.length - 1].y - 6)
    .text(call => fmt(call.total));

  const detail = waveWorld.append("g").attr("class", "wdetail")      // share labels for the call in focus
    .selectAll("g").data(d3.range(keys.length)).join("g");
  detail.append("line");
  const text = detail.append("text").attr("dy", "0.35em");
  text.append("tspan").attr("class", "pct");
  text.append("tspan").attr("class", "what").attr("dx", "0.5em");

  // Scrolling, pinching and dragging stretch the row sideways. d3.zoom keeps track of the
  // gesture; only its sideways part is used, in drawWave().
  WV.zoom = d3.zoom()
    .scaleExtent([1, Math.max(1, 72 / slotWidth)])
    .extent([[0, 0], [W, H]]).translateExtent([[0, 0], [W, H]])
    .filter(event => !busy && (state === "wave" || state === "wave-focus") && (!event.ctrlKey || event.type === "wheel") && !event.button)
    .on("zoom", event => { zoomT = event.transform; drawWave(); });
  waveSvg.call(WV.zoom).on("dblclick.zoom", null);
  waveSvg.call(WV.zoom.transform, zoomT);                            // also draws everything once

  if (grow) {
    busy = true;
    const sweep = 500 / WV.calls.length;                             // the bars rise one after another, left to right
    waveWorld.selectAll(".segs").transition().duration(ms(650)).delay((call, i) => ms(120 + i * sweep))
      .ease(d3.easeCubicOut).attr("transform", "scale(1,1)");
    d3.timeout(() => { busy = false; }, ms(900));
  }
}

// Place everything sideways for the current stretch. Runs on every zoom step.
function drawWave() {
  const x = zoomT.rescaleX(WV.x);                                    // slot number -> pixels, stretched and shifted
  const slotWidth = x(1) - x(0), barWidth = clamp(slotWidth * 0.72, 1, 44);
  WV.barWidth = barWidth;
  waveWorld.selectAll(".wbar").attr("transform", call => `translate(${call.cx = x(call.slot + 0.5)},${WV.mid})`);
  waveWorld.selectAll(".wbar .seg").attr("x", -barWidth / 2).attr("width", barWidth);
  waveWorld.selectAll(".wbar .hit").attr("x", -slotWidth / 2).attr("width", slotWidth);
  waveWorld.selectAll(".wvalue").style("opacity", call => (slotWidth >= 34 || call === waveFocused ? 1 : 0));
  waveWorld.selectAll(".topic")                                      // names show once the gap is wide enough to hold them
    .attr("transform", topic => `translate(${x(topic.slot - GAP / 2) + 4},${WV.mid - 6}) rotate(-90)`)
    .style("opacity", GAP * slotWidth >= 15 ? 1 : 0);
  if (waveFocused) placeCallDetail();
}

// ===========================================================================
// 10. ONE CALL IN FOCUS, AND THE ZOOM TO WHITE
// First click on a call: focus (the row stretches, and the call's shares appear).
// Second click on it: zoom into its white segment until the page is white.
// ===========================================================================
function pickCall(call) {
  if (busy) return;
  if (state === "wave-focus" && waveFocused === call) zoomToWhite(call);
  else if (state === "wave" || state === "wave-focus") focusCall(call);
}

function focusCall(call) {
  state = "wave-focus";
  waveFocused = call;
  setHudLine();
  waveWorld.classed("has-focus", true);
  waveWorld.selectAll(".wbar").classed("is-focused", other => other === call);
  waveWorld.selectAll(".wdetail g").each(function (type, i) {         // fill in the share labels for this call
    const s = call.segments[i];
    d3.select(this).datum(s).select(".pct").text(pct(s.share));
    d3.select(this).select(".what").text(types[s.type].short);
  });
  // Stretch the row until a slot is 56px wide (or keep the current stretch if it is wider),
  // and slide it so the call sits left of centre, leaving room for its labels.
  const k = Math.max(zoomT.k, WV.focusZoom);
  const screenX = W < 700 ? 0.3 : 0.42;
  const target = d3.zoomIdentity.translate(screenX * W - k * WV.x(call.slot + 0.5), 0).scale(k);
  waveSvg.transition("stretch").duration(ms(700)).call(WV.zoom.transform, target);
}

// Share labels to the right of the call in focus, each tied to its segment by a short leader.
function placeCallDetail() {
  const call = waveFocused, edge = call.cx + WV.barWidth / 2;
  const groups = waveWorld.selectAll(".wdetail g");
  // Labels sit level with their segments, top to bottom; where two would collide the lower one is pushed down.
  const order = d3.sort(groups.data(), s => s.mid);
  let previous = -Infinity;
  for (const s of order) previous = s.at = Math.max(WV.mid + s.mid, previous + 17);
  groups.each(function (s) {
    d3.select(this).select("line").attr("x1", edge + 2).attr("y1", WV.mid + s.mid).attr("x2", edge + 9).attr("y2", s.at);
    d3.select(this).select("text").attr("x", edge + 13).attr("y", s.at);
  });
  // Calls that would sit under the labels step out while this one is in focus.
  const box = waveWorld.select(".wdetail").node().getBBox(), right = box.x + box.width + 10;
  waveWorld.selectAll(".wbar").classed("is-covered", other => other !== call && other.cx > call.cx && other.cx - WV.barWidth / 2 < right);
}

function unfocusCall() {
  state = "wave";
  waveFocused = null;
  waveWorld.classed("has-focus", false);
  waveWorld.selectAll(".is-focused").classed("is-focused", false);
  waveWorld.selectAll(".is-covered").classed("is-covered", false);
  setHudLine();
  resetWaveZoom(700);
}

function resetWaveZoom(duration) {
  waveSvg.transition("stretch").duration(ms(duration)).call(WV.zoom.transform, d3.zoomIdentity);
}

// Second click: the camera goes into the call's white segment until the page is white.
// This is the moment the single-call screen will load its data.
function zoomToWhite(call) {
  busy = true;
  waveSvg.interrupt("stretch");
  const s = call.segments[0];                                        // the white segment, just above the midline
  WV.dive = [call.cx, WV.mid + s.mid, Math.min(WV.barWidth, s.height * W / H) * 0.8];
  waveWorld.classed("zooming", true);
  hud.classList.add("faded");
  flyWave(homeView(), WV.dive, 1300).on("end", () => {
    state = "call";
    document.body.classList.remove("black");
    waveSvg.style("display", "none");
    document.querySelector("#call-title").textContent = topicName(call.topic);
    document.querySelector("#call-meta").textContent = `Call ${call.conversation_no} \\u00b7 ${dayFormat(call.date)} \\u00b7 ${fmt(call.words)} words`;
    document.querySelector("#call").hidden = false;
    busy = false;
  });
}

// The waveform's own camera, used only for the zoom to white and back.
function flyWave(from, to, duration) {
  const path = d3.interpolateZoom(from, to);
  return waveWorld.transition("fly").duration(ms(duration)).ease(d3.easeCubicInOut)
    .attrTween("transform", () => t => transformOf(path(t)));
}

function leaveCall() {
  if (busy || state !== "call") return;
  busy = true;
  document.querySelector("#call").hidden = true;
  document.body.classList.add("black");
  waveSvg.style("display", null);
  state = "wave-focus";
  flyWave(WV.dive, homeView(), 1100).on("end", () => {
    waveWorld.attr("transform", null).classed("zooming", false);
    hud.classList.remove("faded");
    busy = false;
  });
}

// Back to the umbrella screen: the page turns white again and the camera pulls out of the black segment.
function leaveWave() {
  waveSvg.style("display", "none");
  document.body.classList.remove("black");
  svg.style("visibility", null);
  if (stageStale) { state = "umbrellas"; focused = null; build(); }  // the window changed size meanwhile: redraw, no animation
  else toUmbrellas(1200);
}

'''+s[j:]
rep("\\u00b7", "·", 4)
open(p,'w').write(s)
print("patched")
