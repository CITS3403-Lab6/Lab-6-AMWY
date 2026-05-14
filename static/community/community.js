const storedUsername = localStorage.getItem("hw-username");
const welcomeName = document.getElementById("welcome-name");

if (storedUsername && welcomeName) {
  welcomeName.textContent = `${storedUsername}'s community`;
}

const partnerCards = document.querySelectorAll(".partner-card");
const inviteBtn = document.getElementById("invite-btn");
const inviteStatus = document.getElementById("invite-status");
const partnerNameInput = document.getElementById("partner-name");
const partnerCodeInput = document.getElementById("partner-code");

const partyMembers = [
  { name: "Wooji", streak: 12, mode: "Warrior" },  // slot 1 — party leader
  { name: "Alex", streak: 9, mode: "Sage" },         // slot 2 — joined second
  { name: "Mia", streak: 4, mode: "Demon" },         // slot 3 — joined third
  null                                                // slot 4 — empty
];

//the following code is to replace the above after flask is connected.
//const partyMembers = await fetch('/api/circle/members').then(r => r.json());

const modeIcons = {
  Sage: "../img/icons/sage.png",
  Warrior: "../img/icons/warrior.png",
  Demon: "../img/icons/demon.png"
};

function renderParty() {
  const slots = document.querySelectorAll(".party-slot");
  slots.forEach((slot, i) => {
    const member = partyMembers[i];
    const nameEl = slot.querySelector(".slot-name");
    const statsEl = slot.querySelector(".slot-stats");
    const imgEl = slot.querySelector(".weapon-img");
    const modeEl = slot.querySelector(".slot-mode");

    if (member) {
      slot.classList.remove("empty");
      nameEl.textContent = member.name;
      statsEl.textContent = `Streak: ${member.streak} days`;
      imgEl.src = modeIcons[member.mode];
      imgEl.alt = member.mode;
      modeEl.textContent = member.mode;
    } else {
      slot.classList.add("empty");
      nameEl.textContent = "Empty";
      statsEl.textContent = "Awaiting member";
      imgEl.src = "../img/icons/Shadow.png";
      imgEl.alt = "Empty slot";
      modeEl.textContent = "—";
    }
  });
}

renderParty();

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