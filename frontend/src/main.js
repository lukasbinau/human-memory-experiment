import './styles.css';

const app = document.querySelector('#app');

app.innerHTML = `
  <section class="welcome">
    <p class="eyebrow">02464 Artificial Intelligence and Human Cognition</p>
    <h1>Human Memory Experiment</h1>
    <p class="intro">The pilot app will be built one clear step at a time.</p>
    <button type="button" id="start-button">Start pilot</button>
  </section>
`;

document.querySelector('#start-button').addEventListener('click', () => {
  app.querySelector('.intro').textContent = 'The experiment flow starts here.';
});
