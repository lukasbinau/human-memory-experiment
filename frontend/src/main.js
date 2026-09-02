import './styles.css';

const app = document.querySelector('#app');
const apiUrl = 'http://127.0.0.1:8000';
const testingMode = import.meta.env.DEV;

let session;
let conditionIndex = 0;
let timer;
let tapTimes = [];
let participantCode = '';
let recalledWords = [];
let recallStartedAt;
let cardGameTimer;
let recallFinishing = false;

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

function showWelcome() {
  app.innerHTML = `
    <section class="panel welcome loading-screen">
      <div class="loading-mark" aria-hidden="true"></div>
      <p class="eyebrow">02464 Artificial Intelligence and Human Cognition</p>
      <p class="kicker">Pilot study</p>
      <h1>How much can you bring back?</h1>
      <p class="intro">A short study of how people remember words and sequences. Your answers are anonymous and help us test the experiment.</p>
      <form id="welcome-form" class="welcome-form">
        <label for="participant-code">Create an anonymous participant ID</label>
        <input id="participant-code" name="participant-code" maxlength="24" placeholder="e.g. blue-birch-07" required />
        <p class="muted">Do not use your name or email address.</p>
        <button type="submit">Begin experiment</button>
      </form>
    </section>
  `;
  window.setTimeout(() => document.querySelector('.loading-mark')?.remove(), 500);
  document.querySelector('#welcome-form').addEventListener('submit', (event) => {
    event.preventDefault();
    participantCode = document.querySelector('#participant-code').value.trim();
    if (!/^[A-Za-z0-9_-]+$/.test(participantCode)) return;
    showInstructions();
  });
}

function showSerialInstructions() {
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Pilot study / serial recall</p><h1>Hold the order.</h1><ol class="instructions"><li>A sequence of digits will appear one at a time.</li><li>Remember the digits in their exact order.</li><li>Type the complete sequence after it disappears.</li></ol><p class="muted">The pilot has six trials, from four to nine digits.</p><button type="button" id="start-serial-button">Start serial recall</button></section>`;
  document.querySelector('#start-serial-button').addEventListener('click', startSerialPilot);
}

async function startSerialPilot() {
  showLoading('Preparing serial recall');
  try {
    const response = await fetch(`${apiUrl}/api/serial/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id }) });
    if (!response.ok) throw new Error();
    session = await response.json();
    conditionIndex = 0;
    showSerialConditionIntro();
  } catch {
    showError('The Python backend could not start serial recall. Check that it is running.');
  }
}

function showSerialConditionIntro() {
  const trial = session.trials[conditionIndex];
  const taskText = {
    articulatory_suppression: 'Repeat “la-la-la” while the digits are shown.',
    finger_tapping: 'Press the spacebar steadily while the digits are shown.',
  }[trial.condition] || 'Focus on the order. The digits will appear once.';
  const partName = {
    capacity_and_errors: 'Capacity and error types',
    chunking: 'Chunking',
    secondary_tasks: 'Secondary tasks',
  }[trial.part];
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Serial recall · ${partName} · Trial ${conditionIndex + 1} / ${session.trials.length}</p><h1>${trial.label}</h1><p class="intro small">${taskText}</p><button type="button" id="continue-serial-button">Continue</button></section>`;
  document.querySelector('#continue-serial-button').addEventListener('click', runSerialSequence);
  addSkipButton(runSerialSequence);
}

function runSerialSequence() {
  const trial = session.trials[conditionIndex];
  tapTimes = [];
  if (trial.condition === 'finger_tapping') {
    document.addEventListener('keydown', recordTap);
  }
  showDigit(0, trial);
}

function recordTap(event) {
  if (event.code === 'Space') {
    event.preventDefault();
    tapTimes.push(performance.now());
  }
}

function showDigit(index, trial) {
  if (index === trial.sequence.length) {
    showSerialRecallForm();
    return;
  }
  if (!document.querySelector('.trial-screen')) {
    app.innerHTML = '<section class="trial-screen"><p class="progress"></p><div class="word"></div></section>';
  }
  document.querySelector('.progress').textContent = `Serial recall · Digit ${index + 1} / ${trial.length}`;
  document.querySelector('.word').textContent = trial.sequence[index];
  addSkipButton(showSerialRecallForm);
  timer = window.setTimeout(() => showSerialBlank(index, trial), session.display_ms);
}

function showSerialBlank(index, trial) {
  if (index === trial.sequence.length - 1) {
    showSerialRecallForm();
    return;
  }
  document.querySelector('.word').textContent = '';
  timer = window.setTimeout(() => showDigit(index + 1, trial), session.interval_ms);
}

function showSerialRecallForm() {
  window.clearTimeout(timer);
  document.querySelector('.skip-button')?.remove();
  const trial = session.trials[conditionIndex];
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Serial recall · ${trial.length} digits</p><h1>Enter the sequence.</h1><p class="intro small">Type the digits in the order you saw them.</p><form id="serial-form"><label for="serial-response">Your sequence</label><input id="serial-response" inputmode="numeric" autocomplete="off" maxlength="12" autofocus /><div class="form-footer"><span class="muted">Digits only.</span><button type="submit">Submit sequence</button></div></form></section>`;
  document.querySelector('#serial-form').addEventListener('submit', submitSerialRecall);
  addSkipButton(() => submitSerialRecall({ preventDefault() {} }));
}

async function submitSerialRecall(event) {
  event.preventDefault();
  const trial = session.trials[conditionIndex];
  const responseText = document.querySelector('#serial-response').value;
  document.removeEventListener('keydown', recordTap);
  document.querySelector('.skip-button')?.remove();
  const response = await fetch(`${apiUrl}/api/serial/score`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id, presented_sequence: trial.sequence, response: responseText, trial_number: trial.trial_number, condition: trial.condition, experiment_part: trial.part, task_data: { tap_count: tapTimes.length } }) });
  if (!response.ok) { showError('The sequence could not be saved. Check that the Python backend is running.'); return; }
  showSerialResult(await response.json());
}

function showSerialResult(result) {
  const isLast = conditionIndex === session.trials.length - 1;
  app.innerHTML = `<section class="panel narrow results"><p class="kicker">Trial complete</p><h1>${result.positional_matches} of ${result.presented_length} positions correct.</h1><div class="score-grid"><div><span>Accuracy</span><strong>${Math.round(result.positional_accuracy * 100)}%</strong></div><div><span>Omissions</span><strong>${result.omissions}</strong></div><div><span>Errors</span><strong>${result.substitutions}</strong></div></div><button type="button" id="serial-next-button">${isLast ? 'Finish pilot' : 'Next trial'}</button></section>`;
  document.querySelector('#serial-next-button').addEventListener('click', () => {
    if (isLast) {
      showComplete();
      return;
    }
    const currentPart = session.trials[conditionIndex].part;
    conditionIndex += 1;
    const nextPart = session.trials[conditionIndex].part;
    if (nextPart !== currentPart) showSerialPartIntro(nextPart);
    else showSerialConditionIntro();
  });
}

function showSerialPartIntro(part) {
  const partDetails = {
    chunking: {
      title: 'Chunking',
      text: 'The same nine digits will be shown twice: once evenly and once in groups of three.',
    },
    secondary_tasks: {
      title: 'Secondary tasks',
      text: 'The next three trials compare memorizing alone with speaking and tapping while the digits appear.',
    },
  }[part];
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Next part</p><h1>${partDetails.title}</h1><p class="intro small">${partDetails.text}</p><button type="button" id="start-part-button">Continue</button></section>`;
  document.querySelector('#start-part-button').addEventListener('click', showSerialConditionIntro);
  addSkipButton(showSerialConditionIntro);
}

function showInstructions() {
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">Before we start</p>
      <h1>Keep your attention on each word.</h1>
      <ol class="instructions">
        <li>Each word appears for two seconds, except in the fast condition.</li>
        <li>Remember as many words as you can.</li>
        <li>Type all remembered words after each list.</li>
        <li>There is a short rest between conditions.</li>
      </ol>
      <p class="muted">This pilot is anonymous. You can stop at any time.</p>
      <button type="button" id="start-button">Start pilot</button>
    </section>
  `;
  document.querySelector('#start-button').addEventListener('click', startPilot);
}

async function startPilot() {
  showLoading('Preparing pilot');
  try {
    const response = await fetch(`${apiUrl}/api/pilot/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ participant_code: participantCode }) });
    if (!response.ok) throw new Error();
    session = await response.json();
    conditionIndex = 0;
    startCondition();
  } catch {
    showError('The Python backend could not start the pilot. Check that it is running.');
  }
}

function startCondition() {
  const condition = session.conditions[conditionIndex];
  showConditionIntro(condition, runWordSequence);
}

function showConditionIntro(condition, next) {
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">Condition ${conditionIndex + 1} / ${session.conditions.length}</p>
      <h1>${condition.label}</h1>
      <p class="intro small">You will see 15 words. Type every word you remember afterwards.</p>
      <button type="button" id="continue-button">Continue</button>
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
      <p class="progress">${condition.label} · Word ${index + 1} / ${condition.words.length}</p>
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
  let secondsLeft = 15;
  app.innerHTML = `<section class="trial-screen"><p class="kicker light">Pause</p><div class="timer">${secondsLeft}</div></section>`;
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
  const cards = ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', '?'].sort(() => Math.random() - 0.5);
  let firstCard;
  let locked = false;
  const selected = new Set();
  let secondsLeft = 15;

  app.innerHTML = `
    <section class="panel game-panel">
      <p class="kicker">Memory game · <span id="game-timer">${secondsLeft}</span></p>
      <h1>Find matching pairs.</h1>
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
  recalledWords = [];
  recallStartedAt = performance.now();
  recallFinishing = false;
  app.innerHTML = `
    <section class="panel narrow">
      <div class="recall-header"><p class="kicker">${condition.label} · Recall</p><div class="countdown" id="countdown">1:30</div></div>
      <h1>Which words came back?</h1>
      <p class="intro small">Add one remembered word at a time. You can remove an entry before finishing.</p>
      <form id="recall-form">
        <div id="remembered-words" class="remembered-words" aria-live="polite"><span class="muted">Your words will appear here.</span></div>
        <label for="recall-response">Your remembered words</label>
        <div class="word-entry"><input id="recall-response" autocomplete="off" autofocus /><button type="submit" aria-label="Add word">Add</button></div>
        <div class="form-footer"><span class="muted">You have 90 seconds.</span><button type="button" id="finish-recall-button">Finish recall</button></div>
      </form>
    </section>
  `;
  document.querySelector('#recall-form').addEventListener('submit', submitRecall);
  document.querySelector('#finish-recall-button').addEventListener('click', finishRecall);
  timer = window.setInterval(updateRecallTimer, 1000);
  addSkipButton(finishRecall);
}

function updateRecallTimer() {
  const remaining = Math.max(0, 90000 - (performance.now() - recallStartedAt));
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
    const response = await fetch(`${apiUrl}/api/demo/score`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: session.session_id, presented_words: condition.words, response: rawResponse, condition: condition.name, trial_number: condition.trial_number, timing: { display_ms: condition.display_ms, post_task: condition.post_task }, task_data: { submissions: recalledWords } }),
    });
    if (!response.ok) throw new Error();
    showConditionComplete();
  } catch {
    showError('The response could not be saved. Check that the Python backend is running.');
  }
}

function showConditionComplete() {
  const isLast = conditionIndex === session.conditions.length - 1;
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Condition complete</p><h1>Thank you.</h1><p class="intro small">Your response has been saved.</p><button type="button" id="next-button">${isLast ? 'Take a 2-minute break' : 'Continue'}</button></section>`;
  document.querySelector('#next-button').addEventListener('click', () => {
    if (isLast) showBreakBeforeSerial();
    else { conditionIndex += 1; showRest(startCondition); }
  });
}

function showBreakBeforeSerial() {
  app.innerHTML = `<section class="panel centered"><p class="kicker">Free recall complete</p><h1>Take a 2-minute break.</h1><p class="intro small">The serial-recall experiment will begin afterwards.</p><div class="break-timer" id="break-timer">2:00</div><button type="button" id="begin-serial-button">Begin serial recall</button></section>`;
  let secondsLeft = 120;
  const breakTimer = window.setInterval(() => {
    secondsLeft -= 1;
    const timerElement = document.querySelector('#break-timer');
    if (timerElement) timerElement.textContent = `${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, '0')}`;
    if (secondsLeft === 0) window.clearInterval(breakTimer);
  }, 1000);
  document.querySelector('#begin-serial-button').addEventListener('click', () => {
    window.clearInterval(breakTimer);
    startSerialPilot();
  });
  addSkipButton(() => {
    window.clearInterval(breakTimer);
    startSerialPilot();
  });
}

function showConditionResult(result) {
  const condition = session.conditions[conditionIndex];
  const isLast = conditionIndex === session.conditions.length - 1;
  app.innerHTML = `
    <section class="panel narrow results">
      <p class="kicker">Condition complete</p>
      <h1>You remembered <strong>${result.recalled_count}</strong> of ${result.total_words}.</h1>
      <div class="score-grid"><div><span>Beginning</span><strong>${result.position_groups.primacy.recalled}/5</strong></div><div><span>Middle</span><strong>${result.position_groups.middle.recalled}/5</strong></div><div><span>End</span><strong>${result.position_groups.recency.recalled}/5</strong></div></div>
      <button type="button" id="next-button">${isLast ? 'Finish pilot' : 'Rest and continue'}</button>
    </section>
  `;
  document.querySelector('#next-button').addEventListener('click', () => {
    if (isLast) showComplete();
    else {
      conditionIndex += 1;
      showRest(startCondition);
    }
  });
}

function showRest(next) {
  app.innerHTML = `<section class="panel centered"><p class="kicker">Take a short rest</p><h1>Ready for the next condition?</h1><p class="muted">Take at least 30 seconds if you need it.</p><button type="button" id="rest-button">Continue</button></section>`;
  document.querySelector('#rest-button').addEventListener('click', next);
  addSkipButton(next);
}

function showComplete() {
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Pilot complete</p><h1>Thank you.</h1><p class="intro small">Your free-recall and serial-recall records have been saved. You can close this window.</p></section>`;
}

function showLoading(message) {
  app.innerHTML = `<section class="panel centered"><p class="kicker">${message}</p><div class="loader"></div></section>`;
}

function showError(message) {
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Something went wrong</p><h1>We could not continue.</h1><p class="intro small">${message}</p><button type="button" id="retry-button">Try again</button></section>`;
  document.querySelector('#retry-button').addEventListener('click', showWelcome);
}

showWelcome();
