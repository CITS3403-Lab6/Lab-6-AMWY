const username = localStorage.getItem("hw-username") || "Adventurer";
const email = localStorage.getItem("hw-email") || "Not set";
const challenge = localStorage.getItem("hw-challenge") || "Not selected";
const mode = localStorage.getItem("hw-mode") || "Not selected";

document.getElementById("welcome-name").textContent = `${username}'s settings`;
document.getElementById("settings-username").textContent = username;
document.getElementById("settings-email").textContent = email;
document.getElementById("settings-challenge").textContent = challenge;
document.getElementById("settings-mode").textContent = mode;
document.getElementById("challenge-summary-name").textContent = challenge;
document.getElementById("challenge-summary-mode").textContent = mode;

const notifyDaily = document.getElementById("notify-daily");
const notifyStreak = document.getElementById("notify-streak");
const notifyCommunity = document.getElementById("notify-community");
const privacyShare = document.getElementById("privacy-share");
const privacyStatus = document.getElementById("privacy-status");
const themeSelect = document.getElementById("theme-select");
const saveMessage = document.getElementById("save-message");

notifyDaily.checked = localStorage.getItem("hw-notify-daily") !== "false";
notifyStreak.checked = localStorage.getItem("hw-notify-streak") !== "false";
notifyCommunity.checked = localStorage.getItem("hw-notify-community") !== "false";
privacyShare.checked = localStorage.getItem("hw-privacy-share") !== "false";
privacyStatus.checked = localStorage.getItem("hw-privacy-status") !== "false";
themeSelect.value = localStorage.getItem("hw-theme") || "dark";

function applyTheme(theme) {
  if (theme === "light") {
    document.body.classList.add("light-theme");
  } else {
    document.body.classList.remove("light-theme");
  }
}

applyTheme(themeSelect.value);

themeSelect.addEventListener("change", () => {
  applyTheme(themeSelect.value);
});

document.getElementById("save-settings-btn").addEventListener("click", () => {
  localStorage.setItem("hw-notify-daily", notifyDaily.checked);
  localStorage.setItem("hw-notify-streak", notifyStreak.checked);
  localStorage.setItem("hw-notify-community", notifyCommunity.checked);
  localStorage.setItem("hw-privacy-share", privacyShare.checked);
  localStorage.setItem("hw-privacy-status", privacyStatus.checked);
  localStorage.setItem("hw-theme", themeSelect.value);

  saveMessage.textContent = "Settings saved successfully.";
});

document.getElementById("change-challenge-btn").addEventListener("click", () => {
  window.location.href = "challenge.html";
});

document.getElementById("logout-btn").addEventListener("click", () => {
  window.location.href = "auth.html";
});