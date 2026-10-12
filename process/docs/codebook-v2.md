# Sentence-Type Codebook

Oct 11, 2026 · AC

Code each of the 300 utterances in the second coding sheet as one of five sentence types, from its words alone. The result tests whether the script's revised rules match a human reading.

**Version 2.** Revised after a 30-row pilot on the first sample. What changed: a lone linking word is now a Fragment, not Unfinished; "you know" and "I mean" now count as disfluencies; a clause opening with "because" is judged on what follows it; an utterance with no verb is always a Fragment. The pilot rows do not count towards the result.

## The task

The coding sheet holds 300 utterances drawn at random from the 650 calls, 60 from each type the script assigned, in shuffled order. None of them was in the first sample. Each row shows one utterance in plain words, with the two utterances before it and the one after it for context.

- Code the line in the **Utterance** column only. The context lines are there to help you understand it.
- Type one of the six codes in the **Code** column exactly as written: Complete fluent, Complete disfluent, Unfinished, Fragment, Response token, Cant tell. If your app shows a dropdown, you can pick from it instead.
- Use **Cant tell** when the words do not let you decide, and say why in **Notes**.
- The words have no punctuation and no disfluency markup, so that you judge from what was said and not from the annotators' marks.
- Keep the answer key (`coding_key_2.csv`) closed until you have finished, and do not look the utterances up in the piece. Either would show you the script's answer.

An utterance is one dialog-act unit from the corpus. Where the other speaker cut in halfway, the pieces have been joined back into one line.

## The five codes

Every utterance gets exactly one of these. The examples are real lines from the corpus, and none of the longer ones is in the second sample.

| Code | What it is | Examples |
| --- | --- | --- |
| **Complete fluent** | A whole sentence: a subject with its verb, finished, with no disfluency in it. Questions and commands count. An opening "and", "but", "so" or "because" does not stop it being whole. | "Well what are your hobbies" · "and they left the dog in the car" · "Oh is he" · "Because I look at him" |
| **Complete disfluent** | A whole sentence, finished, that contains at least one disfluency (see the list below). | "I uh was just in a supermarket" · "Well I I kind of have hobby fads I guess" · "you know they weren't a state" · "I mean the system isn't perfect" |
| **Unfinished** | Something the speaker started and did not finish. It breaks off, trails away, or stops partway through a word. | "and then you um" · "Um our our friend has a" · "how wha-" · "that's exac-" |
| **Fragment** | No main clause. There is no verb at all; or there is a verb but its subject is left out; or it is a clause opening with "if", "when" or "that" standing alone; or it is nothing but linking words. | "In New Mexico" · "A hamster" · "just regular water" · "Got a bunch of groves in it" · "if it's not raining" · "When it was really just starting" · "and uh" |
| **Response token** | Nothing but a reaction or answer word: an interjection with no content of its own. | "Yeah" · "Uh-huh" · "Right" · "Oh yeah" · "Um yeah" |

## Decision steps

Ask these five questions in order and stop at the first one that gives a code. If the utterance holds more than one sentence, judge the longest one.

1. **Is it nothing but a reaction or answer word?** Yeah, uh-huh, right, okay, oh, no, sure, really, wow, with nothing else. A lone "uh" or "um" counts here too. Code **Response token**.
2. **Is it nothing but linking words?** And, but, so, or, then, because, with or without an "uh" or "um": "so", "and uh", "but um", "and then". Code **Fragment**.
3. **Did the speaker break off or trail away before finishing what they started?** A sentence stopped partway ("Um our our friend has a"), a word cut off ("how wha-"), a start that goes nowhere ("and then you um"). Code **Unfinished**.
4. **Is there a main clause?** That is, a subject with its verb that could stand as a sentence. When you judge this, ignore an opening "and", "but", "so" or "because": "because there is lots to see" has one. If there is none, code **Fragment**. No verb means no main clause, even when the words answer a question perfectly well ("A hamster").
5. **Does the sentence contain a disfluency?** If yes, code **Complete disfluent**. If no, code **Complete fluent**.

## What counts as a disfluency

Five things make a finished sentence "disfluent".

| Counts | Looks like |
| --- | --- |
| A filled pause | "uh" or "um", anywhere in the sentence, including its first word |
| A repeated or reworded stretch | "I I kind of", "it it was called", "we were I was", "to uh to Carney" |
| A cut-off word | a word broken off before its end, written with a hyphen: "th-", "goin-" |
| "You know" as a filler | "you know they weren't a state", "and here we are you know" |
| "I mean" as a filler or correction | "I mean the system isn't perfect", "we went I mean they went" |

These do not count, on their own:

- Words that open or link a sentence: well, so, and, but, oh, now.
- "You know" or "I mean" used in their ordinary sense, as part of the sentence: "you know the one", "I mean it".
- Other filler words: like, kind of, I guess.
- Laughter and other noises, which are left out of the text anyway.
- Informal or ungrammatical wording that the speaker did not correct.

## Hard cases

These are the calls most likely to split two coders. Use the code given, so that disagreements with the script come from the script and not from the codebook.

| Case | Example | Code |
| --- | --- | --- |
| A lone linking word, with or without uh or um | "and" · "so" · "but uh" · "and then" | Fragment |
| A clause opening with because, and, but or so | "because there is lots to see" · "and they left the dog in the car" | Judge the rest as a sentence: here, Complete fluent |
| A clause opening with if, when or that, standing alone | "if it's not raining" · "When it was really just starting" | Fragment |
| A verb with its subject left out | "Got a bunch of groves in it" | Fragment |
| A command | "Put it that way" | Complete (a command has no spoken subject, but counts as a sentence) |
| A short phrase that answers a question | "In New Mexico" · "A hamster" · "Pretty good" | Fragment: no verb |
| A short answer with a subject and verb | "I do" · "It is" · "I see" | Complete (fluent, unless it has a disfluency) |
| A start abandoned before any verb | "how wha-" · "and then you um" | Unfinished |
| A reaction word followed by a sentence | "Yeah I think so" | Judge the sentence, not the reaction word |
| A reaction word plus uh or um only | "Oh yeah" · "Um yeah" | Response token |
| A sentence that ends on "or", "and" or "so" | "we drove up there and" · "Salt water or" | If what comes before is a finished main clause, complete; if not, by steps 3 and 4 |
| A sentence finished only after the other speaker cut in | pieces joined in one line | Judge the joined line as one sentence |
| A word repeated for emphasis | "very very good" · "no no no" | Not a disfluency |
| Two sentences in one utterance | "That's correct and I was on a tour" | Judge the longest sentence |
| Words you cannot make sense of | | Cant tell, with a note |

## After coding

Send back the coding sheet with the Code column filled in. The "Something else typed" line on the Read me sheet should read 0; if not, a code is misspelled. The codes are then set against the script's types in `coding_key_2.csv`.

- **Per type:** of the 60 utterances the script gave each type, how many you gave the same code.
- **Overall:** agreement and Cohen's kappa, weighted back to how common each type is in the 650 calls, because the sample holds equal numbers of each and the calls do not.
- **Where they differ:** a table of every disagreement, grouped by the pair of codes involved, to show which rule is responsible.

With 60 utterances per type, a type's agreement rate is known to within roughly 12 percentage points either way. One coder shows whether the script matches a human reading. A second coder on the same sheet would also show whether this codebook is clear enough for two people to agree.

The sample can be drawn again exactly: `make_coding_sample.py` uses a fixed seed (20261011), leaves out every utterance in the first sample's key, and reads only the files written by `extract_swda.py`.
