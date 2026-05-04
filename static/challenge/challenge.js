const challengeCards = document.querySelectorAll('[data-type="challenge"]');
const modeCards = document.querySelectorAll('[data-type="mode"]');

const selectedChallengeText = document.getElementById('selected-challenge');
const selectedModeText = document.getElementById('selected-mode');
const startBtn = document.getElementById('start-btn');

let selectedChallenge = localStorage.getItem('hw-challenge') || '';
let selectedMode = localStorage.getItem('hw-mode') || '';

function updateSelectionUI() {
  challengeCards.forEach(card => {
    card.classList.toggle('selected', card.dataset.value === selectedChallenge);
  });

  modeCards.forEach(card => {
    card.classList.toggle('selected', card.dataset.value === selectedMode);
  });

  selectedChallengeText.textContent = selectedChallenge || 'Not selected';
  selectedModeText.textContent = selectedMode || 'Not selected';

  startBtn.disabled = !(selectedChallenge && selectedMode);
}

challengeCards.forEach(card => {
  card.addEventListener('click', () => {
    selectedChallenge = card.dataset.value;
    localStorage.setItem('hw-challenge', selectedChallenge);
    updateSelectionUI();
  });
});

modeCards.forEach(card => {
  card.addEventListener('click', () => {
    selectedMode = card.dataset.value;
    localStorage.setItem('hw-mode', selectedMode);
    updateSelectionUI();
  });
});

startBtn.addEventListener('click', () => {
  window.location.href = 'dashboard.html';
});

updateSelectionUI();