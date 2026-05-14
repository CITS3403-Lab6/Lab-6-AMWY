const storedUsername = localStorage.getItem("hw-username");
const welcomeName = document.getElementById("welcome-name");

if (storedUsername && welcomeName) {
  welcomeName.textContent = `Welcome back, ${storedUsername}! 👋`;
}

const checks = document.querySelectorAll(".task-check");
const progressBar = document.getElementById("main-progress");
const progressText = document.getElementById("main-progress-text");
const goalCount = document.getElementById("goal-count");
const taskSummary = document.getElementById("task-summary");

function updateProgress() {
  const total = checks.length;
  const done = [...checks].filter(item => item.checked).length;
  const percent = Math.round((done / total) * 100);

  if (goalCount) goalCount.textContent = `${done} / ${total}`;
  if (taskSummary) taskSummary.textContent = `${done} of ${total} tasks complete`;
  if (progressText) progressText.textContent = `${percent}% complete`;
  if (progressBar) progressBar.style.width = `${percent}%`;
}

checks.forEach(check => {
  check.addEventListener("change", updateProgress);
});

updateProgress();

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({ behavior: "smooth" });
    }
  });
});

document.addEventListener("DOMContentLoaded", function() {
  const TOTAL_TASKS_COMPLETED = 35;
  const level = Math.min(Math.floor(TOTAL_TASKS_COMPLETED / 10), 10);

  function updateAvatarReveal(level) {
    const mask = document.getElementById("avatar-mask");
    const levelText = document.getElementById("avatar-level-text");

    const revealPercent = (level / 10) * 100;
    const maskHeight = 100 - revealPercent;

    if (mask) {
      mask.style.height = maskHeight + "%";
      mask.style.top = "auto";
      mask.style.bottom = "0";
    }
    if (levelText) levelText.textContent = level >= 10
      ? "Level 10 — Fully revealed!"
      : `Level ${level} — ${10 - level} levels until full reveal`;
  }

  updateAvatarReveal(level);

  const slider = document.getElementById("level-test-slider");
  const sliderDisplay = document.getElementById("slider-level-display");

  if (slider) {
    slider.addEventListener("input", () => {
      const testLevel = parseInt(slider.value);
      sliderDisplay.textContent = testLevel;
      updateAvatarReveal(testLevel);
    });
  }
});