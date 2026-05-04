const storedUsername = localStorage.getItem("hw-username");
const welcomeName = document.getElementById("welcome-name");

if (storedUsername && welcomeName) {
  welcomeName.textContent = `${storedUsername}'s community`;
}

const filterButtons = document.querySelectorAll(".filter-btn");
const partnerCards = document.querySelectorAll(".partner-card");
const toolbarNote = document.getElementById("toolbar-note");
const actionLog = document.getElementById("action-log");
const inviteBtn = document.getElementById("invite-btn");
const inviteStatus = document.getElementById("invite-status");
const partnerNameInput = document.getElementById("partner-name");
const partnerCodeInput = document.getElementById("partner-code");

function setToolbarText(filter) {
  if (filter === "all") toolbarNote.textContent = "Showing all accountability partners";
  if (filter === "complete") toolbarNote.textContent = "Showing partners who completed today";
  if (filter === "support") toolbarNote.textContent = "Showing partners who may need support";
}

filterButtons.forEach(button => {
  button.addEventListener("click", () => {
    filterButtons.forEach(btn => btn.classList.remove("active"));
    button.classList.add("active");

    const filter = button.dataset.filter;
    setToolbarText(filter);

    partnerCards.forEach(card => {
      const status = card.dataset.status;

      if (filter === "all") {
        card.style.display = "flex";
      } else if (filter === "complete" && status === "complete") {
        card.style.display = "flex";
      } else if (filter === "support" && status === "support") {
        card.style.display = "flex";
      } else {
        card.style.display = "none";
      }
    });
  });
});

function addLogItem(message) {
  if (actionLog.querySelector(".empty-log")) {
    actionLog.innerHTML = "";
  }

  const item = document.createElement("div");
  item.className = "log-item";
  item.textContent = message;
  actionLog.prepend(item);
}

document.querySelectorAll("[data-action]").forEach(button => {
  button.addEventListener("click", () => {
    const action = button.dataset.action;
    const name = button.dataset.name;

    if (action === "support") {
      addLogItem(`You sent support to ${name}.`);
    }

    if (action === "nudge") {
      addLogItem(`You sent a gentle nudge to ${name}.`);
    }

    if (action === "view") {
      addLogItem(`You viewed ${name}'s recent progress.`);
    }
  });
});

inviteBtn.addEventListener("click", () => {
  const name = partnerNameInput.value.trim();
  const code = partnerCodeInput.value.trim();

  if (!name || !code) {
    inviteStatus.textContent = "Please fill in both fields.";
    inviteStatus.style.color = "#f0a86b";
    return;
  }

  inviteStatus.textContent = `Invite sent to ${name}.`;
  inviteStatus.style.color = "#8fd7a2";

  partnerNameInput.value = "";
  partnerCodeInput.value = "";
});