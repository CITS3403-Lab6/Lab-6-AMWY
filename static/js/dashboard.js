document.addEventListener("DOMContentLoaded", function () {
  const hpFill = document.getElementById("hp-fill");

  const hpCurrent = Number(window.HP_CURRENT || 0);
  const hpMax = Number(window.HP_MAX || 0);

  if (hpFill && hpMax > 0) {
    const hpPercent = Math.round((hpCurrent / hpMax) * 100);
    hpFill.style.width = `${Math.max(0, Math.min(100, hpPercent))}%`;
  }

  const progressBar = document.getElementById("main-progress");
  const progressText = document.getElementById("main-progress-text");
  const goalCount = document.getElementById("goal-count");
  const taskSummary = document.getElementById("task-summary");

  const completionPercent = Number(window.COMPLETION_PCT || 0);

  if (progressBar) {
    const safeCompletion = Math.max(0, Math.min(100, completionPercent));
    progressBar.style.width = `${safeCompletion}%`;
  }

  const checks = document.querySelectorAll(".task-check");

  function updateProgress() {
    const total = checks.length;
    const done = [...checks].filter(item => item.checked).length;
    const percent = total > 0 ? Math.round((done / total) * 100) : 0;

    if (goalCount) {
      goalCount.textContent = `${done} / ${total}`;
    }

    if (taskSummary) {
      taskSummary.textContent = `${done} of ${total} tasks complete`;
    }

    if (progressText) {
      progressText.textContent = `${percent}% complete`;
    }

    if (progressBar) {
      progressBar.style.width = `${percent}%`;
    }
  }

  checks.forEach(check => {
    check.addEventListener("change", updateProgress);
  });

  updateProgress();

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (event) {
      event.preventDefault();

      const target = document.querySelector(this.getAttribute("href"));

      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  const stage = Math.max(0, Math.min(10, Number(window.CHARACTER_STAGE || 0)));

  const revealValue = Number(window.CHARACTER_REVEAL_PERCENT);

  const rawRevealPercent = Number.isFinite(revealValue)
    ? Math.max(0, Math.min(100, revealValue))
    : Math.max(0, Math.min(100, stage * 10));

  const revealPercent = rawRevealPercent > 0
    ? Math.max(15, rawRevealPercent)
    : 0;

  const mask = document.getElementById("avatar-mask");
  const levelText = document.getElementById("avatar-level-text");

  const maskHeight = 100 - revealPercent;

  if (mask) {
    mask.style.height = `${maskHeight}%`;
    mask.style.top = "auto";
    mask.style.bottom = "0";
  }

  if (levelText) {
    if (revealPercent >= 100) {
    levelText.textContent = "Unmasked Stage — Fully revealed!";
  } else {
    levelText.textContent = `Unmasked Stage — ${revealPercent}% revealed`;
  }
}

  if (window.SHOW_DIALOGUE && typeof startDialogue === "function") {
    startDialogue(window.USERNAME);
  }
});