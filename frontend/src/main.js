import './styles.css';

const app = document.querySelector('#app');
const apiUrl = 'http://127.0.0.1:8000';

let currentTrial;
let timer;

function showWelcome() {
  app.innerHTML = `
    <section class="panel welcome">
      <p class="eyebrow">02464 Artificial Intelligence and Human Cognition</p>
      <p class="kicker">Pilot study / free recall</p>
      <h1>How much can you bring back?</h1>
      <p class="intro">You will see 15 everyday Danish words, one at a time. Afterwards, type every word you remember.</p>
      <div class="actions">
        <button type="button" id="begin-button">I understand, begin</button>
      </div>
    </section>
  `;
  document.querySelector('#begin-button').addEventListener('click', showInstructions);
}

function showInstructions() {
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">Before we start</p>
      <h1>Keep your attention on the word.</h1>
      <ol class="instructions">
        <li>One word will appear for two seconds.</li>
        <li>Try to remember each word.</li>
        <li>When the list ends, type all the words you remember in any order.</li>
      </ol>
      <p class="muted">This pilot is anonymous. You can stop at any time.</p>
      <div class="actions">
        <button type="button" id="start-trial-button">Start trial</button>
      </div>
    </section>
  `;
  document.querySelector('#start-trial-button').addEventListener('click', startTrial);
}

async function startTrial() {
  app.innerHTML = '<section class="panel centered"><p class="kicker">Preparing trial</p><div class="loader"></div></section>';

  try {
    const response = await fetch(`${apiUrl}/api/demo/start`, { method: 'POST' });
    if (!response.ok) throw new Error('Could not start the trial.');
    currentTrial = await response.json();
    showWord(0);
  } catch (error) {
    showError('The Python backend is not running. Start it, then try again.');
  }
}

function showWord(index) {
  if (index === currentTrial.words.length) {
    showRecallForm();
    return;
  }

  app.innerHTML = `
    <section class="trial-screen">
      <p class="progress">Word ${index + 1} / ${currentTrial.words.length}</p>
      <div class="word">${currentTrial.words[index]}</div>
    </section>
  `;
  timer = window.setTimeout(() => showWord(index + 1), currentTrial.display_ms);
}

function showRecallForm() {
  window.clearTimeout(timer);
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">Recall</p>
      <h1>Which words came back?</h1>
      <p class="intro small">Type all the words you remember. Separate words with spaces, commas, or new lines.</p>
      <form id="recall-form">
        <label for="recall-response">Your remembered words</label>
        <textarea id="recall-response" rows="7" autofocus></textarea>
        <div class="form-footer">
          <span class="muted">Take your best guess.</span>
          <button type="submit">Submit recall</button>
        </div>
      </form>
    </section>
  `;
  document.querySelector('#recall-form').addEventListener('submit', submitRecall);
}

async function submitRecall(event) {
  event.preventDefault();
  const responseText = document.querySelector('#recall-response').value;
  const submitButton = event.target.querySelector('button');
  submitButton.disabled = true;
  submitButton.textContent = 'Scoring...';

  try {
    const response = await fetch(`${apiUrl}/api/demo/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ presented_words: currentTrial.words, response: responseText }),
    });
    if (!response.ok) throw new Error('Could not score the response.');
    showResults(await response.json());
  } catch (error) {
    showError('The response could not be scored. Check that the Python backend is running.');
  }
}

function showResults(result) {
  const groups = result.position_groups;
  app.innerHTML = `
    <section class="panel narrow results">
      <p class="kicker">Trial complete</p>
      <h1>You remembered <strong>${result.recalled_count}</strong> of ${result.total_words}.</h1>
      <div class="score-grid">
        <div><span>Beginning</span><strong>${groups.primacy.recalled}/${groups.primacy.total}</strong></div>
        <div><span>Middle</span><strong>${groups.middle.recalled}/${groups.middle.total}</strong></div>
        <div><span>End</span><strong>${groups.recency.recalled}/${groups.recency.total}</strong></div>
      </div>
      <p class="muted">This is a demo of one baseline trial. The full pilot will include all planned conditions.</p>
      <button type="button" id="restart-button">Run again</button>
    </section>
  `;
  document.querySelector('#restart-button').addEventListener('click', showWelcome);
}

function showError(message) {
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">Something went wrong</p>
      <h1>We could not continue.</h1>
      <p class="intro small">${message}</p>
      <button type="button" id="retry-button">Try again</button>
    </section>
  `;
  document.querySelector('#retry-button').addEventListener('click', showWelcome);
}

showWelcome();
