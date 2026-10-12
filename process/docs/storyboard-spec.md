# Switchboard disfluency visualization: storyboard spec

Settled design as of 11 October 2026, from AC's hand-drawn storyboard and the follow-up discussion. Guiding idea: the complete sentence is the exception in real talk.

## Constraints

- HTML, JavaScript and the D3 library only. No Python in the build or at run time.
- Read the existing extraction outputs and do not create derived copies: `conversations.csv`, `utterances.csv`, `turns.csv`, `speakers.csv`, `sentence_units.csv`, `fluency_by_length.csv`, `summary.json`, `schema.json`, plus the `conversations/` folder of per-call JSON.
- Scope is the 650 calls that have sentence types (`has_parse` = 1), recorded March 1991 to May 1992.
- The page must be served by a web server: a call's own file (`conversations/<id>.json`) loads when that call is put in focus on the waveform. Opened straight from disk, the page still runs but shows type names where the lines of talk would be.
- Every derived variable must come from a script or from fixed rules in the page, never from case-by-case inference by an AI model, so the result is rule-based and replicable (AC, 11 October).

## Categories and color

Five sentence types, counted by words (`stw_` columns), in stacking order from the foot of the umbrella bar:

| Type | Column | On white | On black |
|---|---|---|---|
| Complete sentence, fluent | `stw_complete_fluent` | blue | blue |
| Complete sentence, with a disfluency | `stw_complete_disfluent` | black | white |
| Unfinished clause | `stw_unfinished` | orange | orange |
| Fragment (no clause) | `stw_fragment` | green | green |
| Response token | `stw_response_token` | grey | grey |

Color rule: "complete sentence, with a disfluency" is drawn in the opposite of the background, and it is the segment the camera zooms into to invert the page. Reasons, from AC: the black segment sits in the middle of the umbrella bar, so the zoom does not have to pan down, and the disfluency strip can line up beside it. (Before 11 October, fluent was the ink segment.) In the page, the two page colors are CSS variables that trade places on the black screen; the hues have their own steps there.

Type: headers are IBM Plex Sans 600 in tracked capitals (the "Switchboard" style); labels on the bars are Manrope Light.

## Where the categories come from

**The five sentence types are ours, not corpus codes.** The corpus supplies the ingredients; `extract_swda.py` combines them in two steps. Rules revised on 12 October after AC's hand-coding pilot.

Step 1, per parsed sentence (`classify_tree`), from the Treebank-3 parse:

| First type | Rule | Corpus annotation it rests on |
|---|---|---|
| Complete | A clause not marked unfinished; also a clause opening with "because" that has a full clause inside | Treebank root S, SQ, SBARQ or SINV; root SBAR + "because" + an S node |
| Unfinished clause | A clause marked unfinished | Treebank `-UNF` (outside any `EDITED` part) or `N_S` |
| Response token | An interjection | Treebank root INTJ |
| Fragment | Any other root: noun phrase, prepositional phrase, if/when/that clause alone, verb phrase with no subject | Treebank root label |

An utterance takes the first type of its largest parsed sentence (column `parse_type`). Step 2, per utterance (`refine_sentence_type`), in order (column `sentence_type`):

1. Nothing but linking words (and, an, but, so, or, nor, either, plus, then, because, 'cause), with or without uh or um: **fragment**. Matched on the words, so a lone "so" counts whether the corpus marks it `{C}` or `{D}`.
2. A fragment the corpus marks as abandoned (`-/`, or a dialog act starting `%`): **unfinished clause**.
3. A complete sentence holding any repair or any corpus-marked disfluent word (the six kinds below): **complete, with a disfluency**; otherwise **complete, fluent**.

Check on "no verb = fragment" (AC's rule): 99.9% of parsed sentences typed complete contain a verb (the rest are mis-tagged words). The converse does not hold: 34% of parse-level fragments contain a verb, nearly all inside a subordinate or relative part ("somebody that knows their way around"), in an if/when clause alone, or in a verb phrase with its subject dropped ("Got a bunch of groves in it"). Commands are parsed as clauses and count as complete.

In any write-up, describe the types as derived from the Treebank-3 parses and disfluency annotation of Switchboard, not as tags in the dataset.

**The six kinds of disfluent word are corpus codes**, from the Meteer disfluency markup in the transcripts, renamed in plain words. "You know" is ours to pick out: of the corpus's discourse markers `{D ...}`, only the two words "you know" are counted; "well", "like" and the rest are not.

| Label in the piece | Corpus code | Column |
|---|---|---|
| Repeated or reworded words | Reparandum: the words before the `+` in `[ ... + ... ]` | `w_rp` |
| Editing terms ("I mean") | `{E ...}` | `w_et` |
| Cut-off words | Word fragment outside a repair | `w_fr` |
| "You know" | `{D you know}` | `w_yk` |
| "Uh" | `{F uh}` | `uh` |
| "Um" | `{F um}` | `um` |

"Repeated or reworded" was first labelled "replaced". Read from the markup of 25,061 un-nested repairs: 57% are word-for-word repetitions ("about, uh, about"), 37% change the wording ("we were, I was"), 6% are dropped with nothing after. The files have no column for this split.

**How each thing was produced (provenance check, 11 October):**

- Sentence types and word classes: `extract_swda.py`, standard-library Python, pattern matching only, no model calls and no randomness. Re-running it on `swda.zip` reproduced all 1,163 output files byte for byte (checked for v1 on 11 October and for the revised script on 12 October).
- Everything computed in the page (averages, rates, hump order, the choice of lines of talk): fixed rules in the page's script.
- No utterance, call or topic was labelled by an AI model.
- Two things are judgment, not rule: the grouping of the 64 topics under ten umbrellas and the spelled-out topic names (a small hand-written table). For the umbrellas, the info panel uses AC's wording: "LLM assisted semantic analysis of topic commonalities determined umbrella groupings with a human review and refining pass." The grouping is stored as a fixed table in the page. The rules in the script were also written by Claude, but they are explicit and readable in the code.

## Validating the sentence types (in progress)

The five types have not yet been checked against a full human reading. A 30-row pilot led to revised rules; a second sample is ready for coding.

- **Sample:** 300 utterances, 60 from each type the script assigned, drawn from the 650 calls by `make_coding_sample.py` with a fixed seed (19911103) and shuffled. Re-running the script reproduces the sample exactly.
- **What the coder sees:** `sentence_type_coding_sheet.xlsx`. Each row is one utterance in plain words (no punctuation, no markup), with the two utterances before and the one after, and a dropdown for the code. The script's type is not in the sheet.
- **Answer key:** `coding_key.csv`, to stay closed until coding is done.
- **Codebook:** the Claude Doc "Sentence-Type Codebook": the five codes, four decision steps, what counts as a disfluency, and a table of hard cases.
- **Pilot (first 30 rows, 12 October):** AC's code matched the script's type on 22 of 30. The eight mismatches, with how much of the 650 calls each pattern touches:
  - An abandoned start typed as a fragment ("what i-"). A script weakness: 22% of fragments (0.9% of words) carry the corpus's own abandoned mark and would sit better under unfinished.
  - A subordinate clause that continues the speaker's previous sentence ("because you never know"): AC complete, script fragment. 17% of fragments (1.4% of words) open with a subordinating word.
  - "You know" and "I mean" read as a disfluency: AC yes, script no. The script is also inconsistent here: the disfluency strip counts editing terms as disfluent words, but a sentence whose only mark is an editing term is typed fluent. 3.1% of complete-fluent utterances hold a word the corpus marks disfluent. Counting those would take the fluent share of words from 38.0% to 36.2%; counting "you know" and "I mean" as well, to 32.2%.
  - Boundaries AC coded both ways: a lone "and" (unfinished) against a lone "but" (fragment); "and it's a delicious thing" (complete) against "and he's suave" (fragment); and a verbless answer coded complete. A third of complete sentences (31.5% of words) open with and, but, so or or, so the rule for those matters most.
  - Underneath: the script measures whether an utterance is a complete clause in the parse. A reader may instead judge whether it is a complete contribution to the conversation. The piece has to say which it means.
  - The 30 pilot rows do not count toward the final agreement.
- **AC's decisions after the pilot (12 October), now applied.** The revised script is promoted, the data re-run, and the preview republished.
  - A lone and, so or but is a fragment (step 2, rule 1). First staged as "words the corpus marks `{C}`"; that missed a lone "So" marked `{D}` (about 200 utterances typed response token) and "and then" (typed unfinished), so the rule now matches the words themselves.
  - "You know" and "I mean" are disfluencies. "You know" is a new disfluent word class (`yk`, column `w_yk`), drawn in teal (#0e9aa7 light, #3cc6c9 on dark) between cut-off words and "uh"; "I mean" was already counted as an editing term.
  - A clause opening with but or because is judged on the rest. And/but/so clauses were already parsed as clauses; a stand-alone because-clause with a full clause inside now counts too. If- and when-clauses alone stay fragments.
  - No verb = fragment. Already true of the parse-based rule (see the check above).
  - Added by Claude, agreed in principle: a fragment the corpus marks as abandoned is an unfinished clause.
  - Effect on the share of words, v1 to now: complete fluent 38.0% to 32.6%; complete with a disfluency 43.7% to 50.0%; unfinished 8.9% to 9.5%; fragment 5.1% to 3.7%; response token 4.3%. Disfluent words rise from 8.5 to 10.7 per 100 ("you know" alone is 2.2).
  - Not decided by AC, codebook follows the script: a verb with its subject dropped ("Got a bunch of groves in it") is a fragment.
- **Second sample (12 October):** 300 new utterances, 60 per revised type, seed 20261011, none from the first sample (`make_coding_sample.py --exclude coding_key.csv`). Coder sheet `sentence_type_coding_sheet_2.xlsx`; key `coding_key_2.csv`. Codes are typed (Complete fluent, Complete disfluent, Unfinished, Fragment, Response token, Cant tell; no commas) because the first sheet's dropdown did not show in AC's app; the dropdown is still there for apps that support it, and the Read me sheet counts any misspelled code. The codebook (Claude Doc) is rewritten as version 2 with five decision steps.
- **When the sheet comes back:** agreement per type, overall agreement and Cohen's kappa weighted back to how common each type is, and a table of the disagreements by pair of codes. With 60 per type, a type's agreement is known to within roughly 12 percentage points. A second coder would also test the codebook itself.

## Screens

1. **Opening (white).** An old telephone receiver lies on its side and wiggles occasionally, as if ringing. Its label gives the dataset name, 650 calls, and the date range. Its coiled cord stays attached and runs off the right edge.
2. **Umbrellas (white).** Clicking the receiver zooms in; it settles at the bottom of the screen and the ten umbrella bars rise from it on cords. Bars are in alphabetical order, with names written vertically beside them. Bar height is average words per call; segments are the five types.
3. **Focus, then zoom.** One click focuses a bar. A click anywhere else returns to the umbrella screen. A second click on the focused bar zooms into its black segment until the screen is black. Focus reveals the share of each sentence type and the disfluency strip (below).
4. **Waveform (black).** All calls under that umbrella, grouped by topic in alphabetical order. Within each topic, calls are sorted short, long, short, so each topic forms its own hump and the screen looks like a speech recording. Each call's bar straddles a midline. Above the line, in blue, are its fluent, complete sentences. Everything else hangs below: complete sentences with a disfluency in white next to the line, then unfinished clauses, fragments and response tokens. (AC's choice: this shows fluent speech against everything disfluent or incomplete.) Topic names are written up the gap in front of each hump. The bars rise out of the midline, left to right, when the screen opens.
   - Scrolling, pinching or dragging stretches the row sideways; each call's word count appears above it once bars are wide enough.
   - Pointing at a call shows its topic, date, length and disfluent words per 100 in the heading.
5. **Focus, then zoom.** One click focuses a call: the row stretches, the other calls dim, and lines of talk from that call appear beside it (below). Clicking a different call moves the focus to it. A click on empty space goes back one step. A second click on the focused call zooms into its white segment until the screen is white.
6. **One call (white).** The call is laid out like lines of text: words run left to right and wrap onto as many rows as the call needs, sized so the whole call fits the screen. Each row has two strands, caller A above and answerer B below. On a strand, a bar is an utterance, as long as its words and colored by type, in spoken order. Where a strand turns to coiled phone cord, that speaker is waiting: the cord is as long as the words the other person says in the meantime. The wording must say waiting, not silence, because the corpus has no timing. Bars and cords appear in the order spoken when the screen opens.
   - Pointing at a bar (or tapping it) opens a dark bubble with the speaker, the sentence type, the dialog act in plain words, and the whole utterance with its disfluent words colored by kind. The other bars dim.
   - An utterance the other speaker cuts into shows as two or more bars; pointing at one lights them all.
   - A click on empty space, or Escape, goes back to the waveform with the same call in focus.
   - If the call's file cannot be read, the screen says so instead of drawing.
   - A small "Transcript ends" mark sits after the last bar. Most transcripts stop mid-conversation: only 172 of the 650 calls have a closing among their last eight utterances, and 359 are listed at exactly 5 minutes, of which 29 have one. So a call that ends on "and" (Pets, call 3252) is the corpus's transcript ending, not the page running out of room.

On every screen:

- **Click cue.** A bar in focus gets a thin bracket on its left, as tall as the bar, with thin capitals written across the bracket: "Click to see all topics" on an umbrella, "Click to open the call" on a call. (A cue written on the black segment itself was tried and dropped: it distracted from the disfluent words.) On a narrow screen the umbrella's name steps out while the bracket is shown.
- **Info button.** An "i" in the top right opens a panel, "What is measured, and what was made". It separates what comes from the corpus as annotated, what was made for the piece by rule, and what was made by judgment. Each item is an accordion that opens to the rule behind it. The umbrella list in the panel is written from the same table the bars use.

## What each zoom level reveals

- **Umbrella focus (built): the disfluency strip.** A thin column as tall as the bar, standing for every word in the umbrella's calls. Its filled block is the words that are themselves disfluent, at the same scale as the bar, centred beside the black segment and split into the six kinds. Rates are per 100 words spoken. Across the 650 calls the total is about 10.7 per 100; by umbrella it runs from 9.4 (Home & hobbies) to 12.4 (Politics & world affairs).
- **Call focus on the waveform (built): lines of talk.** Beside each segment of the focused call, its share of the call's words and one line in the callers' own words, with disfluent words colored by kind. The labels this replaced only repeated the key. How a line is chosen:
  - Response tokens: the wording used most often in that call, with its count ("Uh-huh", 5 of 18).
  - The other four types: the utterance whose word count is closest to the median for that type in that call, so it is a typical example by length. Ties go to the earlier utterance.
  - Utterances split across turns by the other speaker are joined back together first.
- **Single call (built): the order of talk, and every utterance in full.** Who speaks when and for how long, who waits, where utterances break off and who speaks next; on pointing, each utterance's own words and its dialog act. The cause of each "complete, with a disfluency" utterance (repair, filled pause, or both: 47%, 26% and 24% corpus-wide) shows in the colored words.
- **Corpus-wide figures behind what the single call lets you see**, per utterance:
  - Response tokens: the word itself (yeah 34%, uh-huh 24%, right 9%, okay 4%) and its dialog act (backchannel 62%, agreement 14%, yes or no answer 8%).
  - Unfinished clauses: how many words were said before stopping (median 4; 47% stop within three words), whether a disfluency is inside (46%), and who speaks next (same speaker 56%, other speaker 42%).
  - Fragments: dialog act (statement or opinion 48%, question 9%, echo or completion of the other speaker 7%) and length (median 4 words).
- **Not in the files:** a per-word repair subtype (repetition, rewording, restart) and the grammatical kind of a fragment (noun phrase, prepositional phrase). Either would need a re-run of the extraction.

## Topic umbrellas

Ten umbrellas over the 64 topics that have parsed calls. The grouping is editorial and lives in one JavaScript table in the page. A second small table spells out the topic names the corpus abbreviates. AIDS moved from Education & society to Politics & world affairs on 11 October (AC's call).

| Umbrella | Calls | Topics |
|---|---|---|
| Education & society | 53 | Choosing a college, Public education, Social change, Women's roles |
| Entertainment & media | 76 | Books and literature, Magazines, Movies, Music, News media, TV programs |
| Family | 56 | Care of the elderly, Child care, Family life, Family reunions |
| Home & hobbies | 93 | Auto repairs, Gardening, Hobbies and crafts, Home repairs, Houses, Painting, Pets, Recipes/food/cooking, Woodworking |
| Law & justice | 93 | Capital punishment, Crime, Drug testing, Gun control, Right to privacy, Trial by jury |
| Money & work | 65 | Buying a car, Consumer goods, Credit card use, Family finance, Job benefits |
| Politics & world affairs | 69 | AIDS, Elections and voting, Ethics in government, Federal budget, Immigration, Latin America, Middle East, Politics, Soviet Union, Taxes, Universal health insurance, Universal public service, Vietnam War |
| Science & environment | 53 | Air pollution, Computers, Metric system, Recycling, Space flight and exploration |
| Small talk | 37 | Clothing and dress, Restaurants, Vacation spots, Weather and climate |
| Sports & outdoors | 55 | Baseball, Basketball, Boating and sailing, Camping, Exercise and fitness, Fishing, Football, Golf |

## Known limits

- 17 of the 64 topics have fewer than five calls, so a topic's hump can rest on two or three conversations.
- Calls within a topic vary widely (Trial by jury runs from 7% to 42% fluent words), so topic-level readings are tendencies.
- The topic is the prompt the callers were assigned, not a coding of what they said.
- The five sentence types are derived by our own rules. A pilot of 30 hand-coded rows led to revised rules; the revised rules await the second hand-coded sample.
- The disfluency strip counts the whole call. 79% of disfluent words are spoken inside complete sentences with a disfluency (the black segment it sits beside); 16% are in unfinished clauses, 4% in fragments, 1% in response tokens.
- On the waveform, bar heights share one scale within an umbrella, not across umbrellas.
- A line of talk is typical in length only. It says nothing about what the callers typically talked about.
- On the single call, position and length are counted in words, not time. Overlapping speech cannot be shown: the transcript puts everything in one sequence.
- Dialog-act names in the bubble are shortened versions of the corpus's 42 SWBD-DAMSL classes (a hand-written name table in the page).

## Built so far

- `extract_swda.py`: the extraction that produced the data files (run once; not part of the D3 build).
- `switchboard_viz.html`: the build file. One HTML page in plain D3 reading `conversations.csv` and, on call focus, `conversations/<id>.json`. All six screens work, with the click cues and the info panel.
- `umbrella_bars_d3.html`: a standalone tutorial version of the umbrella bar chart.
- Published pages: a live preview of the build ("Switchboard Calls"), and two earlier proof-of-concept pages that are not part of the final build. A published page holds at most 511 files, so the preview carries call files for eight umbrellas; Law & justice and Science & environment show type names in place of lines there. The local build has no such limit.

## Next

Nothing from the storyboard is unbuilt. Open items: the hand-coding check of the revised sentence types (second sample and codebook v2 delivered, coding with AC); and the 3D receiver from Blender, if it replaces the drawn one on the opening screen.
