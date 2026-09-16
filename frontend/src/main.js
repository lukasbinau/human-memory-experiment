import './styles.css';

const app = document.querySelector('#app');
const apiUrl = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');
const testingMode = import.meta.env.DEV;
const timingTestMode = new URLSearchParams(window.location.search).get('mode') === 'timing-test';
const totalMainTrials = 11;
const activeSessionKey = 'human-memory-v2-session';

let session;
let conditionIndex = 0;
let timer;
let tapTimes = [];
let participantCode = '';
let recalledWords = [];
let recallStartedAt;
let serialRecallStartedAt;
let serialPresentationStartedAt;
let cardGameTimer;
let recallFinishing = false;
let serialRecallFinishing = false;
let resumeAction = () => timingTestMode ? showTimingTestWelcome() : showWelcome();

function addSkipButton(action) {
  document.querySelector('.skip-button')?.remove();
  if (!testingMode) return;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'skip-button';
  button.textContent = 'Skip';
  button.addEventListener('click', action);
  document.body.appendChild(button);
}

function showStopControl() {
  if (document.querySelector('.stop-button')) return;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'stop-button';
  button.textContent = 'Stop';
  button.addEventListener('click', showStopConfirm);
  document.body.appendChild(button);
}

function hideStopControl() {
  document.querySelector('.stop-button')?.remove();
}

function showStopConfirm() {
  window.clearTimeout(timer);
  window.clearInterval(timer);
  window.clearInterval(cardGameTimer);
  document.removeEventListener('keydown', recordTap);
  document.querySelector('.skip-button')?.remove();
  hideStopControl();
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Stop experiment</p><h1>Stop now?</h1><p class="intro small">If you stop, your completed answers stay saved, but no further answers will be collected. If you continue, you will return to the start of the current step.</p><div class="stop-actions"><button type="button" id="stop-confirm-no">No, continue</button><button type="button" id="stop-confirm-yes" class="secondary-button">Yes, stop</button></div></section>`;
  document.querySelector('#stop-confirm-yes').addEventListener('click', endSessionStopped);
  document.querySelector('#stop-confirm-no').addEventListener('click', () => {
    showStopControl();
    resumeAction();
  });
}

function endSessionStopped() {
  hideStopControl();
  if (!timingTestMode) window.localStorage.removeItem(activeSessionKey);
  app.innerHTML = '<section class="panel narrow"><p class="kicker">Session stopped</p><h1>Thank you.</h1><p class="intro small">You stopped the experiment early. The answers you already submitted have been saved. You can close this window.</p></section>';
}

function showWelcome() {
  hideStopControl();
  app.innerHTML = `
    <section class="panel welcome loading-screen">
      <div class="loading-mark" aria-hidden="true"></div>
      <p class="eyebrow">02464 Artificial Intelligence and Human Cognition</p>
      <p class="kicker">Human memory study</p>
      <h1>Memory experiment</h1>
      <p class="intro">You will complete 11 memory trials involving Danish words and letters.</p>
      <ul class="consent-summary">
        <li>It takes about 15 minutes. Please complete it in a quiet place without interruptions.</li>
        <li>Your name and answers are stored together for the project analysis.</li>
        <li>Participation is voluntary. You may stop at any time without penalty.</li>
      </ul>
      <form id="welcome-form" class="welcome-form">
        <label for="participant-name">Your name</label>
        <input id="participant-name" name="participant-name" type="text" maxlength="80" autocomplete="name" placeholder="Enter your full name" required />
        <label class="consent-check" for="participant-consent"><input id="participant-consent" type="checkbox" required /><span>I have read this information and agree to participate.</span></label>
        <button type="submit">Agree and continue</button>
      </form>
    </section>
  `;
  window.setTimeout(() => document.querySelector('.loading-mark')?.remove(), 500);
  document.querySelector('#welcome-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const nameInput = document.querySelector('#participant-name');
    participantCode = nameInput.value.trim();
    if (!participantCode) {
      nameInput.setCustomValidity('Enter your name to continue.');
      nameInput.reportValidity();
      return;
    }
    nameInput.setCustomValidity('');
    showInstructions();
  });
}

function showTimingTestWelcome() {
  hideStopControl();
  app.innerHTML = `
    <section class="panel welcome loading-screen">
      <div class="loading-mark" aria-hidden="true"></div>
      <p class="eyebrow">02464 Artificial Intelligence and Human Cognition</p>
      <p class="kicker">Free-recall timing test</p>
      <h1>Compare word timings.</h1>
      <p class="intro">Choose timing pairs and try two word lists at a time. You can return to the menu and compare as many pairs as you like.</p>
      <form id="timing-welcome-form" class="welcome-form">
        <label for="participant-name">Your name</label>
        <input id="participant-name" name="participant-name" maxlength="80" autocomplete="name" placeholder="Enter your full name" required />
        <p class="muted">This is a separate timing test and will not be included in the main pilot analysis.</p>
        <button type="submit">Begin timing test</button>
      </form>
    </section>
  `;
  window.setTimeout(() => document.querySelector('.loading-mark')?.remove(), 500);
  document.querySelector('#timing-welcome-form').addEventListener('submit', (event) => {
    event.preventDefault();
    participantCode = document.querySelector('#participant-name').value.trim();
    showTimingTestInstructions();
  });
}

function showTimingTestInstructions() {
  resumeAction = showTimingTestInstructions;
  showStopControl();
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">Before we start</p>
      <h1>Choose what to compare.</h1>
      <ol class="instructions">
        <li>Select one of ten timing pairs from the menu.</li>
        <li>You will see two different lists of 15 words.</li>
        <li>The order of the two speeds is randomized and hidden.</li>
        <li>After both lists, choose another pair or finish whenever you like.</li>
      </ol>
      <button type="button" id="start-timing-button">Choose timing pair</button>
    </section>
  `;
  document.querySelector('#start-timing-button').addEventListener('click', startTimingTest);
}

async function startTimingTest() {
  showLoading('Preparing timing test');
  try {
    const response = await fetch(`${apiUrl}/api/timing-test/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ participant_code: participantCode }) });
    if (!response.ok) throw new Error();
    session = await response.json();
    showTimingPairMenu();
  } catch {
    showError('The Python backend could not start the timing test. Check that it is running.');
  }
}

function formatSeconds(displayMs) {
  const seconds = displayMs / 1000;
  return `${seconds} ${seconds === 1 ? 'second' : 'seconds'}`;
}

function showTimingPairMenu() {
  resumeAction = showTimingPairMenu;
  showStopControl();
  app.innerHTML = `
    <section class="panel timing-menu">
      <p class="kicker">Free-recall timing test</p>
      <h1>Choose a timing pair.</h1>
      <p class="intro small">Each comparison contains two 15-word lists in a randomized order.</p>
      <div class="timing-pair-grid">
        ${session.pairs.map((pair) => `<button type="button" class="timing-pair-button" data-pair-id="${pair.id}"><span>${formatSeconds(pair.first_ms)}</span><strong>vs.</strong><span>${formatSeconds(pair.second_ms)}</span></button>`).join('')}
      </div>
      <p class="muted">You can revisit any pair. Close the page when you are finished testing.</p>
    </section>
  `;
  document.querySelectorAll('.timing-pair-button').forEach((button) => button.addEventListener('click', () => startTimingPair(button.dataset.pairId)));
}

async function startTimingPair(pairId) {
  showLoading('Preparing comparison');
  try {
    const response = await fetch(`${apiUrl}/api/timing-test/pair`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id, pair_id: pairId }) });
    if (!response.ok) throw new Error();
    const comparison = await response.json();
    session.conditions = comparison.conditions;
    session.activePairId = comparison.pair_id;
    conditionIndex = 0;
    startCondition();
  } catch {
    showError('The timing pair could not be prepared. Check that the Python backend is running.');
  }
}

function showSerialConditionIntro() {
  resumeAction = showSerialConditionIntro;
  showStopControl();
  const trial = session.trials[conditionIndex];
  const taskText = {
    articulatory_suppression: `<p>You will see ${trial.length} letters, one at a time.</p><p>When the first letter appears, begin repeating “la-la-la” aloud. Continue without stopping while all letters are shown, then stop when the recall screen appears.</p><p>Remember the letters and enter them in the exact order shown.</p>`,
    finger_tapping: `<p>You will see ${trial.length} letters, one at a time.</p><p>When the first letter appears, begin tapping the space bar at a steady rhythm. Continue while all letters are shown, then stop when the recall screen appears.</p><p>Remember the letters and enter them in the exact order shown.</p>`,
    grouped: '<p>You will see three Danish words, one at a time. Each word contains three letters and appears for 2 seconds.</p><p>Together, the words contain nine letters. Remember all nine letters in the exact order shown.</p>',
    baseline_6: '<p>You will see 6 letters, one at a time.</p><p>Each letter appears for 2 seconds, with a short blank interval between letters. Remember them in the exact order shown.</p>',
    baseline_7: '<p>You will see 7 letters, one at a time.</p><p>Each letter appears for 2 seconds, with a short blank interval between letters. Remember them in the exact order shown.</p>',
    baseline_8: '<p>You will see 8 letters, one at a time.</p><p>Each letter appears for 2 seconds, with a short blank interval between letters. Remember them in the exact order shown.</p>',
    baseline_9: '<p>You will see 9 letters, one at a time.</p><p>Each letter appears for 2 seconds, with a short blank interval between letters. Remember them in the exact order shown.</p>',
  }[trial.condition];
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Serial recall · Trial ${trial.trial_number} of ${totalMainTrials}</p><h1>Remember ${trial.length} letters.</h1><div class="intro small">${taskText}</div><p class="muted instruction-note">After the presentation, you have ${session.settings?.serial_response_seconds || 30} seconds to respond. Your answer submits automatically when time runs out.</p><button type="button" id="continue-serial-button">Start trial</button></section>`;
  document.querySelector('#continue-serial-button').addEventListener('click', runSerialSequence);
  addSkipButton(runSerialSequence);
}

function runSerialSequence() {
  const trial = session.trials[conditionIndex];
  tapTimes = [];
  serialPresentationStartedAt = performance.now();
  if (trial.condition === 'finger_tapping') {
    document.addEventListener('keydown', recordTap);
  }
  showSerialUnit(0, trial);
}

function recordTap(event) {
  if (event.code === 'Space') {
    event.preventDefault();
    tapTimes.push(performance.now());
  }
}

function recordTouchTap(event) {
  event.preventDefault();
  tapTimes.push(performance.now());
}

function showSerialUnit(index, trial) {
  const units = trial.presentation_units || [...trial.sequence];
  if (index === units.length) {
    showSerialRecallForm();
    return;
  }
  if (!document.querySelector('.trial-screen')) {
    app.innerHTML = '<section class="trial-screen"><p class="progress"></p><div class="word"></div></section>';
  }
  document.querySelector('.progress').textContent = `Serial recall · Trial ${trial.trial_number} of ${totalMainTrials}`;
  document.querySelector('.word').textContent = units[index];
  addSkipButton(showSerialRecallForm);
  timer = window.setTimeout(() => showSerialBlank(index, trial), trial.unit_display_ms || session.display_ms);
}

function showSerialBlank(index, trial) {
  const units = trial.presentation_units || [...trial.sequence];
  if (index === units.length - 1) {
    showSerialRecallForm();
    return;
  }
  document.querySelector('.word').textContent = '';
  const interval = trial.intervals ? trial.intervals[index] : session.interval_ms;
  timer = window.setTimeout(() => showSerialUnit(index + 1, trial), interval);
}

function showSerialRecallForm() {
  window.clearTimeout(timer);
  document.querySelector('.skip-button')?.remove();
  const trial = session.trials[conditionIndex];
  const responseSeconds = session.settings?.serial_response_seconds || 30;
  serialRecallStartedAt = performance.now();
  serialRecallFinishing = false;
  app.innerHTML = `<section class="panel narrow"><div class="recall-header"><p class="kicker">Serial recall · Trial ${trial.trial_number} of ${totalMainTrials}</p><div class="countdown"><span>Time remaining</span><strong id="serial-countdown">0:${String(responseSeconds).padStart(2, '0')}</strong></div></div><h1>Enter the sequence.</h1><p class="intro small">Type only the letters you remember, in the order they appeared. It is okay to enter fewer letters. Do not guess. Uppercase, lowercase, and spaces are accepted.</p><form id="serial-form"><label for="serial-response">Your letter sequence</label><input id="serial-response" inputmode="text" autocomplete="off" autocapitalize="characters" maxlength="30" autofocus /><div class="form-footer"><span class="muted">Your response submits automatically when time runs out.</span><button type="submit">Submit sequence</button></div></form></section>`;
  document.querySelector('#serial-form').addEventListener('submit', submitSerialRecall);
  timer = window.setInterval(updateSerialRecallTimer, 250);
  addSkipButton(() => submitSerialRecall({ preventDefault() {} }));
}

function updateSerialRecallTimer() {
  const totalMs = (session.settings?.serial_response_seconds || 30) * 1000;
  const remaining = Math.max(0, totalMs - (performance.now() - serialRecallStartedAt));
  const seconds = Math.ceil(remaining / 1000);
  const countdown = document.querySelector('#serial-countdown');
  if (countdown) countdown.textContent = `0:${String(seconds).padStart(2, '0')}`;
  if (remaining === 0) submitSerialRecall({ preventDefault() {} });
}

async function submitSerialRecall(event) {
  event.preventDefault();
  if (!document.querySelector('#serial-form') || serialRecallFinishing) return;
  serialRecallFinishing = true;
  window.clearInterval(timer);
  const trial = session.trials[conditionIndex];
  const responseText = document.querySelector('#serial-response').value;
  const responseMs = Math.round(performance.now() - serialRecallStartedAt);
  document.removeEventListener('keydown', recordTap);
  document.querySelector('.skip-button')?.remove();
  const submission = { trial, responseText, responseMs };
  if (trial.condition === 'articulatory_suppression') {
    showSuppressionConfirmation(submission);
    return;
  }
  await sendSerialResponse(submission, null);
}

function showSuppressionConfirmation(submission) {
  resumeAction = () => showSuppressionConfirmation(submission);
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Serial recall · Trial 9 of ${totalMainTrials}</p><h1>One quick question.</h1><p class="intro small">Did you repeat “la-la-la” throughout the complete letter presentation?</p><div class="stop-actions"><button type="button" data-compliance="true">Yes</button><button type="button" data-compliance="false" class="secondary-button">No</button></div></section>`;
  document.querySelectorAll('[data-compliance]').forEach((button) => button.addEventListener('click', () => sendSerialResponse(submission, button.dataset.compliance === 'true')));
}

async function sendSerialResponse({ trial, responseText, responseMs }, suppressionConfirmed) {
  showLoading('Saving your response');
  const response = await fetch(`${apiUrl}/api/v2/serial-score`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id, presented_sequence: trial.sequence, response: responseText, trial_number: trial.trial_number, condition: trial.condition, experiment_part: trial.part, timing: { presentation_units: trial.presentation_units, unit_display_ms: trial.unit_display_ms, intervals: trial.intervals, total_exposure_ms: trial.total_exposure_ms }, task_data: { tap_count: tapTimes.length, tap_times_ms: tapTimes.map((value) => Math.round(value - serialPresentationStartedAt)), suppression_confirmed: suppressionConfirmed, chunks: trial.chunks || [], response_ms: responseMs, adaptive_derivation: trial.adaptive_derivation, matched_baseline_trial_number: trial.matched_baseline_trial_number } }) });
  if (!response.ok) { showError('The sequence could not be saved. Check your connection and try again.'); return; }
  showSerialResult();
}

function showSerialResult() {
  const isLast = conditionIndex === session.trials.length - 1;
  const trialNumber = session.trials[conditionIndex].trial_number;
  const nextLabel = isLast ? (trialNumber === 8 ? 'Continue' : 'View results') : 'Next trial';
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Trial ${trialNumber} of ${totalMainTrials} complete</p><h1>Your response has been saved.</h1><p class="intro small">Continue when you are ready.</p><button type="button" id="serial-next-button">${nextLabel}</button></section>`;
  document.querySelector('#serial-next-button').addEventListener('click', async () => {
    if (isLast && trialNumber === 8) {
      await loadAdaptiveTrials();
    } else if (isLast) {
      await showComplete();
    } else {
    conditionIndex += 1;
    showSerialConditionIntro();
    }
  });
}

async function loadAdaptiveTrials() {
  showLoading('Calculating your next trials');
  const response = await fetch(`${apiUrl}/api/v2/adaptive`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id }) });
  if (!response.ok) { showError('The adaptive trials could not be prepared.'); return; }
  const adaptive = await response.json();
  session.trials = adaptive.trials;
  conditionIndex = 0;
  showSerialConditionIntro();
}

function showInstructions() {
  resumeAction = showInstructions;
  showStopControl();
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">Before we start</p>
      <h1>Two kinds of recall.</h1>
      <ol class="instructions">
        <li>In free recall, remember words and enter them in any order.</li>
        <li>In serial recall, remember letters and enter them in the exact order shown.</li>
        <li>You will receive detailed instructions before every trial.</li>
        <li>Response screens are timed. You may finish early.</li>
      </ol>
      <p class="muted">Do not write down the items or refresh the page. You may stop at any time.</p>
      <button type="button" id="start-button">Start experiment</button>
    </section>
  `;
  document.querySelector('#start-button').addEventListener('click', startFinalProtocol);
}

async function startFinalProtocol() {
  showLoading('Preparing experiment');
  try {
    const response = await fetch(`${apiUrl}/api/v2/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ participant_code: participantCode }) });
    if (!response.ok) throw new Error();
    const protocol = await response.json();
    session = { ...protocol, trials: protocol.serial_baseline_trials, conditions: protocol.free_recall_conditions };
    window.localStorage.setItem(activeSessionKey, session.session_id);
    conditionIndex = 0;
    startCondition();
  } catch {
    showError('The experiment could not start. Check your connection and try again.');
  }
}

function startCondition() {
  const condition = session.conditions[conditionIndex];
  showConditionIntro(condition, runWordSequence);
}

function showConditionIntro(condition, next) {
  resumeAction = () => showConditionIntro(condition, next);
  const conditionName = timingTestMode ? `List ${conditionIndex + 1} / ${session.conditions.length}` : `Free recall · Trial ${condition.trial_number} of ${totalMainTrials}`;
  const responseSeconds = session.settings?.free_recall_response_seconds || 90;
  const taskText = timingTestMode
    ? '<p>You will see 15 Danish words one at a time. Recall them in any order after the final word.</p>'
    : {
      1: '<p>You will see 15 Danish words, one at a time. Each word appears for 2 seconds.</p><p>After the final word, recall begins immediately. Enter every word you remember; the order does not matter.</p>',
      2: '<p>You will see 15 new Danish words, one at a time. Each word appears for 1 second.</p><p>After the final word, recall begins immediately. Enter every word you remember; the order does not matter.</p>',
      3: `<p>You will see 15 new Danish words, one at a time. Each word appears for 2 seconds.</p><p>After the final word, there is a ${session.settings?.free_recall_pause_seconds || 15}-second waiting period. Recall begins automatically afterward.</p>`,
      4: `<p>You will see 15 new Danish words, one at a time. Each word appears for 2 seconds.</p><p>After the final word, you will play a ${session.settings?.card_game_seconds || 15}-second card-matching game. Recall begins automatically when the game ends.</p>`,
    }[condition.trial_number];
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">${conditionName}</p>
      <h1>${timingTestMode ? condition.label : 'Remember 15 words.'}</h1>
      <div class="intro small">${taskText}</div>
      <p class="muted instruction-note">You have ${responseSeconds} seconds to respond and may finish early. Your response submits automatically when time runs out.</p>
      <button type="button" id="continue-button">Start ${timingTestMode ? 'list' : 'trial'}</button>
    </section>
  `;
  document.querySelector('#continue-button').addEventListener('click', next);
  addSkipButton(next);
}

function runWordSequence() {
  showWord(0);
}

function showWord(index) {
  const condition = session.conditions[conditionIndex];
  if (index === condition.words.length) {
    finishConditionTask(condition);
    return;
  }
  app.innerHTML = `
    <section class="trial-screen">
      <p class="progress">${timingTestMode ? `List ${conditionIndex + 1} / ${session.conditions.length}` : `Free recall · Trial ${condition.trial_number} of ${totalMainTrials}`}</p>
      <div class="word">${condition.words[index]}</div>
    </section>
  `;
  addSkipButton(() => finishConditionTask(condition));
  timer = window.setTimeout(() => showWord(index + 1), condition.display_ms);
}

function finishConditionTask(condition) {
  window.clearTimeout(timer);
  if (condition.post_task === 'pause') {
    showTimedPause();
  } else if (condition.post_task === 'card_game') {
    showCardGame();
  } else {
    showRecallForm();
  }
}

function showTimedPause() {
  let secondsLeft = session.settings?.free_recall_pause_seconds || 15;
  app.innerHTML = `<section class="trial-screen"><p class="kicker light">Free recall · Trial ${session.conditions[conditionIndex].trial_number} of ${totalMainTrials}</p><div><div class="timer">${secondsLeft}</div><p class="pause-note">Recall begins automatically.</p></div></section>`;
  addSkipButton(showRecallForm);
  timer = window.setInterval(() => {
    secondsLeft -= 1;
    const timerElement = document.querySelector('.timer');
    if (timerElement) timerElement.textContent = secondsLeft;
    if (secondsLeft === 0) {
      window.clearInterval(timer);
      showRecallForm();
    }
  }, 1000);
}

function showCardGame() {
  const cards = ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'X'].sort(() => Math.random() - 0.5);
  let firstCard;
  let locked = false;
  const selected = new Set();
  let secondsLeft = session.settings?.card_game_seconds || 15;

  app.innerHTML = `
    <section class="panel game-panel">
      <p class="kicker">Free recall · Trial ${session.conditions[conditionIndex].trial_number} of ${totalMainTrials} · <span id="game-timer">${secondsLeft}</span></p>
      <h1>Match the cards.</h1>
      <p class="intro small">Turn over two cards at a time. One card has no matching partner.</p>
      <div class="card-grid">${cards.map((_, index) => `<button class="memory-card" data-index="${index}" type="button">?</button>`).join('')}</div>
    </section>
  `;

  const gameTimer = window.setInterval(() => {
    secondsLeft -= 1;
    const timerElement = document.querySelector('#game-timer');
    if (timerElement) timerElement.textContent = secondsLeft;
    if (secondsLeft === 0) {
      window.clearInterval(gameTimer);
      showRecallForm();
    }
  }, 1000);
  cardGameTimer = gameTimer;
  addSkipButton(() => {
    window.clearInterval(cardGameTimer);
    showRecallForm();
  });

  document.querySelectorAll('.memory-card').forEach((button) => {
    button.addEventListener('click', () => {
      if (locked || selected.has(Number(button.dataset.index))) return;
      const index = Number(button.dataset.index);
      button.textContent = cards[index];
      if (firstCard === undefined) {
        firstCard = index;
        return;
      }
      locked = true;
      const firstButton = document.querySelector(`[data-index="${firstCard}"]`);
      if (cards[firstCard] === cards[index]) {
        selected.add(firstCard);
        selected.add(index);
        firstButton.classList.add('matched');
        button.classList.add('matched');
        firstCard = undefined;
        locked = false;
      } else {
        window.setTimeout(() => {
          firstButton.textContent = '?';
          button.textContent = '?';
          firstCard = undefined;
          locked = false;
        }, 700);
      }
    });
  });
}

function showRecallForm() {
  window.clearTimeout(timer);
  window.clearInterval(cardGameTimer);
  const condition = session.conditions[conditionIndex];
  const responseSeconds = session.settings?.free_recall_response_seconds || 90;
  recalledWords = [];
  recallStartedAt = performance.now();
  recallFinishing = false;
  app.innerHTML = `
    <section class="panel narrow">
      <div class="recall-header"><p class="kicker">${timingTestMode ? `List ${conditionIndex + 1} / ${session.conditions.length}` : `Free recall · Trial ${condition.trial_number} of ${totalMainTrials}`}</p><div class="countdown"><span>Time remaining</span><strong id="countdown">${Math.floor(responseSeconds / 60)}:${String(responseSeconds % 60).padStart(2, '0')}</strong></div></div>
      <h1>Enter the words you remember.</h1>
      <p class="intro small">Type one word and select Add, then repeat. Order does not matter. Remove an entry if needed, and select Finish recall when you remember no more.</p>
      <form id="recall-form">
        <div id="remembered-words" class="remembered-words" aria-live="polite"><span class="muted">Your words will appear here.</span></div>
        <label for="recall-response">Your remembered words</label>
        <div class="word-entry"><input id="recall-response" autocomplete="off" autofocus /><button type="submit" aria-label="Add word">Add</button></div>
        <div class="form-footer"><span class="muted">Your response submits automatically when time runs out.</span><button type="button" id="finish-recall-button">Finish recall</button></div>
      </form>
    </section>
  `;
  document.querySelector('#recall-form').addEventListener('submit', submitRecall);
  document.querySelector('#finish-recall-button').addEventListener('click', finishRecall);
  timer = window.setInterval(updateRecallTimer, 250);
  addSkipButton(finishRecall);
}

function updateRecallTimer() {
  const totalMs = (session.settings?.free_recall_response_seconds || 90) * 1000;
  const remaining = Math.max(0, totalMs - (performance.now() - recallStartedAt));
  const seconds = Math.ceil(remaining / 1000);
  const countdown = document.querySelector('#countdown');
  if (countdown) countdown.textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  if (remaining === 0) finishRecall();
}

function submitRecall(event) {
  event.preventDefault();
  const input = document.querySelector('#recall-response');
  const word = input.value.trim();
  if (!word) return;
  recalledWords.push({ word, submittedAt: Math.round(performance.now() - recallStartedAt) });
  input.value = '';
  input.focus();
  renderRememberedWords();
}

function renderRememberedWords() {
  const list = document.querySelector('#remembered-words');
  list.innerHTML = recalledWords.length ? recalledWords.map((entry, index) => `<span class="word-chip">${entry.word}<button type="button" data-index="${index}" aria-label="Remove ${entry.word}">×</button></span>`).join('') : '<span class="muted">Your words will appear here.</span>';
  list.querySelectorAll('button').forEach((button) => button.addEventListener('click', () => {
    recalledWords.splice(Number(button.dataset.index), 1);
    renderRememberedWords();
  }));
}

async function finishRecall() {
  if (!document.querySelector('#recall-form') || recallFinishing) return;
  recallFinishing = true;
  window.clearInterval(timer);
  document.querySelector('.skip-button')?.remove();
  const condition = session.conditions[conditionIndex];
  const rawResponse = recalledWords.map((entry) => entry.word).join(', ');
  try {
    const scorePath = timingTestMode ? '/api/timing-test/score' : '/api/v2/free-score';
    const response = await fetch(`${apiUrl}${scorePath}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: session.session_id, presented_words: condition.words, response: rawResponse, condition: condition.name, trial_number: condition.trial_number, timing: { display_ms: condition.display_ms, post_task: condition.post_task }, task_data: { submissions: recalledWords, pair_id: session.activePairId } }),
    });
    if (!response.ok) throw new Error();
    if (timingTestMode) showTimingConditionComplete();
    else showConditionComplete();
  } catch {
    showError('The response could not be saved. Check your connection and try again.');
  }
}

function showTimingConditionComplete() {
  const isLast = conditionIndex === session.conditions.length - 1;
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">List ${conditionIndex + 1} / ${session.conditions.length} complete</p><h1>Response saved.</h1><p class="intro small">${isLast ? 'That comparison is complete. Choose another pair whenever you are ready.' : 'Take a moment before the second list.'}</p><button type="button" id="timing-next-button">${isLast ? 'Back to timing pairs' : 'Next list'}</button></section>`;
  document.querySelector('#timing-next-button').addEventListener('click', () => {
    if (isLast) showTimingPairMenu();
    else { conditionIndex += 1; showRest(startCondition); }
  });
}

function showConditionComplete() {
  resumeAction = showConditionComplete;
  const isLast = conditionIndex === session.conditions.length - 1;
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Trial ${session.conditions[conditionIndex].trial_number} of ${totalMainTrials} complete</p><h1>Your response has been saved.</h1><p class="intro small">Continue when you are ready.</p><button type="button" id="next-button">${isLast ? 'Continue to break' : 'Next trial'}</button></section>`;
  document.querySelector('#next-button').addEventListener('click', () => {
    if (isLast) showSectionBreak();
    else { conditionIndex += 1; showRest(startCondition); }
  });
}

function showSectionBreak() {
  let secondsLeft = session.settings?.section_break_seconds || 120;
  resumeAction = showSectionBreak;
  app.innerHTML = `<section class="panel centered"><p class="kicker">Free recall complete</p><h1>Take a break.</h1><p class="intro small">Serial recall begins next. The break lasts up to two minutes, but you may continue whenever you are ready.</p><div class="timer" id="break-timer">${secondsLeft}</div><button type="button" id="begin-serial-button">Continue to serial recall</button></section>`;
  const continueToSerial = () => { window.clearInterval(timer); conditionIndex = 0; showSerialInstructions(); };
  document.querySelector('#begin-serial-button').addEventListener('click', continueToSerial);
  addSkipButton(continueToSerial);
  timer = window.setInterval(() => {
    secondsLeft -= 1;
    document.querySelector('#break-timer').textContent = secondsLeft;
    if (secondsLeft === 0) continueToSerial();
  }, 1000);
}

function showSerialInstructions() {
  resumeAction = showSerialInstructions;
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Serial recall</p><h1>Remember letters in order.</h1><p class="intro small">Letters will appear one at a time. After each sequence, enter only the letters you remember in the exact order shown. Do not guess.</p><p class="muted">You will receive detailed instructions before every trial.</p><button type="button" id="begin-serial-trials">Continue</button></section>`;
  document.querySelector('#begin-serial-trials').addEventListener('click', showSerialConditionIntro);
  addSkipButton(showSerialConditionIntro);
}

function showRest(next) {
  resumeAction = () => showRest(next);
  app.innerHTML = `<section class="panel centered"><p class="kicker">Take a short rest</p><h1>Ready for the next trial?</h1><p class="muted">Continue when you are ready.</p><button type="button" id="rest-button">Continue</button></section>`;
  document.querySelector('#rest-button').addEventListener('click', next);
  addSkipButton(next);
}

async function showComplete() {
  hideStopControl();
  showLoading('Preparing your results');
  const response = await fetch(`${apiUrl}/api/v2/${session.session_id}/results`);
  if (!response.ok) { showError('Your results could not be loaded, but your responses remain saved.'); return; }
  const results = await response.json();
  window.localStorage.removeItem(activeSessionKey);
  const renderTrialRows = (section) => results.trials
    .filter((trial) => trial.section === section)
    .map((trial) => {
      const percentage = trial.total ? Math.round((trial.correct / trial.total) * 100) : 0;
      return `<li class="result-row"><div class="result-row-heading"><span>Trial ${trial.trial_number}</span><strong>${trial.correct} of ${trial.total}</strong></div><div class="result-bar" aria-label="Trial ${trial.trial_number}: ${percentage}% correct"><span style="width: ${percentage}%"></span></div></li>`;
    })
    .join('');
  app.innerHTML = `<section class="panel results-panel"><p class="kicker">Experiment complete</p><h1>Your results</h1><div class="result-summary"><div><strong>${results.free_recall_recalled}<span> / ${results.free_recall_total}</span></strong><p>Words recalled</p></div><div><strong>${results.serial_positional_matches}<span> / ${results.serial_total}</span></strong><p>Letters in the correct position</p></div></div><div class="result-sections"><section><h2>Free recall</h2><p class="muted">Words recalled in each trial</p><ol class="result-list">${renderTrialRows('free_recall')}</ol></section><section><h2>Serial recall</h2><p class="muted">Letters placed correctly in each trial</p><ol class="result-list">${renderTrialRows('serial_recall')}</ol></section></div><p class="muted result-note">These results are a simple summary, not an assessment of your memory ability. All eleven responses have been saved.</p></section>`;
}

async function restoreActiveSession() {
  const sessionId = window.localStorage.getItem(activeSessionKey);
  if (!sessionId) {
    showWelcome();
    return;
  }
  showLoading('Restoring your experiment');
  try {
    const response = await fetch(`${apiUrl}/api/v2/${sessionId}/state`);
    if (!response.ok) throw new Error();
    const protocol = await response.json();
    const completed = protocol.completed_trial_numbers;
    session = { ...protocol, trials: protocol.serial_baseline_trials, conditions: protocol.free_recall_conditions };
    showStopControl();
    if (completed.length === totalMainTrials) {
      await showComplete();
    } else if (completed.length < 4) {
      conditionIndex = completed.length;
      startCondition();
    } else if (completed.length === 4) {
      showSectionBreak();
    } else if (completed.length < 8) {
      conditionIndex = completed.length - 4;
      showSerialConditionIntro();
    } else {
      session.trials = protocol.adaptive.trials;
      conditionIndex = completed.length - 8;
      showSerialConditionIntro();
    }
  } catch {
    window.localStorage.removeItem(activeSessionKey);
    showError('The saved experiment could not be restored. Start a new session to continue.');
  }
}

function showLoading(message) {
  app.innerHTML = `<section class="panel centered"><p class="kicker">${message}</p><div class="loader"></div></section>`;
}

function showError(message) {
  hideStopControl();
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Something went wrong</p><h1>We could not continue.</h1><p class="intro small">${message}</p><button type="button" id="retry-button">Try again</button></section>`;
  document.querySelector('#retry-button').addEventListener('click', timingTestMode ? showTimingTestWelcome : showWelcome);
}

if (timingTestMode) showTimingTestWelcome();
else restoreActiveSession();
