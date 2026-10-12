# Complete sentences are the exception: disfluency in the Switchboard corpus

An interactive D3 visualization of how people actually talk on the phone. It is built on
650 calls from the Switchboard corpus (telephone conversations between strangers, recorded in
1991 and 1992). The idea behind it: in real talk, the complete, fluent sentence is the exception.

You move through six screens, each one closer in:

1. **Opening.** A telephone receiver rings. Click it to answer.
2. **Umbrellas.** Ten bars, one per group of topics. Each bar is the average call, split into
   five sentence types by share of words.
3. **Umbrella focus.** One bar with its shares labelled, and a thin strip showing how many words
   per 100 are disfluent, split into six kinds ("uh", "um", "you know", repeats, editing terms,
   cut-off words).
4. **Waveform (black).** Every call under that umbrella as its own bar, grouped by topic. Fluent
   complete sentences rise above the line; everything else hangs below it.
5. **Call focus.** One call, with a typical line of talk for each sentence type in the callers'
   own words.
6. **Single call.** Every utterance in order: the caller on the upper strand, the answerer on the
   lower one. A coiled cord stands for the stretches where a speaker is waiting.

An **i** button in the top right corner opens a panel. It lists what comes from the corpus as
annotated, what was made for this piece by fixed rule (and the rules), and what was made by
judgment (the topic umbrellas).

## Run it

The page is plain HTML and JavaScript with the D3 library (v7.9.0, loaded from a CDN) and two
Google Fonts. No build step and no Python are needed to view it.

The page loads its data with `fetch`, and browsers block that for pages opened straight from
disk. So serve the `site` folder over HTTP, with any one of these:

```
cd site
python -m http.server 8000          # then open http://localhost:8000
npx serve .                         # Node
```

Or use the Live Server extension in VS Code on `site/index.html`.

An internet connection is needed for D3 and the fonts.

## What is in the repository

```
site/                  the visualization: everything needed to run it
  index.html           the page: HTML, CSS and the D3 script in one file
  conversations.csv    one row per call: topic, date, word counts by sentence type and by kind of disfluent word
  conversations/       one JSON file per call (650 files): its utterances and words, read on the last two screens
pipeline/              how the data files were made (Python, run once; not part of the page)
  extract_swda.py      reads the corpus and writes every data file, by fixed rules
  publish_site.py      copies the files the page reads into site/
  make_coding_sample.py  draws a blind, stratified sample of utterances for hand coding
  corpus/              put the corpus download here (not tracked)
  output/              the full extraction output lands here (not tracked)
process/               how the piece was made: notes, validation, prototypes, checks. See process/README.md
website-copy/          an untracked second copy of the site, for experiments (listed in .gitignore)
```

## Rebuild the data

You only need this to change the rules or regenerate the files. The script uses only the Python
standard library.

1. Get the corpus: the Switchboard Dialog Act Corpus as packaged by Christopher Potts
   (https://github.com/cgpotts/swda). Download the repository and put its `swda.zip` in
   `pipeline/corpus/`.
2. Extract:

   ```
   cd pipeline
   python extract_swda.py --input corpus/swda.zip --out output
   ```

   This writes `conversations.csv`, `utterances.csv`, `turns.csv`, `speakers.csv`,
   `sentence_units.csv`, `fluency_by_length.csv`, `summary.json`, `schema.json` and
   `conversations/<id>.json` for all 1,155 calls. The run is deterministic: running it again
   gives the same files, byte for byte. `schema.json` describes every column.
3. Copy what the page needs into `site/`:

   ```
   python publish_site.py --data output --site ../site
   ```

## The derived categories

The corpus supplies the words, the topics, the disfluency markup on words and a parse of each
sentence. Two things here are derived, not corpus codes:

- **Five sentence types:** complete and fluent; complete with a disfluency; unfinished;
  fragment; response token. `extract_swda.py` reads each sentence's Treebank parse (top label,
  unfinished marks), then applies three utterance-level rules: a run of nothing but linking words
  is a fragment; an abandoned fragment is unfinished; a complete sentence holding any disfluency is
  "with a disfluency". The full rules are in the page's info panel and in
  `process/docs/storyboard-spec.md`.
- **Six kinds of disfluent word:** repeated or reworded words (the reparandum of a repair),
  editing terms such as "I mean", cut-off words, "you know" as a discourse marker, "uh", and "um".
  All six rest on the corpus's own disfluency markup.

No utterance was labelled by hand or by an AI model. The grouping of the 64 topics into ten
umbrellas is the one judgment call: LLM-assisted analysis of what the topics have in common, then a
human review and refining pass.

**Validation status.** The sentence-type rules were revised after a 30-utterance hand-coding
pilot. A fresh sample of 300 utterances is drawn and waiting to be coded
(`process/validation/sample-2/`). Until that is done, treat the types as unvalidated.

## Credits and licence

- Data: the Switchboard corpus (Godfrey, Holliman and McDaniel, 1992), with the dialog act
  annotation of Jurafsky, Shriberg and Biasca (1997) and the Penn Treebank-3 parses, as packaged at
  https://github.com/cgpotts/swda. The files in `site/` contain transcript words from that corpus.
  Check the corpus licence in that repository before making this repository public.
- Design direction informed by the work of Kim Albrecht.
- Built by AC with Claude.
