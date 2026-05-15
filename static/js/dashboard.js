const hpFill = document.getElementById("hp-fill");
if (hpFill && window.HP_MAX > 0) {
  hpFill.style.width = Math.round((window.HP_CURRENT / window.HP_MAX) * 100) + "%";
}

const progressBar = document.getElementById("main-progress");
const progressText = document.getElementById("main-progress-text");
const goalCount = document.getElementById("goal-count");
const taskSummary = document.getElementById("task-summary");

if (progressBar) {
  progressBar.style.width = (window.COMPLETION_PCT || 0) + "%";
}

const checks = document.querySelectorAll(".task-check");

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

document.addEventListener("DOMContentLoaded", function () {
  const level = Math.min(window.CHARACTER_STAGE || 0, 10);

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
      ? "Stage 10 — Fully revealed!"
      : `Stage ${level} — ${10 - level} stages until full reveal`;
  }

  updateAvatarReveal(level);
});

if (window.SHOW_DIALOGUE) {
  startDialogue(window.USERNAME);
}