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

async function setTrialPhase(trialNumber, phase) {
  const response = await fetch(`${apiUrl}/api/v2/trial/phase`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: session.session_id, trial_number: trialNumber, phase }),
  });
  if (!response.ok) throw new Error(`Trial phase could not be set to ${phase}.`);
  return response.json();
}

function replaceCurrentTrial(trial) {
  if (trial.trial_number <= 4) session.conditions[conditionIndex] = trial;
  else session.trials[conditionIndex] = trial;
}

function addSkipButton(action) {
  document.querySelector('.skip-button')?.remove();
  if (!testingMode) return;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'skip-button';
  button.textContent = 'Spring over';
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
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Stop eksperimentet</p><h1>Vil du stoppe nu?</h1><p class="intro small">Hvis du stopper, bliver dine færdige svar gemt, men der indsamles ikke flere svar. Hvis du fortsætter, vender du tilbage til begyndelsen af det aktuelle trin.</p><div class="stop-actions"><button type="button" id="stop-confirm-no">Nej, fortsæt</button><button type="button" id="stop-confirm-yes" class="secondary-button">Ja, stop</button></div></section>`;
  document.querySelector('#stop-confirm-yes').addEventListener('click', endSessionStopped);
  document.querySelector('#stop-confirm-no').addEventListener('click', () => {
    showStopControl();
    resumeAction();
  });
}

function endSessionStopped() {
  hideStopControl();
  if (!timingTestMode) window.localStorage.removeItem(activeSessionKey);
  app.innerHTML = '<section class="panel narrow"><p class="kicker">Eksperimentet er stoppet</p><h1>Tak for din deltagelse.</h1><p class="intro small">Du stoppede eksperimentet før tid. De svar, du allerede har indsendt, er gemt. Du kan lukke vinduet.</p></section>';
}

function showWelcome() {
  hideStopControl();
  app.innerHTML = `
    <section class="panel welcome loading-screen">
      <div class="loading-mark" aria-hidden="true"></div>
      <p class="eyebrow">02464 Artificial Intelligence and Human Cognition</p>
      <p class="kicker">Undersøgelse af menneskets hukommelse</p>
      <h1>Hukommelseseksperiment</h1>
      <p class="intro">Du skal gennemføre 11 forsøg med danske ord og bogstaver.</p>
      <ul class="consent-summary">
        <li>Det tager cirka 15 minutter. Gennemfør det et roligt sted uden afbrydelser.</li>
        <li>Dit navn og dine svar gemmes sammen til projektets analyse.</li>
        <li>Det er frivilligt at deltage. Du kan stoppe når som helst uden konsekvenser.</li>
      </ul>
      <form id="welcome-form" class="welcome-form">
        <label for="participant-name">Dit navn</label>
        <input id="participant-name" name="participant-name" type="text" maxlength="80" autocomplete="name" placeholder="Skriv dit fulde navn" required />
        <label class="consent-check" for="participant-consent"><input id="participant-consent" type="checkbox" required /><span>Jeg har læst informationen og accepterer at deltage.</span></label>
        <button type="submit">Acceptér og fortsæt</button>
      </form>
    </section>
  `;
  window.setTimeout(() => document.querySelector('.loading-mark')?.remove(), 500);
  document.querySelector('#welcome-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const nameInput = document.querySelector('#participant-name');
    participantCode = nameInput.value.trim();
    if (!participantCode) {
      nameInput.setCustomValidity('Skriv dit navn for at fortsætte.');
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
      <p class="kicker">Tidstest med ord</p>
      <h1>Sammenlign visningstider.</h1>
      <p class="intro">Vælg et par af tider, og prøv to ordlister ad gangen. Du kan vende tilbage til menuen og sammenligne så mange par, du vil.</p>
      <form id="timing-welcome-form" class="welcome-form">
        <label for="participant-name">Dit navn</label>
        <input id="participant-name" name="participant-name" maxlength="80" autocomplete="name" placeholder="Skriv dit fulde navn" required />
        <p class="muted">Dette er en separat tidstest og indgår ikke i analysen af hovedeksperimentet.</p>
        <button type="submit">Start tidstesten</button>
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
      <p class="kicker">Inden vi begynder</p>
      <h1>Vælg, hvad du vil sammenligne.</h1>
      <ol class="instructions">
        <li>Vælg et af de ti tidspar i menuen.</li>
        <li>Du får vist to forskellige lister med 15 ord.</li>
        <li>Rækkefølgen af de to hastigheder er tilfældig og skjult.</li>
        <li>Efter begge lister kan du vælge et nyt par eller afslutte.</li>
      </ol>
      <button type="button" id="start-timing-button">Vælg tidspar</button>
    </section>
  `;
  document.querySelector('#start-timing-button').addEventListener('click', startTimingTest);
}

async function startTimingTest() {
  showLoading('Forbereder tidstesten');
  try {
    const response = await fetch(`${apiUrl}/api/timing-test/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ participant_code: participantCode }) });
    if (!response.ok) throw new Error();
    session = await response.json();
    showTimingPairMenu();
  } catch {
    showError('Tidstesten kunne ikke startes. Kontrollér forbindelsen, og prøv igen.');
  }
}

function formatSeconds(displayMs) {
  const seconds = displayMs / 1000;
  return `${seconds} ${seconds === 1 ? 'sekund' : 'sekunder'}`;
}

function showTimingPairMenu() {
  resumeAction = showTimingPairMenu;
  showStopControl();
  app.innerHTML = `
    <section class="panel timing-menu">
      <p class="kicker">Tidstest med ord</p>
      <h1>Vælg et tidspar.</h1>
      <p class="intro small">Hver sammenligning består af to lister med 15 ord i tilfældig rækkefølge.</p>
      <div class="timing-pair-grid">
        ${session.pairs.map((pair) => `<button type="button" class="timing-pair-button" data-pair-id="${pair.id}"><span>${formatSeconds(pair.first_ms)}</span><strong>vs.</strong><span>${formatSeconds(pair.second_ms)}</span></button>`).join('')}
      </div>
      <p class="muted">Du kan prøve hvert par igen. Luk siden, når du er færdig.</p>
    </section>
  `;
  document.querySelectorAll('.timing-pair-button').forEach((button) => button.addEventListener('click', () => startTimingPair(button.dataset.pairId)));
}

async function startTimingPair(pairId) {
  showLoading('Forbereder sammenligningen');
  try {
    const response = await fetch(`${apiUrl}/api/timing-test/pair`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id, pair_id: pairId }) });
    if (!response.ok) throw new Error();
    const comparison = await response.json();
    session.conditions = comparison.conditions;
    session.activePairId = comparison.pair_id;
    conditionIndex = 0;
    startCondition();
  } catch {
    showError('Tidsparret kunne ikke forberedes. Kontrollér forbindelsen, og prøv igen.');
  }
}

async function showSerialConditionIntro() {
  resumeAction = showSerialConditionIntro;
  showStopControl();
  showLoading('Forbereder forsøget');
  let trial;
  try {
    trial = await setTrialPhase(session.trials[conditionIndex].trial_number, 'intro');
    replaceCurrentTrial(trial);
  } catch {
    showError('Forsøget kunne ikke forberedes. Kontrollér forbindelsen, og prøv igen.');
    return;
  }
  const taskText = {
    articulatory_suppression: `<p>Du får vist ${trial.length} bogstaver ét ad gangen.</p><p>Når det første bogstav vises, skal du begynde at sige “la-la-la” højt. Fortsæt uden pause, mens alle bogstaverne vises, og stop, når svarfeltet kommer frem.</p><p>Husk bogstaverne, og skriv dem i den rækkefølge, de blev vist.</p>`,
    finger_tapping: `<p>Du får vist ${trial.length} bogstaver ét ad gangen.</p><p>Når det første bogstav vises, skal du begynde at trykke på mellemrumstasten i en jævn rytme. Fortsæt, mens alle bogstaverne vises, og stop, når svarfeltet kommer frem.</p><p>Husk bogstaverne, og skriv dem i den rækkefølge, de blev vist.</p>`,
    grouped: '<p>Du får vist tre danske ord ét ad gangen. Hvert ord består af tre bogstaver og vises i 2 sekunder.</p><p>Tilsammen indeholder ordene ni bogstaver. Husk alle ni bogstaver i den viste rækkefølge.</p>',
    baseline_6: '<p>Du får vist 6 bogstaver ét ad gangen.</p><p>Hvert bogstav vises i 2 sekunder med en kort pause imellem. Husk dem i den viste rækkefølge.</p>',
    baseline_7: '<p>Du får vist 7 bogstaver ét ad gangen.</p><p>Hvert bogstav vises i 2 sekunder med en kort pause imellem. Husk dem i den viste rækkefølge.</p>',
    baseline_8: '<p>Du får vist 8 bogstaver ét ad gangen.</p><p>Hvert bogstav vises i 2 sekunder med en kort pause imellem. Husk dem i den viste rækkefølge.</p>',
    baseline_9: '<p>Du får vist 9 bogstaver ét ad gangen.</p><p>Hvert bogstav vises i 2 sekunder med en kort pause imellem. Husk dem i den viste rækkefølge.</p>',
  }[trial.condition];
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Bogstaver i rækkefølge · Forsøg ${trial.trial_number} af ${totalMainTrials}</p><h1>Husk ${trial.length} bogstaver.</h1><div class="intro small">${taskText}</div><p class="muted instruction-note">Efter visningen har du ${session.settings?.serial_response_seconds || 30} sekunder til at svare. Dit svar indsendes automatisk, når tiden er gået.</p><button type="button" id="continue-serial-button">Start forsøget</button></section>`;
  document.querySelector('#continue-serial-button').addEventListener('click', runSerialSequence);
  addSkipButton(runSerialSequence);
}

async function runSerialSequence() {
  const trial = session.trials[conditionIndex];
  try {
    replaceCurrentTrial(await setTrialPhase(trial.trial_number, 'presentation'));
  } catch {
    showError('Forsøget kunne ikke startes. Kontrollér forbindelsen, og prøv igen.');
    return;
  }
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
  document.querySelector('.progress').textContent = `Bogstaver i rækkefølge · Forsøg ${trial.trial_number} af ${totalMainTrials}`;
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

async function showSerialRecallForm() {
  window.clearTimeout(timer);
  document.querySelector('.skip-button')?.remove();
  let trial = session.trials[conditionIndex];
  try {
    trial = await setTrialPhase(trial.trial_number, 'response');
    replaceCurrentTrial(trial);
  } catch {
    showError('Svarfeltet kunne ikke åbnes. Kontrollér forbindelsen, og prøv igen.');
    return;
  }
  const responseSeconds = session.settings?.serial_response_seconds || 30;
  serialRecallStartedAt = performance.now();
  serialRecallFinishing = false;
  app.innerHTML = `<section class="panel narrow"><div class="recall-header"><p class="kicker">Bogstaver i rækkefølge · Forsøg ${trial.trial_number} af ${totalMainTrials}</p><div class="countdown"><span>Tid tilbage</span><strong id="serial-countdown">0:${String(responseSeconds).padStart(2, '0')}</strong></div></div><h1>Skriv bogstaverne.</h1><p class="intro small">Skriv kun de bogstaver, du kan huske, i den rækkefølge de blev vist. Du må gerne skrive færre bogstaver. Undgå at gætte.</p><form id="serial-form"><label for="serial-response">De bogstaver, du kan huske</label><input id="serial-response" inputmode="text" autocomplete="off" autocapitalize="characters" maxlength="30" autofocus /><div class="form-footer"><span class="muted">Dit svar indsendes automatisk, når tiden er gået.</span><button type="submit">Indsend svar</button></div></form></section>`;
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
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Bogstaver i rækkefølge · Forsøg 9 af ${totalMainTrials}</p><h1>Et hurtigt spørgsmål.</h1><p class="intro small">Sagde du “la-la-la” under hele visningen af bogstaverne?</p><div class="stop-actions"><button type="button" data-compliance="true">Ja</button><button type="button" data-compliance="false" class="secondary-button">Nej</button></div></section>`;
  document.querySelectorAll('[data-compliance]').forEach((button) => button.addEventListener('click', () => sendSerialResponse(submission, button.dataset.compliance === 'true')));
}

async function sendSerialResponse({ trial, responseText, responseMs }, suppressionConfirmed) {
  showLoading('Gemmer dit svar');
  const response = await fetch(`${apiUrl}/api/v2/serial-score`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id, presented_sequence: trial.sequence, response: responseText, trial_number: trial.trial_number, condition: trial.condition, experiment_part: trial.part, timing: { presentation_units: trial.presentation_units, unit_display_ms: trial.unit_display_ms, intervals: trial.intervals, total_exposure_ms: trial.total_exposure_ms }, task_data: { tap_count: tapTimes.length, tap_times_ms: tapTimes.map((value) => Math.max(0, Math.round(value - serialPresentationStartedAt))), suppression_confirmed: suppressionConfirmed, chunks: trial.chunks || [], response_ms: responseMs, adaptive_derivation: trial.adaptive_derivation, matched_baseline_trial_number: trial.matched_baseline_trial_number } }) });
  if (!response.ok) { showError('Dit svar kunne ikke gemmes. Kontrollér forbindelsen, og prøv igen.'); return; }
  showSerialResult();
}

function showSerialResult() {
  const isLast = conditionIndex === session.trials.length - 1;
  const trialNumber = session.trials[conditionIndex].trial_number;
  const nextLabel = isLast ? (trialNumber === 8 ? 'Fortsæt' : 'Se resultater') : 'Næste forsøg';
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Forsøg ${trialNumber} af ${totalMainTrials} er færdigt</p><h1>Dit svar er gemt.</h1><p class="intro small">Fortsæt, når du er klar.</p><button type="button" id="serial-next-button">${nextLabel}</button></section>`;
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
  showLoading('Forbereder de næste forsøg');
  const response = await fetch(`${apiUrl}/api/v2/adaptive`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.session_id }) });
  if (!response.ok) { showError('De næste forsøg kunne ikke forberedes.'); return; }
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
      <p class="kicker">Inden vi begynder</p>
      <h1>To slags hukommelsesopgaver.</h1>
      <ol class="instructions">
        <li>I den første del skal du huske ord og skrive dem i vilkårlig rækkefølge.</li>
        <li>I den anden del skal du huske bogstaver og skrive dem i den viste rækkefølge.</li>
        <li>Du får detaljerede instruktioner før hvert forsøg.</li>
        <li>Der er tid på svarene, men du må gerne afslutte før tid.</li>
      </ol>
      <p class="muted">Skriv ikke ordene eller bogstaverne ned. Du kan stoppe når som helst.</p>
      <button type="button" id="start-button">Start eksperimentet</button>
    </section>
  `;
  document.querySelector('#start-button').addEventListener('click', startFinalProtocol);
}

async function startFinalProtocol() {
  showLoading('Forbereder eksperimentet');
  try {
    const response = await fetch(`${apiUrl}/api/v2/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ participant_code: participantCode }) });
    if (!response.ok) throw new Error();
    const protocol = await response.json();
    session = { ...protocol, trials: protocol.serial_baseline_trials, conditions: protocol.free_recall_conditions };
    window.localStorage.setItem(activeSessionKey, session.session_id);
    conditionIndex = 0;
    startCondition();
  } catch {
    showError('Eksperimentet kunne ikke startes. Kontrollér forbindelsen, og prøv igen.');
  }
}

async function startCondition() {
  let condition = session.conditions[conditionIndex];
  if (!timingTestMode) {
    showLoading('Forbereder forsøget');
    try {
      condition = await setTrialPhase(condition.trial_number, 'intro');
      replaceCurrentTrial(condition);
    } catch {
      showError('Forsøget kunne ikke forberedes. Kontrollér forbindelsen, og prøv igen.');
      return;
    }
  }
  showConditionIntro(condition, runWordSequence);
}

function showConditionIntro(condition, next) {
  resumeAction = () => showConditionIntro(condition, next);
  const conditionName = timingTestMode ? `Liste ${conditionIndex + 1} / ${session.conditions.length}` : `Ord, du kan huske · Forsøg ${condition.trial_number} af ${totalMainTrials}`;
  const responseSeconds = session.settings?.free_recall_response_seconds || 90;
  const taskText = timingTestMode
    ? '<p>Du får vist 15 danske ord ét ad gangen. Skriv bagefter de ord, du kan huske, i vilkårlig rækkefølge.</p>'
    : {
      1: '<p>Du får vist 15 danske ord ét ad gangen. Hvert ord vises i 2 sekunder.</p><p>Efter det sidste ord skal du straks skrive alle de ord, du kan huske. Rækkefølgen er ligegyldig.</p>',
      2: '<p>Du får vist 15 nye danske ord ét ad gangen. Hvert ord vises i 1 sekund.</p><p>Efter det sidste ord skal du straks skrive alle de ord, du kan huske. Rækkefølgen er ligegyldig.</p>',
      3: `<p>Du får vist 15 nye danske ord ét ad gangen. Hvert ord vises i 2 sekunder.</p><p>Efter det sidste ord er der ${session.settings?.free_recall_pause_seconds || 15} sekunders ventetid. Svarfeltet åbner automatisk bagefter.</p>`,
      4: `<p>Du får vist 15 nye danske ord ét ad gangen. Hvert ord vises i 2 sekunder.</p><p>Efter det sidste ord skal du spille et kortspil i ${session.settings?.card_game_seconds || 15} sekunder. Svarfeltet åbner automatisk, når spillet slutter.</p>`,
    }[condition.trial_number];
  app.innerHTML = `
    <section class="panel narrow">
      <p class="kicker">${conditionName}</p>
      <h1>${timingTestMode ? condition.label : 'Husk 15 ord.'}</h1>
      <div class="intro small">${taskText}</div>
      <p class="muted instruction-note">Du har ${responseSeconds} sekunder til at svare og må gerne afslutte før tid. Dit svar indsendes automatisk, når tiden er gået.</p>
      <button type="button" id="continue-button">Start ${timingTestMode ? 'listen' : 'forsøget'}</button>
    </section>
  `;
  document.querySelector('#continue-button').addEventListener('click', next);
  addSkipButton(next);
}

async function runWordSequence() {
  if (!timingTestMode) {
    try {
      replaceCurrentTrial(await setTrialPhase(session.conditions[conditionIndex].trial_number, 'presentation'));
    } catch {
      showError('Forsøget kunne ikke startes. Kontrollér forbindelsen, og prøv igen.');
      return;
    }
  }
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
      <p class="progress">${timingTestMode ? `Liste ${conditionIndex + 1} / ${session.conditions.length}` : `Ord, du kan huske · Forsøg ${condition.trial_number} af ${totalMainTrials}`}</p>
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
  app.innerHTML = `<section class="trial-screen"><p class="kicker light">Ord, du kan huske · Forsøg ${session.conditions[conditionIndex].trial_number} af ${totalMainTrials}</p><div><div class="timer">${secondsLeft}</div><p class="pause-note">Svarfeltet åbner automatisk.</p></div></section>`;
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
      <p class="kicker">Ord, du kan huske · Forsøg ${session.conditions[conditionIndex].trial_number} af ${totalMainTrials} · <span id="game-timer">${secondsLeft}</span></p>
      <h1>Find kortparrene.</h1>
      <p class="intro small">Vend to kort ad gangen. Ét kort har ikke en makker.</p>
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

async function showRecallForm() {
  window.clearTimeout(timer);
  window.clearInterval(cardGameTimer);
  let condition = session.conditions[conditionIndex];
  if (!timingTestMode) {
    try {
      condition = await setTrialPhase(condition.trial_number, 'response');
      replaceCurrentTrial(condition);
    } catch {
      showError('Svarfeltet kunne ikke åbnes. Kontrollér forbindelsen, og prøv igen.');
      return;
    }
  }
  const responseSeconds = session.settings?.free_recall_response_seconds || 90;
  recalledWords = [];
  recallStartedAt = performance.now();
  recallFinishing = false;
  app.innerHTML = `
    <section class="panel narrow">
      <div class="recall-header"><p class="kicker">${timingTestMode ? `Liste ${conditionIndex + 1} / ${session.conditions.length}` : `Ord, du kan huske · Forsøg ${condition.trial_number} af ${totalMainTrials}`}</p><div class="countdown"><span>Tid tilbage</span><strong id="countdown">${Math.floor(responseSeconds / 60)}:${String(responseSeconds % 60).padStart(2, '0')}</strong></div></div>
      <h1>Skriv de ord, du kan huske.</h1>
      <p class="intro small">Skriv ét ord, og vælg Tilføj. Gentag for hvert ord. Rækkefølgen er ligegyldig, og du kan fjerne et ord igen.</p>
      <form id="recall-form">
        <div id="remembered-words" class="remembered-words" aria-live="polite"><span class="muted">Dine ord vises her.</span></div>
        <label for="recall-response">De ord, du kan huske</label>
        <div class="word-entry"><input id="recall-response" autocomplete="off" autofocus /><button type="submit" aria-label="Tilføj ord">Tilføj</button></div>
        <div class="form-footer"><span class="muted">Dit svar indsendes automatisk, når tiden er gået.</span><button type="button" id="finish-recall-button">Afslut svar</button></div>
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
  list.innerHTML = recalledWords.length ? recalledWords.map((entry, index) => `<span class="word-chip">${entry.word}<button type="button" data-index="${index}" aria-label="Fjern ${entry.word}">×</button></span>`).join('') : '<span class="muted">Dine ord vises her.</span>';
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
  const responseMs = Math.round(performance.now() - recallStartedAt);
  try {
    const scorePath = timingTestMode ? '/api/timing-test/score' : '/api/v2/free-score';
    const response = await fetch(`${apiUrl}${scorePath}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: session.session_id, presented_words: condition.words, response: rawResponse, condition: condition.name, trial_number: condition.trial_number, timing: { display_ms: condition.display_ms, post_task: condition.post_task, post_task_seconds: condition.post_task === 'pause' ? session.settings?.free_recall_pause_seconds : condition.post_task === 'card_game' ? session.settings?.card_game_seconds : 0, response_limit_seconds: session.settings?.free_recall_response_seconds }, task_data: { submissions: recalledWords, response_ms: responseMs, pair_id: session.activePairId } }),
    });
    if (!response.ok) throw new Error();
    if (timingTestMode) showTimingConditionComplete();
    else showConditionComplete();
  } catch {
    showError('Dit svar kunne ikke gemmes. Kontrollér forbindelsen, og prøv igen.');
  }
}

function showTimingConditionComplete() {
  const isLast = conditionIndex === session.conditions.length - 1;
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Liste ${conditionIndex + 1} / ${session.conditions.length} er færdig</p><h1>Dit svar er gemt.</h1><p class="intro small">${isLast ? 'Sammenligningen er færdig. Vælg et nyt par, når du er klar.' : 'Hold en kort pause før den anden liste.'}</p><button type="button" id="timing-next-button">${isLast ? 'Tilbage til tidspar' : 'Næste liste'}</button></section>`;
  document.querySelector('#timing-next-button').addEventListener('click', () => {
    if (isLast) showTimingPairMenu();
    else { conditionIndex += 1; showRest(startCondition); }
  });
}

function showConditionComplete() {
  resumeAction = showConditionComplete;
  const isLast = conditionIndex === session.conditions.length - 1;
  app.innerHTML = `<section class="panel narrow centered"><p class="kicker">Forsøg ${session.conditions[conditionIndex].trial_number} af ${totalMainTrials} er færdigt</p><h1>Dit svar er gemt.</h1><p class="intro small">Fortsæt, når du er klar.</p><button type="button" id="next-button">${isLast ? 'Fortsæt til pausen' : 'Næste forsøg'}</button></section>`;
  document.querySelector('#next-button').addEventListener('click', () => {
    if (isLast) showSectionBreak();
    else { conditionIndex += 1; showRest(startCondition); }
  });
}

function showSectionBreak() {
  let secondsLeft = session.settings?.section_break_seconds || 120;
  resumeAction = showSectionBreak;
  app.innerHTML = `<section class="panel centered"><p class="kicker">Første del er færdig</p><h1>Hold en pause.</h1><p class="intro small">Nu følger opgaver med bogstaver. Pausen varer op til to minutter, men du må fortsætte, når du er klar.</p><div class="timer" id="break-timer">${secondsLeft}</div><button type="button" id="begin-serial-button">Fortsæt til bogstaverne</button></section>`;
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
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Bogstaver i rækkefølge</p><h1>Husk bogstavernes rækkefølge.</h1><p class="intro small">Bogstaverne vises ét ad gangen. Efter hver række skal du skrive de bogstaver, du kan huske, i den viste rækkefølge. Undgå at gætte.</p><p class="muted">Du får detaljerede instruktioner før hvert forsøg.</p><button type="button" id="begin-serial-trials">Fortsæt</button></section>`;
  document.querySelector('#begin-serial-trials').addEventListener('click', showSerialConditionIntro);
  addSkipButton(showSerialConditionIntro);
}

function showRest(next) {
  resumeAction = () => showRest(next);
  app.innerHTML = `<section class="panel centered"><p class="kicker">Hold en kort pause</p><h1>Klar til næste forsøg?</h1><p class="muted">Fortsæt, når du er klar.</p><button type="button" id="rest-button">Fortsæt</button></section>`;
  document.querySelector('#rest-button').addEventListener('click', next);
  addSkipButton(next);
}

async function showComplete() {
  hideStopControl();
  showLoading('Forbereder dine resultater');
  const response = await fetch(`${apiUrl}/api/v2/${session.session_id}/results`);
  if (!response.ok) { showError('Dine resultater kunne ikke indlæses, men dine svar er stadig gemt.'); return; }
  const results = await response.json();
  window.localStorage.removeItem(activeSessionKey);
  const renderTrialRows = (section) => results.trials
    .filter((trial) => trial.section === section)
    .map((trial) => {
      const percentage = trial.total ? Math.round((trial.correct / trial.total) * 100) : 0;
      return `<li class="result-row"><div class="result-row-heading"><span>Forsøg ${trial.trial_number}</span><strong>${trial.correct} af ${trial.total}</strong></div><div class="result-bar" aria-label="Forsøg ${trial.trial_number}: ${percentage}% korrekte"><span style="width: ${percentage}%"></span></div></li>`;
    })
    .join('');
  app.innerHTML = `<section class="panel results-panel"><p class="kicker">Eksperimentet er færdigt</p><h1>Dine resultater</h1><div class="result-summary"><div><strong>${results.free_recall_recalled}<span> / ${results.free_recall_total}</span></strong><p>Ord husket</p></div><div><strong>${results.serial_positional_matches}<span> / ${results.serial_total}</span></strong><p>Bogstaver på den rigtige plads</p></div></div><div class="result-sections"><section><h2>Ord, du kunne huske</h2><p class="muted">Antal huskede ord i hvert forsøg</p><ol class="result-list">${renderTrialRows('free_recall')}</ol></section><section><h2>Bogstaver i rækkefølge</h2><p class="muted">Bogstaver på den rigtige plads i hvert forsøg</p><ol class="result-list">${renderTrialRows('serial_recall')}</ol></section></div><p class="muted result-note">Resultaterne er kun en enkel opsummering og ikke en vurdering af din hukommelse. Alle elleve svar er gemt.</p></section>`;
}

async function restoreActiveSession() {
  const sessionId = window.localStorage.getItem(activeSessionKey);
  if (!sessionId) {
    showWelcome();
    return;
  }
  showLoading('Gendanner dit eksperiment');
  try {
    const response = await fetch(`${apiUrl}/api/v2/${sessionId}/state`);
    if (!response.ok) throw new Error();
    const protocol = await response.json();
    const completed = protocol.completed_trial_numbers;
    session = { ...protocol, trials: protocol.serial_baseline_trials, conditions: protocol.free_recall_conditions };
    const recoveryResponse = await fetch(`${apiUrl}/api/v2/${sessionId}/recover`, { method: 'POST' });
    if (!recoveryResponse.ok) throw new Error();
    const activeTrial = (await recoveryResponse.json()).active_trial;
    showStopControl();
    if (completed.length === totalMainTrials) {
      await showComplete();
    } else if (activeTrial) {
      if (activeTrial.trial_number <= 4) {
        conditionIndex = activeTrial.trial_number - 1;
        replaceCurrentTrial(activeTrial);
        if (activeTrial.phase === 'response') await showRecallForm();
        else showConditionIntro(activeTrial, runWordSequence);
      } else {
        if (activeTrial.trial_number >= 9) session.trials = protocol.adaptive.trials;
        conditionIndex = activeTrial.trial_number <= 8 ? activeTrial.trial_number - 5 : activeTrial.trial_number - 9;
        replaceCurrentTrial(activeTrial);
        if (activeTrial.phase === 'response') await showSerialRecallForm();
        else await showSerialConditionIntro();
      }
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
    showError('Det gemte eksperiment kunne ikke gendannes. Start et nyt forløb for at fortsætte.');
  }
}

function showLoading(message) {
  app.innerHTML = `<section class="panel centered"><p class="kicker">${message}</p><div class="loader"></div></section>`;
}

function showError(message) {
  hideStopControl();
  app.innerHTML = `<section class="panel narrow"><p class="kicker">Der opstod en fejl</p><h1>Vi kunne ikke fortsætte.</h1><p class="intro small">${message}</p><button type="button" id="retry-button">Prøv igen</button></section>`;
  document.querySelector('#retry-button').addEventListener('click', timingTestMode ? showTimingTestWelcome : showWelcome);
}

if (timingTestMode) showTimingTestWelcome();
else restoreActiveSession();
