import './styles.css';

const app = document.querySelector('#app');
const apiUrl = 'http://127.0.0.1:8000';

let session;
let conditionIndex = 0;
let timer;

function showWelcome() {
  app.innerHTML = `
    <section class="panel welcome">
      <p class="eyebrow">02464 Artificial Intelligence and Human Cognition</p>
      <p class="kicker">Pilot study</p>
      <h1>How much can you bring back?</h1>
      <p class="intro">Choose a pilot mode to try. Both modes save their results to the experiment database.</p>
      <div class="mode-buttons"><button type="button" id="free-recall-button">Free recall</button><button type="button" id="serial-recall-button">Serial recall</button></div>
    </section>
  `;
  document.querySelector('#free-recall-button').addEventListener('click', showInstructions);
  document.querySelector('#serial-recall-button').addEventListener('click', showSerialInstructions);
}

function showSerialInstructions() {
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Pilot study / serial recall</p><h1>Hold the order.</h1><ol class="instructions"><li>A sequence of digits will appear one at a time.</li><li>Remember the digits in their exact order.</li><li>Type the complete sequence after it disappears.</li></ol><p class="muted">The pilot has six trials, from four to nine digits.</p><button type="button" id="start-serial-button">Start serial recall</button></section>`;
  document.querySelector('#start-serial-button').addEventListener('click', startSerialPilot);
}

async function startSerialPilot() {
  showLoading('Preparing serial recall');
  try {
    const response = await fetch(`${apiUrl}/api/serial/start`, { method: 'POST' });
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
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Serial recall · Trial ${conditionIndex + 1} / ${session.trials.length}</p><h1>${trial.length} digits.</h1><p class="intro small">Focus on the order. The digits will appear once.</p><button type="button" id="continue-serial-button">Continue</button></section>`;
  document.querySelector('#continue-serial-button').addEventListener('click', runSerialSequence);
}

function runSerialSequence() {
  const trial = session.trials[conditionIndex];
  showDigit(0, trial);
}

function showDigit(index, trial) {
  if (index === trial.sequence.length) {
    showSerialRecallForm();
    return;
  }
  app.innerHTML = `<section class="trial-screen"><p class="progress">Serial recall · Digit ${index + 1} / ${trial.length}</p><div class="word">${trial.sequence[index]}</div></section>`;
  timer = window.setTimeout(() => showSerialBlank(index, trial), session.display_ms);
}

function showSerialBlank(index, trial) {
  if (index === trial.sequence.length - 1) {
    showSerialRecallForm();
    return;
  }
  app.innerHTML = '<section class="trial-screen"></section>';
  timer = window.setTimeout(() => showDigit(index + 1, trial), session.interval_ms);
}

function showSerialRecallForm() {
  window.clearTimeout(timer);
  const trial = session.trials[conditionIndex];
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Serial recall · ${trial.length} digits</p><h1>Enter the sequence.</h1><p class="intro small">Type the digits in the order you saw them.</p><form id="serial-form"><label for="serial-response">Your sequence</label><input id="serial-response" inputmode="numeric" autocomplete="off" maxlength="12" autofocus /><div class="form-footer"><span class="muted">Digits only.</span><button type="submit">Submit sequence</button></div></form></section>`;
  document.querySelector('#serial-form').addEventListener('submit', submitSerialRecall);
}

async function submitSerialRecall(event) {
  event.preventDefault();
  const trial = session.trials[conditionIndex];
  const responseText = document.querySelector('#serial-response').value;
  const response = await fetch(`${apiUrl}/api/serial/score`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id, presented_sequence: trial.sequence, response: responseText, trial_number: trial.trial_number }) });
  if (!response.ok) { showError('The sequence could not be saved. Check that the Python backend is running.'); return; }
  showSerialResult(await response.json());
}

function showSerialResult(result) {
  const isLast = conditionIndex === session.trials.length - 1;
  app.innerHTML = `<section class="panel narrow results"><p class="kicker">Trial complete</p><h1>${result.positional_matches} of ${result.presented_length} positions correct.</h1><div class="score-grid"><div><span>Accuracy</span><strong>${Math.round(result.positional_accuracy * 100)}%</strong></div><div><span>Omissions</span><strong>${result.omissions}</strong></div><div><span>Errors</span><strong>${result.substitutions}</strong></div></div><button type="button" id="serial-next-button">${isLast ? 'Finish pilot' : 'Next trial'}</button></section>`;
  document.querySelector('#serial-next-button').addEventListener('click', () => { if (isLast) showComplete(); else { conditionIndex += 1; showSerialConditionIntro(); } });
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
    const response = await fetch(`${apiUrl}/api/pilot/start`, { method: 'POST' });
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
  const condition = session.conditions[conditionIndex];
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">${condition.label} · Recall</p>
      <h1>Which words came back?</h1>
      <p class="intro small">Type all the words you remember. Separate words with spaces, commas, or new lines.</p>
      <form id="recall-form">
        <label for="recall-response">Your remembered words</label>
        <textarea id="recall-response" rows="7" autofocus></textarea>
        <div class="form-footer"><span class="muted">Take your best guess.</span><button type="submit">Submit recall</button></div>
      </form>
    </section>
  `;
  document.querySelector('#recall-form').addEventListener('submit', submitRecall);
}

async function submitRecall(event) {
  event.preventDefault();
  const responseText = document.querySelector('#recall-response').value;
  const condition = session.conditions[conditionIndex];
  const submitButton = event.target.querySelector('button');
  submitButton.disabled = true;
  submitButton.textContent = 'Saving...';
  try {
    const response = await fetch(`${apiUrl}/api/demo/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: session.session_id,
        presented_words: condition.words,
        response: responseText,
        condition: condition.name,
        trial_number: condition.trial_number,
        timing: { display_ms: condition.display_ms, post_task: condition.post_task },
      }),
    });
    if (!response.ok) throw new Error();
    showConditionResult(await response.json());
  } catch {
    showError('The response could not be saved. Check that the Python backend is running.');
  }
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
}

function showComplete() {
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Pilot complete</p><h1>Thank you.</h1><p class="intro small">Your four trial records have been saved. You can close this window.</p></section>`;
}

function showLoading(message) {
  app.innerHTML = `<section class="panel centered"><p class="kicker">${message}</p><div class="loader"></div></section>`;
}

function showError(message) {
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Something went wrong</p><h1>We could not continue.</h1><p class="intro small">${message}</p><button type="button" id="retry-button">Try again</button></section>`;
  document.querySelector('#retry-button').addEventListener('click', showWelcome);
}

showWelcome();
