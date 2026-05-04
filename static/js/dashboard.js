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