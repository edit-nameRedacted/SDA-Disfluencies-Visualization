# Process files

These are the working files behind the visualization. The page doesn't need any of them to run.

```
docs/
  storyboard-spec.md     the design spec: constraints, colour rules, every screen, where each category
                         comes from, validation status, known limits
  codebook-v2.md         the hand-coding codebook for the second sample (a copy of the Claude Doc
                         "Sentence-Type Codebook", version 2)
  schema.json            column-by-column description of every file extract_swda.py writes
  summary.json           corpus-wide totals from the last extraction run
validation/
  sample-1/              first sample: 300 utterances, seed 19911103, coded under the original rules
    sentence_type_coding_sheet.xlsx   the blank coding sheet
    pilot_coded_first_30.xlsx         AC's pilot: the first 30 rows coded; led to the rule revision
    coding_sample.csv, coding_key.csv the sample as CSV, and its answer key
  sample-2/              second sample: 300 new utterances, seed 20261011, under the revised rules
    sentence_type_coding_sheet_2.xlsx the coding sheet (codes are typed; the Read me tab counts misspellings)
    coding_sample_2.csv, coding_key_2.csv
  build_coding_sheet.py  builds the .xlsx coding sheet from a coding_sample.csv (needs openpyxl)
prototypes/              earlier proof-of-concept pages (umbrella bars, barcodes, calls by topic)
                         and the scripts that fed them; superseded by site/index.html
build-history/
  extract_swda.v1.py     the extraction script before the rule revision of 12 October
  snapshots/             copies of the page taken before each major change, named for the change
  patches/               the scripts that applied some of those changes. They point at the old
                         working paths and are kept as a record, not to be re-run
checks/                  Playwright scripts that walked the page at several window sizes and took
                         screenshots. They expect a local server folder (../serve4) and d3 in
                         node_modules; adjust the paths to reuse them
analysis/                small one-off checks: verb_check2.py (how many parsed sentences of each
                         type contain a verb), plain_index.py and lookup.py (find an utterance's
                         script type from its words)
assets/
  Asset_1.svg            the receiver drawing (it is also inlined in the page)
  storyboard-sketch.jpg  the hand-drawn storyboard
```

## Blinding

The answer keys (`coding_key*.csv`) are in this folder. Whoever codes a sample shouldn't open its
key, or look the utterances up in the page, until they have finished.
