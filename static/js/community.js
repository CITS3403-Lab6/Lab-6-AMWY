const partyMembers = [
  { name: "Wooji", streak: 12, mode: "Warrior" },  // slot 1 — party leader
  { name: "Alex", streak: 9, mode: "Sage" },         // slot 2 — joined second
  { name: "Mia", streak: 4, mode: "Demon" },         // slot 3 — joined third
  null                                                // slot 4 — empty
];

//the following code is to replace the above after flask is connected.
//const partyMembers = await fetch('/api/circle/members').then(r => r.json());

const modeIcons = {
  Sage: "/static/img/icons/sage.png",
  Warrior: "/static/img/icons/warrior.png",
  Demon: "/static/img/icons/demon.png"
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
      imgEl.src = "/static/img/icons/Shadow.png";
      imgEl.alt = "Empty slot";
      modeEl.textContent = "—";
    }
  });
}

renderParty();
