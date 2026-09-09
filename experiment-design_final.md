Human Memory Experiments

# Experiment Design Specification

**Course:** 02464 Artificial Intelligence and Human Cognition  
**Project:** Human Memory Mini Project  
**Design date:** 9 September 2026  
**Group:** s255728, s255213, s256191, s254943

This document is the operational specification for pilot version 1.0. It records the procedure, stimuli, timings, response rules, and data requirements that the app must implement. Each planned variation is performed once per participant. Any change discovered during piloting must be recorded as a new protocol version.

## 1. Study Overview

The study consists of two behavioural experiments:

1. A free-recall experiment investigating long-term memory effects in the recall of word sequences.
2. A serial-recall experiment investigating working-memory capacity, recall errors, semantic chunking, and the effects of secondary tasks using a standardized 15-letter sequence limit.

The app must present each trial, collect the participant's response, and save trial-level data for later analysis.

For pilot version 1.0, each participant completes 8 trials in total: four free-recall trials, one serial capacity baseline trial, two secondary-task trials, and one semantic-chunking trial. This reduced design is intended to keep the session brief and reduce fatigue.

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
- Participants submit remembered words one at a time after each sequence.
- Submitted words are displayed above the input field and can be removed individually before recall is finished.
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
4. Allow up to 90 seconds for recall. The countdown starts when the recall screen appears.
5. The participant types one word and presses Enter to submit it. The word appears above the input field with a small remove button.
6. End the trial when the participant presses `Finish recall` or the response timer expires, and save the submitted words, submission times, removals, and raw response data with the presented sequence and condition metadata.

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

- The limited capacity of working memory using a standardized 15-item constraint.
- The types of errors participants make.
- The effect of semantic chunking, comparing meaningful groups with random consonants.
- The effect of articulatory suppression.
- The lack of an effect of finger tapping.

### 3.2 Stimuli and response

- Stimuli are visually presented letters.
- Non-chunking trials use random consonants only, excluding vowels, to reduce accidental semantic chunking.
- Letters are presented one at a time for exactly 1000 ms each, followed by a 500 ms blank interval before the next letter.
- After the final letter, participants enter the complete sequence using the keyboard.
- Participants must reproduce the letters in the same order in which they were presented. They have 30 seconds to submit the response.

### 3.3 Part A: Working-memory capacity and error types

This part contains one trial consisting of exactly 15 random consonants. It replaces the incremental 4–9 length trials so that the pilot remains short and all serial conditions use a standardized 15-item baseline.

The non-chunking consonant pool is:

`B, C, D, F, G, H, J, K, L, M, N, P, Q, R, S, T, V, W, X, Z`

The trial generator samples without replacement within a trial. Example sequence:

`X P Q M R T F K S V N L C B Z`

Fifteen items exceed standard working-memory capacity for many participants, so floor effects are expected. This limitation must be acknowledged and discussed as a possible indicator of cognitive overload rather than interpreted as a precise individual capacity estimate.

Errors should be classified using the following categories:

- **Transposition:** a presented item is recalled, but in the wrong position.
- **Omission:** a presented item is not recalled.
- **Substitution/intrusion:** an incorrect item is recalled.
- **Repetition:** an item is recalled more than once.

The scoring rules in Section 6.14 apply. Error categories are descriptive and may overlap; the raw response is always retained.

### 3.4 Part B: Semantic chunking

Chunking is tested by comparing the 15-random-consonant baseline with a specialized 15-letter sequence that forms five recognizable three-letter words or abbreviations. Both trials use the same display speed.

| Condition | Presentation structure |
|---|---|
| Baseline (ungrouped) | 15 random consonants presented sequentially |
| Semantic chunking | 15 letters forming five three-letter words or recognizable abbreviations, presented sequentially |

Example semantic-chunking sequence:

`C A T D O G S U N C A R M A C`

This forms `CAT`, `DOG`, `SUN`, `CAR`, and `MAC`. The chunking sequence is predefined and must be stored exactly as presented. It is intentionally allowed to contain vowels because semantic chunking is the manipulation being tested.

The chunking effect will be quantified as:

`recall accuracy in semantic-chunking trial - recall accuracy in baseline trial`

The total number of presented letters and the duration of each letter presentation must be identical in the two trials. Any difference in performance is therefore interpreted cautiously, because the fixed condition order can also create practice effects.

### 3.5 Part C: Articulatory suppression and finger tapping

The two secondary-task conditions each use a newly generated sequence of exactly 15 random consonants. The baseline sequence from Part A is the control comparison.

| Condition | Participant activity during presentation |
|---|---|
| Baseline (control) | Memorize the consonant sequence without a secondary task |
| Articulatory suppression | Repeatedly say a simple sound, such as “la-la-la” |
| Finger tapping | Repeatedly tap the same key or surface with one finger at a constant rhythm |

Expected relationship:

`P_articulatory suppression < P_baseline approximately equal to P_finger tapping`

Applying these constraints to 15-item consonant lists may produce severe floor effects. The results must therefore be interpreted as a pilot comparison of cognitive load, not as a reliable estimate of capacity.

The tapping task should remain simple and regular. A complex tapping sequence could impose additional working-memory demands and undermine the control comparison.

## 4. Data the App Must Save

For every trial, the app should save enough information to reproduce the planned analyses. At minimum, this includes:

- Participant name supplied at the beginning of the session.
- Experiment type: free recall or serial recall.
- Experiment part and condition.
- Trial number.
- Presented stimulus sequence.
- Original position of every presented item.
- Presentation duration and any pause durations.
- Start and end timestamps, where useful.
- Participant response.
- Response completion status.
- Any task-specific response, such as the working-memory-task answer or tapping timestamps.
- Scoring fields calculated either during or after the experiment.

The app should preferably save raw responses as well as derived scores. This allows scoring rules to be improved without asking participants to repeat the experiment. For serial trials, it must also save the exact condition sequence and whether the sequence was generated or predefined.

## 5. Pilot Design

The first implementation should support brief pilot runs before data collection for the full experiment. Pilot runs should be used to check:

- That every condition can be completed from start to finish.
- That stimuli are readable and presented at the intended rate.
- That the working-memory, articulatory-suppression, and tapping instructions are understandable.
- That participants can enter free recall and serial recall responses as intended.
- That all trial data are saved correctly.
- That the total duration is reasonable and remains under approximately 15 minutes for the pilot protocol.
- That the 15-item serial tasks are not so difficult that all scores are zero, while acknowledging that low scores are expected.
- That the selected stimuli do not create obvious repetition, guessing, or other unwanted strategies.

Pilot data should be processed using the same analysis procedure intended for the main experiment, even though the pilot will not contain enough trials to establish reliable effects. The fixed order must be reported as a limitation because practice and fatigue are not counterbalanced.

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

For serial recall, non-chunking trials must use the consonant pool in Section 3.3, sampled without replacement within each trial. The semantic-chunking trial must use the predefined 15-letter sequence in Section 3.4.

### 6.2 Number of trials

**Decided:** Each participant will complete each planned variation exactly once. The pilot therefore contains four free-recall trials and four serial-recall trials: baseline capacity, articulatory suppression, finger tapping, and semantic chunking.

This is appropriate for an initial pilot. For the main study, one trial per condition will produce noisy estimates, especially for serial recall. The app should support a configurable number of repetitions so this change does not require a redesign.

### 6.3 Condition order and practice effects

**Decided for pilot version 1.0:** Do not randomize or counterbalance conditions. Use the following strategic fixed sequence for the serial-recall experiment:

1. Baseline capacity: 15 random consonants.
2. Articulatory suppression: 15 random consonants.
3. Finger tapping: 15 random consonants.
4. Semantic chunking: 15 letters forming five three-letter words or abbreviations.

The baseline is first to establish a comparison before serial-recall practice begins. The articulatory-suppression condition is kept early so practice does not obscure its difficulty. Semantic chunking is last, where the result will be affected by both chunking and practice; this combined effect must be stated as a limitation rather than treated as a pure chunking effect.

For a later main experiment, use counterbalanced block orders or a Latin-square design and repeated trials. Keep the assigned order fixed within one participant and save it in the data.

### 6.4 One-session structure

Participants complete all variations in one session. Use the four free-recall conditions in this order: baseline, fast presentation, pause, and working-memory task. Then show a 2-minute rest. Use the serial-recall conditions in the fixed order defined in Section 6.3. Show a rest screen between every condition block, with at least 30 seconds before the participant starts the next block. The participant may take longer between blocks, but may not pause during a timed trial except through the stop procedure.

The app should show estimated progress and allow the participant to stop safely. Fatigue and fixed order should be recorded as possible limitations in the report.

### 6.5 Primacy, middle, and recency groups

For 15-word free-recall sequences:

- Primacy group: positions 1–5
- Middle group: positions 6–10
- Recency group: positions 11–15

For each item position, the app should also retain a binary recalled/not-recalled value. The primary comparisons should be primacy versus middle and recency versus middle. The app should not calculate only a single overall recall percentage, because that would hide the effects being tested.

### 6.6 Free-recall response scoring

An entirely foolproof automatic spelling system is not realistic, particularly for free text in Danish. The safest design is a conservative, auditable pipeline:

1. Save the participant's raw response unchanged.
2. Split the response into entries using whitespace, commas, semicolons, and line breaks.
3. Normalize only harmless differences such as capitalization, surrounding punctuation, and repeated whitespace.
4. Match normalized entries exactly against the canonical words presented on that trial.
5. Use a Danish spellchecking dictionary and edit-distance matching only to suggest possible matches, never to silently award credit.
6. Flag ambiguous or near matches for manual review after data collection.
7. Keep both the raw response and the final scoring decision.

The pilot uses exact normalized matching. Possible spelling corrections are flagged for manual review and never silently awarded credit. Singular/plural variants should not receive automatic credit unless the scoring rules explicitly define them as equivalent. Test the implementation with deliberately misspelled, punctuated, duplicated, and unrelated responses.

### 6.7 Working-memory task

**Decided for pilot version 1.0:** The working-memory interruption is a 3-by-3 grid of nine face-down cards containing four matching pairs and one unmatched card. The layout is shuffled at the start of the trial. The participant flips two cards at a time. Matching cards remain face up; non-matching cards turn face down after 1000 ms. The game lasts exactly 15000 ms, after which input is disabled.

Treat the game as an interference task, not as a second outcome measure. Record card flips, matches, and timestamps, but do not use game performance as a primary memory outcome. The game begins immediately after the final word and ends automatically at 15000 ms.

### 6.8 Timing

The free-recall timings are:

- Baseline, pause, and working-memory conditions: 2 seconds per word.
- Fast condition: 1 second per word.
- Pause and working-memory interruption: 15 seconds.
- Serial letter presentation: 1000 ms per letter with a 500 ms blank interval.
- Serial response window: 30 seconds.

The app should use a monotonic clock and schedule stimulus changes against absolute target times rather than relying on chained delays. It should save the intended and observed timestamps so timing drift can be checked.

Transitions, instructions, and response entry should not be included in the 15-second experimental pause. The pilot should verify that the 1-second word presentation is readable and that serial letters are displayed at the intended rate.

### 6.9 Serial-recall stimuli

Non-chunking trials use random consonants sampled without replacement from:

`B, C, D, F, G, H, J, K, L, M, N, P, Q, R, S, T, V, W, X, Z`

The capacity, articulatory-suppression, and finger-tapping trials each require a newly generated sequence of 15 consonants. The semantic-chunking trial uses the predefined sequence `C A T D O G S U N C A R M A C`. All sequences must be stored exactly as presented, including original item positions.

### 6.10 Monitoring articulatory suppression

**Decided:** The task should be both instructed and monitored as far as practical.

**Pilot implementation:** Ask participants to repeat “la-la-la” continuously while letters are presented. Do not use a microphone or store audio in pilot version 1.0. Ask for a brief compliance confirmation after the trial. For an in-person pilot, an observer may record visible non-compliance.

Self-report and observer notes cannot guarantee compliance, so compliance is treated as an exploratory variable. The app must distinguish observer notes from participant self-report.

### 6.11 Finger tapping

**Pilot implementation:** Use the spacebar, paced by a visible 500 ms metronome cue, and record keydown timestamps. This gives the app an objective measure of whether taps occurred and whether their rhythm was roughly maintained.

The tapping instruction must remain repetitive and simple so it does not become a memory task. Tapping compliance is exploratory and does not determine whether the trial is included in the pilot's primary analysis.

### 6.12 Scoring serial-recall responses

The app should save the raw typed sequence and derive transparent scoring fields afterward. At minimum, calculate:

- item-level positional accuracy;
- whole-sequence accuracy;
- omissions;
- intrusions/substitutions;
- repetitions;
- transpositions where a presented letter is present but displaced.

Because one response can contain several error types, the scoring report should allow overlapping classifications rather than forcing every trial into exactly one category. For example, a response may contain both an omission and an intrusion. The exact precedence and algorithm should be fixed before analysing the main data, then tested on hand-constructed examples.

### 6.13 Data storage and hosting

**Decided direction:** Supabase for the database and Hugging Face for hosting. The implementation should keep the database contract independent of the user interface.

Store raw trial records, derived scoring records, app version, and experiment configuration separately where practical. Store the participant's supplied name with the session, restrict database access with row-level security, and never expose service-role credentials in the client application.

Supabase should be treated as the authoritative data store, with scheduled exports or a controlled backup process. Hugging Face hosting should be checked for the chosen framework, client-side timing behaviour, microphone permissions, and database-secret handling before committing to it.

### 6.14 Consent and participant safety

Before starting, show a minimal information and consent screen explaining the purpose of the study, what participation involves, approximate duration, that the participant's name and results are stored together, voluntary participation, and the right to stop without penalty. The screen should use plain language and avoid unnecessary institutional or legal text for this informal pilot.

The participant enters their actual name at the beginning of the session. The app should collect only the information needed for the analysis, provide a clear stop button, and show a completion message. Do not collect microphone data by default; if microphone-based compliance checking is used later, request separate explicit consent and define retention and deletion rules.

The group should confirm the applicable DTU course and data-protection expectations with the course staff before collecting data outside the project group.

### 6.15 Next design checkpoint

The following decisions are now recorded:

1. The 300-word CSV is fully approved and is the official pilot stimulus pool.
2. The pilot has four free-recall trials and four serial-recall trials, with one trial per planned variation.
3. Serial recall uses 15-letter sequences: random consonants for baseline and secondary tasks, and a predefined semantic-chunking sequence.
4. The pilot uses the fixed serial order in Section 6.3. Randomization and counterbalancing are reserved for the main experiment.
5. Further refinement and hand-testing of the scoring rules will be completed before analysing the main data.
6. The end-to-end pilot will be conducted after the app scaffolding and implementation are ready.

This document should be updated whenever one of these decisions changes.

## 7. Final App Interaction Decisions

### 7.1 Loading and welcome screen

1. Open the app on a white landing screen.
2. Show a centered loading animation while the app loads its configuration and checks the backend connection.
3. Once loading is complete, show the experiment title and short general instructions in the center of the page.
4. At the bottom of the page, show a field labelled `Your name`.
5. The participant enters their actual name.
6. The `Begin experiment` button starts the session and saves the participant name.

The loading animation must end automatically. It must not be used to hide a failed backend connection; a clear error message should be shown if the app cannot start a session.

### 7.2 Experiment and condition start

1. After `Begin experiment`, show a short introduction to the first experiment.
2. Show a `Start` button before each timed condition.
3. The timed trial begins only after the participant presses `Start`.
4. Do not include a practice trial. The first real trial is preceded by instructions only.
5. Show a rest screen between condition blocks and the planned two-minute break between the free-recall and serial-recall experiments.

### 7.3 Free-recall response interface

The recall screen contains these elements in this order:

1. Condition name and a 90-second countdown.
2. A list of submitted words above the input field.
3. A single-word input field.
4. A `Finish recall` button below the input field.

When the participant presses Enter:

- prevent form submission and page reload;
- trim the entered word;
- ignore an empty entry;
- add the word to the visible list;
- clear and refocus the input field;
- save the submission time relative to the start of recall.

Each submitted word has a small `x` button in its corner. Pressing it removes the word from the visible list and records the removal. The app should use a brief, subtle slide-and-fade animation when a word is added. The animation must not delay the next entry or affect the countdown.

The submitted-word list remains visible because it helps participants avoid accidental duplicate entries. The raw submission history, including removed words, must still be saved for later inspection.

When the participant presses `Finish recall`, or when the 90-second countdown reaches zero, the app saves the trial and advances. The app shows a completion message for the condition but does not show recall scores during the experiment. This prevents feedback from influencing later conditions.

### 7.4 Participant names

The participant name is used to identify which results belong to which participant. The app should explain that the name is saved with the session and its trial records. The current database column is named `participant_code` for backward compatibility, but it stores the participant's supplied name.

The app should validate that the field is not empty and should allow letters, numbers, hyphens, and underscores. The exact minimum and maximum length will be set during implementation.

## 8. Analysis Reminder

Before any data analysis begins, normalize the free-recall dataset using the finalized scoring rules. Preserve the original raw responses, create normalized response tokens, and document how capitalization, punctuation, whitespace, spelling variants, duplicates, and intrusions were handled. Do not overwrite the raw data.

For the serial-recall pilot, report the fixed condition order and the standardized 15-item limit explicitly. Interpret the semantic-chunking comparison cautiously because the chunking condition is last and therefore confounded with practice effects. Report item-level and whole-sequence accuracy, as well as overlapping error categories.
