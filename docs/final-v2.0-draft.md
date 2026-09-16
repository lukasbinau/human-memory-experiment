# Final Protocol v2.1 Draft

**Protocol identifier:** `final-v2.1-draft`  
**Designed:** 15 September 2026  
**Revised:** 2026  
**Status:** Implemented draft

This document specifies the group's revised experiment. It replaces the
nine-trial design in `final-v1.0-draft` for future implementation, but it does
not change or reinterpret data collected under an earlier protocol version.
The trial flow and explicitly stated timings below are agreed design choices.
Details carried over from the implemented protocol are stated explicitly so
they remain auditable.

## 1. Study Overview

The experiment consists of two parts:

1. **Free recall:** participants remember words without regard to presentation
   order.
2. **Serial recall:** participants remember letters and reproduce them in the
   exact order in which they appeared.

Each participant completes 11 trials in one session: four free-recall trials,
four serial-baseline trials, and three subsequent serial-recall trials. A
two-minute timed break separates free recall from serial recall, but the
participant may skip the remainder and continue early. Other rest screens are
participant-controlled.

## 2. Fixed Trial Order

| Trial | Experiment part | Condition | Stimulus length |
|---:|---|---|---:|
| 1 | Free recall | Baseline | 15 words |
| 2 | Free recall | Fast presentation | 15 words |
| 3 | Free recall | Pause | 15 words |
| 4 | Free recall | Working-memory task | 15 words |
| 5 | Serial baseline | Baseline 6 | 6 letters |
| 6 | Serial baseline | Baseline 7 | 7 letters |
| 7 | Serial baseline | Baseline 8 | 8 letters |
| 8 | Serial baseline | Baseline 9 | 9 letters |
| 9 | Serial secondary task | Articulatory suppression | Adaptive: 6–9 letters |
| 10 | Serial secondary task | Finger tapping | Adaptive: 6–9 letters |
| 11 | Serial chunking | Meaningful chunks | 9 letters |

The order is fixed. Practice, fatigue, and condition are therefore confounded
with trial order and must be reported as a limitation.

## 3. Free Recall

### 3.1 Task and stimuli

Each trial presents 15 Danish nouns one at a time. The words describe simple,
recognizable objects and contain 3–7 letters. The four trials use different
word lists. A word does not repeat within one participant's session.

After presentation, the participant types every word they can remember. Recall
order does not matter, and the app provides no answer options.

### 3.2 Conditions

| Condition | Word display | Post-sequence task | Recall start |
|---|---:|---|---|
| Baseline | 2000 ms per word | None | Immediately |
| Fast presentation | 1000 ms per word | None | Immediately |
| Pause | 2000 ms per word | 15-second unfilled pause | After the pause |
| Working-memory task | 2000 ms per word | Card-matching game | After the game |

The fast presentation is exactly half the baseline duration. The
working-memory task uses the existing 15-second card-matching game. If the
participant finds every pair before time expires, the solved cards remain
visible and the recall screen still begins only when the timer expires.

The response period is 90 seconds, and participants may finish early. The app
must save the raw entries and the normalized entries, and it must not show
performance feedback between trials.

Automatic experimental scoring uses exact normalized matching. A separate
local pre-analysis pipeline may suggest likely spelling corrections for manual
review, but it must not silently alter raw responses or overwrite the original
exact-match score.

### 3.3 Measures

The primary free-recall measures are:

- number and proportion of presented words recalled;
- recall status for every original list position;
- primacy recall for positions 1–5;
- middle recall for positions 6–10;
- recency recall for positions 11–15;
- intrusions and repeated responses.

The planned comparisons are primacy versus middle and recency versus middle
within each condition, fast versus baseline, pause versus baseline, and
working-memory task versus baseline. Responses are scored by exact normalized
matching while preserving raw text for review.

## 4. Serial Recall Part 1: Individual Baseline

### 4.1 Procedure

The participant completes four trials in ascending order: 6, 7, 8, and 9
letters. Letters are presented one at a time. After each sequence, the
participant types the letters in the exact presentation order. There is no
secondary task in this part.

Each letter is displayed for 2000 ms. A 500 ms blank screen appears between
letters, with no blank required after the final letter. No fixation marker is
shown before a list. The response period is 30 seconds.

All four baseline trials are always completed. In particular, the nine-letter
baseline is required even when the participant has difficulty at a shorter
length, because it is the comparator for chunking.

### 4.2 Adaptive baseline rule

For each baseline trial, calculate positional accuracy by dividing the number
of letters recalled in the correct position by the number of letters shown.
Calculate the arithmetic mean of the four accuracies, multiply it by 9, round
down to the nearest whole number, and clamp the result to
the inclusive range 6–9. This result is the participant's adaptive length for
articulatory suppression and finger tapping.

For correct-position counts $c_6$, $c_7$, $c_8$, and $c_9$:

$$
L = \operatorname{clamp}_{6,9}\left(\operatorname{floor}
\left(\frac{9}{4}\left(\frac{c_6}{6}+\frac{c_7}{7}+
\frac{c_8}{8}+\frac{c_9}{9}\right)\right)\right)
$$

A trial is recorded as passed only when the complete sequence is correct, but
pass/fail does not determine the adaptive length. All four positional
accuracies contribute equally to the average. The lower clamp means the
adaptive tasks use six letters when the scaled and rounded average is below
six. A participant with perfect performance at all four lengths receives an
adaptive length of nine.

### 4.3 Measures

For every baseline length, save at least:

- number and proportion of letters in the correct position;
- whether the whole sequence is correct;
- raw and normalized response;
- omissions, substitutions or intrusions, transpositions, and repetitions.

## 5. Serial Recall Part 2: Secondary Tasks and Chunking

### 5.1 Articulatory suppression

The sequence contains the participant's adaptive number of letters. The
participant repeatedly says “la-la-la” while the letters are displayed. The
participant stops speaking after the final letter and then enters the sequence
in the correct order.

After recall, the participant records a self-confirmation of whether they
performed articulatory suppression as instructed. This is stored as compliance
metadata and does not automatically include or exclude the trial.

This condition is compared with the baseline trial of the same length. For
example, an adaptive seven-letter suppression trial is compared with the
participant's seven-letter baseline.

### 5.2 Finger tapping

The sequence contains the participant's adaptive number of letters. The
participant taps one finger at a steady rhythm while the letters are displayed,
stops after the final letter, and then enters the sequence in the correct
order.

This condition is also compared with the baseline trial of the same length.
Tapping uses the keyboard space bar without a pace cue. The app records tapping
count and keydown timestamps. Taps must not trigger scrolling or otherwise
interrupt stimulus presentation.

### 5.3 Chunking

The participant is shown three meaningful Danish three-letter words, giving
nine letters in total. The words allow the letters to be remembered as three
meaningful groups. The participant then enters all nine letters in the exact
presentation order.

Chunking is always compared with the participant's nine-letter baseline. Each
three-letter word is shown as one complete unit for 2000 ms. A 500 ms blank
screen appears between words, matching the inter-unit blank used between
individual serial letters.

This matches display and blank duration per visible unit, not total trial
duration or exposure per letter. The nine-letter baseline contains nine visible
units, whereas chunking contains three; this timing difference is part of the
chosen design and must be reported when interpreting the chunking comparison.

The three words and their flattened nine-letter sequence must be saved. Words
must come from the technically reviewed and group-approved chunk pool.

### 5.4 Measures and comparisons

The primary serial measure is positional accuracy: the proportion of letters
recalled in the correct position. Whole-sequence correctness and error types
are secondary measures. Ordered-subsequence accuracy may be retained as an
additional descriptive measure, but it does not replace positional accuracy.

The planned within-participant comparisons are:

- articulatory suppression versus baseline at the adaptive length;
- finger tapping versus baseline at the adaptive length;
- nine-letter chunking versus the nine-letter baseline.

Because each condition is represented by one trial, results will be noisy and
must not be interpreted as reliable participant-level capacity estimates.
The adaptive length is derived from four noisy baseline observations, while
each secondary-task effect is estimated from one later trial and one matched
baseline trial. These comparisons are therefore exploratory and cannot cleanly
isolate causal task effects without repeated trials.

## 6. Stimulus Rules

Free-recall words are sampled without replacement from the approved Danish noun
pool. Planned trials contain 60 distinct words. If a presentation is restarted
after a refresh, its replacement words must not overlap the planned words or
any words already presented in the session.

Non-chunked serial trials use uppercase letters sampled from the full Danish
alphabet. A letter may not repeat within a sequence. The exact generated
sequence is saved. A participant must not be shown the answer or receive
correctness feedback during the experiment.

The adaptive secondary-task trials use newly generated sequences rather than
repeat the baseline sequence. Their length, not their exact letters, is matched
to baseline. This avoids a direct practice benefit, although different
sequences may differ in difficulty.

## 7. Data Requirements

In addition to the existing session and trial fields, save:

- protocol version `final-v2.1-draft`;
- fixed trial number and condition;
- presented sequence and presentation units;
- intended and observed presentation timing;
- raw and normalized response;
- positional matches and positional accuracy;
- whole-sequence correctness and error counts;
- selected adaptive length and the four baseline outcomes used to derive it;
- the identifier of the matched baseline trial for trials 9–11;
- chunk identities and flattened chunk sequence;
- card-game and tapping interaction data;
- whether a response ended manually or by timeout.
- attempt number, refresh count, and the last saved phase for every trial.

### 7.1 Refresh and attempt handling

The server stores one authoritative row per trial, including while the trial is
in progress. Refreshing at the instruction screen returns to the same trial
with the same stimuli. Refreshing during stimulus presentation starts a new
attempt of the same trial with newly generated stimuli. Refreshing at the
response screen keeps the presented stimuli but clears the unsent answer and
restarts the full response timer.

`attempt_number` begins at one and increases only when an interrupted
presentation is replaced. `refresh_count` increases for every recovery request,
regardless of phase. Completing the trial updates the active row rather than
creating a duplicate. The score endpoint validates the submitted stimulus
against the active row, so a replaced presentation cannot later be submitted.

The session is marked complete only after all 11 trials have been saved.
Incomplete sessions and all timeout, blank-response, and compliance data remain
stored and distinguishable. Inclusion and exclusion rules are decided during
analysis rather than by discarding records during collection. Participant names
continue to be stored in the existing participant field and must be treated as
personal data.

After trial 11, participants see only aggregate totals: total free-recall words
recalled out of 60 and total serial letters recalled in the correct position
out of all serial letters presented. The serial denominator therefore reflects
the participant's adaptive length. No condition-level breakdown, accuracy
percentage, or correct answers are shown.

## 8. Confirmed Operational Decisions

The group confirmed the following on 15 September 2026:

1. Adaptive length is the mean positional accuracy across the four baseline
    trials, scaled to nine letters, rounded down, and clamped to 6–9.
2. Adaptive secondary-task trials use new non-repeating letter sequences.
3. All Danish letters are eligible for non-chunked serial sequences.
4. Serial letters and chunk words display for 2000 ms with 500 ms blanks.
5. No fixation marker appears before a list.
6. The card game lasts a fixed 15 seconds.
7. Finger tapping uses the space bar without a pace cue.
8. Articulatory-suppression compliance is self-confirmed.
9. Free- and serial-recall response limits are 90 and 30 seconds respectively.
10. All 60 free-recall words are distinct within a session.
11. No accuracy feedback appears during the experiment; aggregate totals appear
    after completion.
12. All collected records are retained for later inclusion decisions.
13. Participant names continue to be collected.
14. A two-minute timed break separates free and serial recall, with an option
    to continue early; all other rest screens are participant-controlled.
15. A solved card game remains visible until its fixed timer expires.
16. Final results show recalled words out of 60 and correct-position serial
    letters out of the participant-specific total presented.

Any change to these decisions after data collection begins requires a new
protocol identifier. Before implementation, the development team may still
need to choose non-experimental UI wording and storage keys, provided those
choices do not alter this protocol.

## 9. Validation Before Release

Before freezing this design as `final-v2.0`, the group must:

- update the backend protocol, frontend flow, scoring, and analysis together;
- add tests for all 11 trials and the adaptive-length edge cases;
- complete at least one desktop and one mobile session;
- verify all 11 stored trial rows and matched-baseline metadata;
- run the analysis data-quality checks on the validation sessions;
- record the deployed Git and hosting commit identifiers.