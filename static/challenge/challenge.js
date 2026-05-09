const modeCards = document.querySelectorAll('[data-type="mode"]');
const selectedModeText = document.getElementById('selected-mode');
const selectedTargetText = document.getElementById('selected-target');
const startBtn = document.getElementById('start-btn');

const targets = {
  Sage: '50% of tasks',
  Warrior: '70% of tasks',
  Demon: '90% of tasks'
};

let selectedMode = localStorage.getItem('hw-mode') || '';

function updateSelectionUI() {
  modeCards.forEach(card => {
    card.classList.toggle('selected', card.dataset.value === selectedMode);
  });

  selectedModeText.textContent = selectedMode || 'Not selected';
  selectedTargetText.textContent = selectedMode ? targets[selectedMode] : '—';
  startBtn.disabled = !selectedMode;
}

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