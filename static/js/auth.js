// ---------- SCREEN SWITCHING ----------
function showScreen(screenId) {
  const screens = ["screen-signup", "screen-login", "screen-dialogue", "screen-combat"];

  screens.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.style.display = "none";
    }
  });

  const target = document.getElementById(screenId);
  if (target) {
    target.style.display = "block";
  }
}

// ---------- BACKGROUND ----------
const backgroundImages = [
  'static/img/backgrounds/origbig.png',
  'static/img/backgrounds/origbig2.png',
  'static/img/backgrounds/origbig3.png',
  'static/img/backgrounds/origbig4.png',
];

const backGround = document.getElementById('bgLayer');
if (backGround) {
  const backgroundPick = backgroundImages[Math.floor(Math.random() * backgroundImages.length)];
  backGround.style.backgroundImage = `url('${backgroundPick}')`;
}

// ---------- TITLE INTRO ----------
const titleImages = [
  'static/img/titles/habitwise_01_lava.png',
  'static/img/titles/habitwise_02_water.png',
  'static/img/titles/habitwise_03_crystal.png',
  'static/img/titles/habitwise_04_dirt.png',
  'static/img/titles/habitwise_05_cracked.png',
];

const titleScreen = document.getElementById('screen-title');
if (titleScreen) {
  const pick = titleImages[Math.floor(Math.random() * titleImages.length)];
  titleScreen.style.backgroundImage = `url('${pick}')`;

  titleScreen.addEventListener('animationend', () => {
    titleScreen.style.display = 'none';
  });
}

const signupScreen = document.getElementById('screen-signup');
if (signupScreen) {
  signupScreen.addEventListener('animationend', () => {
    signupScreen.style.animation = 'none';
    signupScreen.style.opacity = '1';
  }, { once: true });
}

// ---------- SIGNUP ----------
function handleSignUp() {
  const username = document.getElementById("signup-username").value.trim();
  const email = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value.trim();

  if (!username || !email || !password) {
    alert("Please fill in all fields.");
    return;
  }

  localStorage.setItem("hw-username", username);
  localStorage.setItem("hw-email", email);
  localStorage.setItem("hw-password", password);

  showScreen("screen-login");
}

// ---------- LOGIN ----------
function handleLogin() {
  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value.trim();

  const savedUsername = localStorage.getItem("hw-username");
  const savedPassword = localStorage.getItem("hw-password");

  if (username === savedUsername && password === savedPassword) {
    startDialogue(username);
  } else {
    alert("Incorrect username or password.");
  }
}

// ---------- DIALOGUE ----------
let dialogues = [];
let current = 0;

function startDialogue(username) {
  dialogues = [
    { speaker: "???", text: "You're awake!" },
    { speaker: username, text: "Am I? My eyes are open, yet it's dark. But my body feels light." },
    { speaker: "???", text: "You made a choice, did you not? Most people here say they made an oath." },
    { speaker: username, text: "I did. I made an oath to become a person I can be proud of." },
    { speaker: "???", text: "Well now's the time to prove it. Stand up! There are monsters here!" },
  ];

  current = 0;

  const overlay = document.getElementById('transition-overlay');
  const bg = document.getElementById('bgLayer');
  const dialogueScreen = document.getElementById('screen-dialogue');

  overlay.classList.add('visible');

  setTimeout(() => {
    showScreen('screen-dialogue');

    if (bg) bg.style.display = 'none';
    if (dialogueScreen) dialogueScreen.classList.add('dark-bg');
    overlay.style.backgroundColor = 'black';

    setTimeout(() => {
      overlay.classList.remove('visible');

      setTimeout(() => {
        document.getElementById('dialogue-box').classList.add('visible');
        nextDialogue();
      }, 1000);

    }, 200);

  }, 1000);
}

function nextDialogue() {
  if (current < dialogues.length) {
    document.getElementById("dialogue-speaker").textContent = dialogues[current].speaker;
    document.getElementById("dialogue-text").textContent = dialogues[current].text;
    current++;
  } else {
    const overlay = document.getElementById('transition-overlay');
    const bg = document.getElementById('bgLayer');
    const dialogueScreen = document.getElementById('screen-dialogue');

    document.getElementById('dialogue-box').classList.remove('visible');

    setTimeout(() => {
      overlay.style.backgroundColor = 'black';
      overlay.classList.add('visible');

      setTimeout(() => {
        if (dialogueScreen) dialogueScreen.classList.remove('dark-bg');
        if (bg) bg.style.display = 'block';

        showScreen('screen-combat');
        overlay.style.backgroundColor = 'white';

        setTimeout(() => {
          overlay.classList.remove('visible');
        }, 200);

      }, 1000);

    }, 1000);
  }
}

// ---------- COMBAT ACTIONS ----------
function selectAction(action) {
  if (action === 'attack') {
    const overlay = document.getElementById('transition-overlay');

    overlay.style.backgroundColor = 'white';
    overlay.classList.add('visible');

    setTimeout(() => {
      overlay.classList.remove('visible');
      alert("Next page will be connected from here.");
    }, 1000);
  }

  if (action === 'analyse') {
    alert("The enemy represents resistance to change.");
  }

  if (action === 'defend') {
    alert("Discipline requires patience as well as action.");
  }

  if (action === 'help') {
    alert("Tip: Start small, but stay consistent.");
  }
}