# Human Memory Experiments

## Experiment Design Specification

**Course:** 02464 Artificial Intelligence and Human Cognition  
**Project:** Human Memory Mini Project  
**Design date:** 2 September 2026  
**Group:** s255728, s255213, s256191, s254943

This document is the operational specification for pilot version 1.0. It records the procedure, stimuli, timings, response rules, and data requirements that the app must implement. Each planned variation is performed once per participant. Any change discovered during piloting must be recorded as a new protocol version.

## 1. Study Overview

The study consists of two behavioural experiments:

1. A free-recall experiment investigating long-term memory effects in the recall of word sequences.
2. A serial-recall experiment investigating working-memory capacity, recall errors, chunking, and the effects of secondary tasks.

The app must present each trial, collect the participant's response, and save trial-level data for later analysis.

For pilot version 1.0, each participant completes 15 trials in total: four free-recall trials, six capacity trials, two chunking trials, and three secondary-task trials.

## 2. Free-Recall Experiment

### 2.1 Research effects

The free-recall experiment is designed to investigate:

- The primacy effect.
- The recency effect.
- The effect of increasing the presentation rate.
- The effect of a working-memory task immediately after the sequence and before recall.
- The effect of a pause immediately after the sequence and before recall.

### 2.2 Stimuli and response

- Each trial contains a sequence of exactly 15 Danish nouns.
- The nouns should describe clearly recognizable, simple objects.
- Each noun contains 3–7 letters.
- The app samples 60 distinct words from the approved 300-word CSV for each participant: 15 words for each of the four conditions.
- A word may not repeat within one participant's session, but may be reused by another participant.
- Participants freely type all words they remember after each sequence.
- No answer options are shown. This reduces the possibility of guessing from a predefined list.

### 2.3 Experimental conditions

| Condition | Word presentation | Post-sequence interval | Recall |
|---|---:|---|---|
| Baseline | 15 words, 2 seconds per word | None | Immediate free recall |
| Fast presentation | 15 words, 1 second per word | None | Immediate free recall |
| Pause | 15 words, 2 seconds per word | 15-second pause | Free recall |
| Working-memory task | 15 words, 2 seconds per word | 15-second card game | Free recall |

For the working-memory condition, the participant performs the nine-card memory game described in Section 6.7 during the 15-second interval.

### 2.4 Trial flow

1. Show a 1-second fixation screen.
2. Present 15 nouns sequentially at the condition-specific rate.
3. After the final noun, either begin recall immediately, show the 15-second pause, or run the 15-second card game.
4. Allow up to 90 seconds for the participant to type all remembered nouns in any order.
5. End the trial when the participant submits or the response timer expires, and save the raw response with the presented sequence and condition metadata.

### 2.5 Planned measurements

Recall performance should be measured by item position in the original sequence:

- **Primacy:** compare recall of items at the beginning of the sequence with recall of items in the middle.
- **Recency:** compare recall of items at the end of the sequence with recall of items in the middle.

The app should preserve the original item position so that each recalled word can be matched to its presentation position during analysis. Positions 1–5 are the primacy group, positions 6–10 are the middle group, and positions 11–15 are the recency group. Response-scoring rules are defined in Section 6.6.

Expected qualitative patterns:

- Recall should be higher for early items than for middle items.
- Recall should be higher for late items than for middle items.
- Faster presentation should primarily reduce the primacy effect.
- A working-memory task should primarily reduce the recency effect.
- A pause alone should have a smaller effect on recency than the working-memory task.

## 3. Serial-Recall Experiment

### 3.1 Research effects

The serial-recall experiment is designed to investigate:

- The limited capacity of working memory.
- The types of errors participants make.
- The effect of chunking.
- The effect of articulatory suppression.
- The lack of an effect of finger tapping.

### 3.2 Stimuli and response

- Stimuli are visually presented digits.
- Digits are presented one at a time for exactly 1000 ms each, followed by a 500 ms blank interval before the next digit.
- After the final digit, participants enter the complete sequence using the keyboard.
- Participants must reproduce the digits in the same order in which they were presented. They have 30 seconds to submit the response.

### 3.3 Part A: Working-memory capacity and error types

This part contains six trials, with sequence lengths 4, 5, 6, 7, 8, and 9 digits. The six lengths are presented in a random order generated from the session seed. The same trials are used to measure both recall capacity and error types.

Example sequence:

`4 7 2 9 1 6 3`

Recall accuracy will be measured as a function of sequence length. The expected pattern is that performance decreases as sequence length increases.

Errors should be classified using the following categories:

- **Transposition:** a presented item is recalled, but in the wrong position.
- **Omission:** a presented item is not recalled.
- **Substitution/intrusion:** an incorrect item is recalled.
- **Repetition:** an item is recalled more than once.

The scoring rules in Section 5 apply. Error categories are descriptive and may overlap; the raw response is always retained.

### 3.4 Part B: Chunking

Chunking will be tested with one relatively difficult sequence of exactly 9 digits.

| Condition | Presentation structure |
|---|---|
| Ungrouped | All digits are presented with 500 ms blank intervals |
| Grouped | The same nine digits are divided into groups of three, with 250 ms within-group intervals and 1250 ms between-group intervals |

Example:

- Ungrouped: `8 1 6 4 9 2 7 3 5`
- Grouped: `816 492 735`

The total presentation time is equal in both conditions. This controls for the possibility that grouped sequences improve performance simply because participants receive more presentation time.

The chunking effect will be quantified as:

`recall accuracy in grouped trials - recall accuracy in ungrouped trials`

The precise pause durations are 250 ms within groups and 1250 ms between groups for grouped trials, versus 500 ms for every interval in ungrouped trials. The definition of recall accuracy is given in Section 5.

### 3.5 Part C: Articulatory suppression and finger tapping

The following three conditions will each use one newly generated sequence of exactly 8 digits:

| Condition | Participant activity during presentation |
|---|---|
| Control | Memorize the digit sequence without a secondary task |
| Articulatory suppression | Repeatedly say a simple sound, such as “la-la-la” |
| Finger tapping | Repeatedly tap the same key or surface with one finger at a constant rhythm |

Expected relationship:

`P_articulatory suppression < P_control approximately equal to P_finger tapping`

Here, `P` denotes serial recall performance.

Articulatory suppression is expected to reduce recall because it interferes with verbal rehearsal in working memory. Finger tapping is a control task and is expected to have little or no effect compared with the control condition.

The tapping task should remain simple and regular. A complex tapping sequence could impose additional working-memory demands and undermine the control comparison.

## 4. Data the App Must Save

For every trial, the app should save enough information to reproduce the planned analyses. At minimum, this includes:

- Anonymous participant identifier.
- Experiment type: free recall or serial recall.
- Experiment part and condition.
- Trial number.
- Presented stimulus sequence.
- Original position of every presented item.
- Presentation duration and any pause durations.
- Start and end timestamps, where useful.
- Participant response.
- Response completion status.
- Any task-specific response, such as the working-memory-task answer.
- Scoring fields calculated either during or after the experiment.

The app should preferably save raw responses as well as derived scores. This allows scoring rules to be improved without asking participants to repeat the experiment.

## 5. Pilot Design

The first implementation should support brief pilot runs before data collection for the full experiment. Pilot runs should be used to check:

- That every condition can be completed from start to finish.
- That stimuli are readable and presented at the intended rate.
- That the working-memory, articulatory-suppression, and tapping instructions are understandable.
- That participants can enter free recall and serial recall responses as intended.
- That all trial data are saved correctly.
- That the total duration is reasonable.
- That the task is neither so easy that performance is perfect nor so difficult that performance is near zero.
- That the selected stimuli do not create obvious repetition, guessing, or other unwanted strategies.

Pilot data should be processed using the same analysis procedure intended for the main experiment, even though the pilot will not contain enough trials to establish reliable effects.

## 6. Pilot Implementation Notes

This section records implementation decisions for pilot version 1.0. Suggestions for the later main experiment are explicitly labelled as such.

### 6.1 Stimulus list

**Decided:** The group has a cleaned CSV file containing exactly 300 unique Danish nouns. The current file is [hukommelseseksperiment_300_ord.csv](hukommelseseksperiment_300_ord.csv).

**Pilot requirement:** Treat the CSV as a candidate pool, not as an automatically valid word list. Before the pilot, inspect all 300 entries and record at least:

- spelling and whether the word is a noun;
- number of letters;
- familiarity and recognizability;
- whether it describes a clearly identifiable simple object;
- singular/plural and grammatical form;
- potential ambiguity, offensiveness, regional usage, or uncommon spelling.

The final pool should contain more words than are needed for one participant. The trial generator should sample without replacement within a session, while storing the exact canonical form used in each trial.

**Decision:** The same cleaned master pool may be reused across participants, but a word may not repeat within one participant's session. The current CSV has one column, `ord`, and uses one canonical word per row.

**Completed:** The group has fully approved the current word list. It has been checked for duplicate entries, blank rows, review markers, and word length. All current entries contain 3–7 letters.

### 6.2 Number of trials

**Decided:** Each participant will complete each planned variation once.

This is appropriate for an initial pilot. For the main study, one trial per condition or sequence length will produce very noisy estimates, especially for serial recall. The most important recommendation is therefore to distinguish:

- **Pilot mode:** one trial per variation, used to test timing, instructions, data saving, and difficulty.
- **Main mode:** repeated trials per condition, subject to the one-hour limit and the group's participant constraints.

The app should support a configurable number of repetitions so this change does not require a redesign.

### 6.3 Condition order and counterbalancing

Randomizing every trial freely is not sufficient because adjacent conditions can influence one another. For example, a fast-presentation trial immediately before a baseline trial may affect expectations or fatigue.

For pilot version 1.0, use the fixed block order in Section 6.4. Counterbalancing is reserved for the main experiment, because the pilot is intended to test the app and procedure rather than estimate condition effects.

For the main experiment, the recommended approach is **block randomization with counterbalanced block orders**:

1. Put each condition in a clearly labelled block.
2. Randomize the order of blocks for each participant.
3. Use a balanced order scheme so that each condition appears roughly equally often in each serial position across participants. A Latin-square order is suitable when the number of participants is small.
4. Keep the condition order fixed within one participant once assigned, and save the order in the data.
5. Insert a rest screen between blocks.

If the pilot has too few participants for proper counterbalancing, use a predetermined order and record it rather than pretending it was randomized.

### 6.4 One-session structure

**Decided:** Participants complete all variations in one session, with ample time between variations.

**Pilot structure:** Use the four free-recall conditions in this order: baseline, fast presentation, pause, and working-memory task. Then show a 2-minute rest. Use the serial-recall parts in this order: capacity/error types, chunking, and secondary tasks. Show a rest screen between every condition block, with at least 30 seconds before the participant starts the next block. The participant may take longer between blocks, but may not pause during a timed trial except through the stop procedure.

The app should show estimated progress and allow the participant to stop safely. Fatigue and order should be recorded as possible limitations in the report.

### 6.5 Primacy, middle, and recency groups

**Pilot definition for 15-word sequences:**

- Primacy group: positions 1–5
- Middle group: positions 6–10
- Recency group: positions 11–15

This gives equally sized and interpretable comparison groups. For each item position, the app should also retain a binary recalled/not-recalled value. That allows the group to inspect the full serial-position curve later rather than being locked into the three-bin analysis.

The primary comparisons should be primacy versus middle and recency versus middle. The app should not calculate only a single overall recall percentage, because that would hide the effects being tested.

### 6.6 Free-recall response scoring

An entirely foolproof automatic spelling system is not realistic, particularly for free text in Danish. The safest design is a conservative, auditable pipeline:

1. Save the participant's raw response unchanged.
2. Split the response into entries using whitespace, commas, semicolons, and line breaks.
3. Normalize only harmless differences such as capitalization, surrounding punctuation, and repeated whitespace.
4. Match normalized entries exactly against the canonical words presented on that trial.
5. Use a Danish spellchecking dictionary and edit-distance matching only to suggest possible matches, never to silently award credit.
6. Flag ambiguous or near matches for manual review after data collection.
7. Keep both the raw response and the final scoring decision.

This approach is more defensible than silently correcting responses with an LLM. It also handles duplicate responses and intrusions transparently. Singular/plural variants should not receive automatic credit unless the scoring rules explicitly define them as equivalent.

The final scoring implementation should be tested against deliberately misspelled, punctuated, duplicated, and unrelated responses. The pilot uses exact normalized matching; possible spelling corrections are flagged for manual review and never silently awarded credit.

### 6.7 Working-memory task

**Decided for pilot version 1.0:** The working-memory interruption is a 3-by-3 grid of nine face-down cards containing four matching pairs and one unmatched card. The layout is shuffled at the start of the trial. The participant flips two cards at a time. Matching cards remain face up; non-matching cards turn face down after 1000 ms. The game lasts exactly 15000 ms, after which input is disabled.

Treat the game as an interference task, not as a second outcome measure. Record card flips, matches, and timestamps, but do not use game performance as a primary memory outcome.

The app should save the game start/end times and basic interaction data. The game begins immediately after the final word and ends automatically at 15000 ms.

### 6.8 Timing

The current free-recall timings are a reasonable starting point:

- Baseline, pause, and working-memory conditions: 2 seconds per word.
- Fast condition: 1 second per word.
- Pause and working-memory interruption: 15 seconds.

The app should use a monotonic clock and schedule stimulus changes against absolute target times rather than relying on chained delays. It should save the intended and observed timestamps so timing drift can be checked.

Transitions, instructions, and response entry should not be included in the 15-second experimental pause. The pilot should verify that the 1-second presentation is readable and that the 15-second interruption is long enough to affect recency without making the session unnecessarily tiring.

### 6.9 Serial-recall sequence lengths and repetitions

**Pilot choice:** Vary sequence length from 4 to 9 digits.

Use one trial at each length: 4, 5, 6, 7, 8, and 9. This is sufficient for a pilot but cannot reliably estimate a capacity curve. For the main experiment, use multiple randomized sequences at each length, with the exact count chosen after the pilot and duration check.

Sequences should be randomly generated subject to explicit rules preventing accidental patterns and should be stored exactly as presented. The app should record both item-level correctness and whole-sequence correctness, since these answer different questions.

### 6.10 Secondary-task sequence length

**Pilot choice:** Use 8-digit sequences for the control, articulatory-suppression, and finger-tapping comparison. Eight digits are difficult enough to leave room for impairment while avoiding a floor effect for most participants.

The same difficulty range and number of trials must be used in all three conditions. The pilot should check that control performance is neither near 100% nor near 0%; if it is, adjust the fixed length before the main study.

### 6.11 Grouped and ungrouped timing

The grouped and ungrouped conditions contain the same digits and have the same total presentation duration:

- Keep individual digit display durations identical.
- Place the longer pauses between groups in grouped trials.
- Distribute the same total pause time across non-group boundaries in ungrouped trials, or otherwise match the total duration exactly.
- Save all actual stimulus and pause timestamps for verification.

Simply adding extra pauses to grouped trials would confound chunking with extra exposure time. The exact schedule should be selected after deciding the normal inter-digit interval and tested with a stopwatch or timestamp log during the pilot.

### 6.12 Monitoring articulatory suppression

**Decided:** The task should be both instructed and monitored as far as practical.

**Pilot implementation:** Ask participants to repeat “la-la-la” continuously while digits are presented. Do not use a microphone or store audio in pilot version 1.0. Ask for a brief compliance confirmation after the trial. For an in-person pilot, an observer may record visible non-compliance.

Self-report and observer notes cannot guarantee compliance, so compliance is treated as an exploratory variable. The app must distinguish observer notes from participant self-report.

### 6.13 Finger tapping

**Pilot implementation:** Use the spacebar, paced by a visible 500 ms metronome cue, and record keydown timestamps. This gives the app an objective measure of whether taps occurred and whether their rhythm was roughly maintained.

The tapping instruction must remain repetitive and simple so it does not become a memory task. Tapping compliance is exploratory and does not determine whether the trial is included in the pilot's primary analysis.

### 6.14 Scoring serial-recall errors

The app should save the raw typed sequence and derive transparent scoring fields afterward. At minimum, calculate:

- item-level positional accuracy;
- whole-sequence accuracy;
- omissions;
- intrusions/substitutions;
- repetitions;
- transpositions where a presented digit is present but displaced.

Because one response can contain several error types, the scoring report should allow overlapping classifications rather than forcing every trial into exactly one category. For example, a response may contain both an omission and an intrusion. The exact precedence and algorithm should be fixed before analysing the main data, then tested on hand-constructed examples.

### 6.15 Data storage and hosting

**Decided direction:** Supabase for the database and Hugging Face for hosting. The exact technology stack will be selected after the project scaffolding is complete.

The implementation should keep the database contract independent of the user interface. Store raw trial records, derived scoring records, app version, and experiment configuration separately where practical. Use anonymous participant codes rather than names, restrict database access with row-level security, and never expose service-role credentials in the client application.

Supabase should be treated as the authoritative data store, with scheduled exports or a controlled backup process. Hugging Face hosting should be checked for the chosen framework, client-side timing behaviour, microphone permissions, and database-secret handling before committing to it.

### 6.16 Consent and participant safety

**Pilot requirement:** Before starting, show a short information and consent screen explaining the purpose of the study, what participation involves, approximate duration, data collected, anonymity, voluntary participation, and the right to stop without penalty.

The app should collect only the information needed for the analysis, generate or accept an anonymous participant ID, provide a clear stop button, and show a completion message. Do not collect microphone data by default; if microphone-based compliance checking is used, request separate explicit consent and define retention and deletion rules.

The group should confirm the applicable DTU course and data-protection expectations with the course staff before collecting data outside the project group.

### 6.17 Next design checkpoint

The following decisions are now recorded:

1. The 300-word CSV is fully approved and is the official pilot stimulus pool.
2. The current one-trial-per-variation design is for the pilot only. The main experiment will be designed later.
3. The pilot block order and rest schedule are defined in Section 6.3 and Section 6.4. The pilot uses a fixed order, with rest screens between blocks and a 2-minute break between the two experiments.
4. Further refinement and hand-testing of the scoring rules will be postponed until after the pilot.
5. The end-to-end pilot will be conducted later, after the app scaffolding and implementation are ready.

This document should be updated whenever one of these decisions changes.
