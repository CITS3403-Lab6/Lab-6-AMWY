// ---------- SCREEN SWITCHING ----------
function showScreen(screenId) {
  // Hide all screens
  const screens = ["screen-signup", "screen-login", "screen-dialogue", "screen-combat", "screen-dashboard"];
  screens.forEach(id => {
    document.getElementById(id).style.display = "none";
  });
  // Show the one we want
  document.getElementById(screenId).style.display = "block";
}
// ---------- BACKGROUND ----------
const backgroundImages = [
    'img/backgrounds/origbig.png',
    'img/backgrounds/origbig2.png',
    'img/backgrounds/origbig3.png',
    'img/backgrounds/origbig4.png',
]
const backGround = document.getElementById('bgLayer');
const backgroundPick = backgroundImages[Math.floor(Math.random() * backgroundImages.length)];
backGround.style.backgroundImage = `url('${backgroundPick}')`;


// ---------- TITLE INTRO ----------
const titleImages = [
  'img/titles/habitwise_01_lava.png',
  'img/titles/habitwise_02_water.png',
  'img/titles/habitwise_03_crystal.png',
  'img/titles/habitwise_04_dirt.png',
  'img/titles/habitwise_05_cracked.png',
];

const titleScreen = document.getElementById('screen-title');
const pick = titleImages[Math.floor(Math.random() * titleImages.length)];
titleScreen.style.backgroundImage = `url('${pick}')`;

// Remove title from layout once its animation finishes (so it doesn't block clicks)
titleScreen.addEventListener('animationend', () => {
  titleScreen.style.display = 'none';
});

const signupScreen = document.getElementById('screen-signup');
signupScreen.addEventListener('animationend', () => {
  signupScreen.style.animation = 'none';
  signupScreen.style.opacity = '1';
}, { once: true });

// ---------- SIGNUP ----------
function handleSignUp() {
  const username = document.getElementById("signup-username").value.trim();
  const email    = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value.trim();

  // Basic validation
  if (!username || !email || !password) {
    alert("Please fill in all fields.");
    return;
  }

  // Save user to localStorage
  localStorage.setItem("hw-username", username);
  localStorage.setItem("hw-email", email);
  localStorage.setItem("hw-password", password);

  // Go to login screen
  showScreen("screen-login");
}


// ---------- LOGIN ----------
function handleLogin() {
  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value.trim();

  const savedUsername = localStorage.getItem("hw-username");
  const savedPassword = localStorage.getItem("hw-password");

  if (username === savedUsername && password === savedPassword) {
    // Start the dialogue with their actual username
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
    { speaker: "???",      text: "You're awake!" },
    { speaker: username,   text: "Am I? My eyes are open, yet it's dark. But my body feels light." },
    { speaker: "???",      text: "You made a choice, did you not? Most people here say they made an oath." },
    { speaker: username,   text: "I did. I made an oath to become a person I can be proud of." },
    { speaker: "???",      text: "Well now's the time to prove it. Stand up! There are monsters here!" },
  ];
  current = 0;

  const overlay = document.getElementById('transition-overlay');

  // Step 1: Fade to white (takes 1s)
  overlay.classList.add('visible');

  setTimeout(() => {
    // Step 2: While hidden behind white overlay, swap screens
    showScreen('screen-dialogue');
    document.getElementById('bgLayer').style.display = 'none';
    document.getElementById('screen-dialogue').classList.add('dark-bg');
    overlay.style.backgroundColor = 'black';

    // Step 3: Fade out the overlay (reveals black screen)
    setTimeout(() => {
      overlay.classList.remove('visible');

      // Step 4: Once overlay is gone, fade in the dialogue box
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
    document.getElementById("dialogue-text").textContent   = dialogues[current].text;
    current++;
  } else {
    const overlay = document.getElementById('transition-overlay');

    // Step 1: Fade dialogue box out
    document.getElementById('dialogue-box').classList.remove('visible');

    setTimeout(() => {
      // Step 2: Fade to black overlay
      overlay.style.backgroundColor = 'black';
      overlay.classList.add('visible');

      setTimeout(() => {
        // Step 3: While hidden, swap to combat screen
        document.getElementById('screen-dialogue').classList.remove('dark-bg');
        document.getElementById('bgLayer').style.display = 'block';
        showScreen('screen-combat');

        // Switch overlay to white so it fades out to reveal combat
        overlay.style.backgroundColor = 'white';

        // Step 4: Fade overlay out
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

    // Step 1: Fade to white
    overlay.style.backgroundColor = 'white';
    overlay.classList.add('visible');

    setTimeout(() => {
      // Step 2: While hidden, swap to dashboard
      showScreen('screen-dashboard');

      // Step 3: Fade overlay out to reveal dashboard
      setTimeout(() => {
        overlay.classList.remove('visible');
      }, 200);

    }, 1000);
  }
}