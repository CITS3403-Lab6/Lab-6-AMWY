# to become the new difficulty constants
VALID_MINDSET_TYPES = {
    "Sage": {
        "name": "Sage - Think & Reflect",
        "description": "Mindful and balanced. Must complete at least 50% of tasks.",
        "min_completion_percentage": 50,
    },
    "Warrior": {
        "name": "Warrior - Act & Execute",
        "description": "Disciplined and driven. Must complete at least 75% of tasks.",
        "min_completion_percentage": 75,
    },
    "Demon": {
        "name": "Demon - Embrace Chaos",
        "description": "Ambitious and relentless. Must complete at least 90% of tasks.",
        "min_completion_percentage": 90,
    },
}

CHARACTER_REVEAL_LEVELS = {
    1: {
        "stage": "0",
        "name": "Beginning",
        "description": "Blind and unsure, all you have is your imagination.",

    },
    10: {
        "stage": "1",
        "name": "End of the Beginning",
        "description": "Something is in sight! Something...",
    },
    20: {
        "stage": "2",
        "name": "Sight?",
        "description": "Something is in view...",
    },
    30: {
        "stage": "3",
        "name": "Who is it?",
        "description": "Someone is there...or something?...",
    },
    40: {
        "stage": "4",
        "name": "It seems inhumane...",
        "description": "Unsure of who it may resemble...",
    },
    50: {
        "stage": "5",
        "name": "Curious...and fearful.",
        "description": "It doesn't seem like a person...what is it?",
    },
    60: {
        "stage": "6",
        "name": "Curious...",
        "description": "It's quiet...",
    },
    70: {
        "stage": "7",
        "name": "Grace",
        "description": "Silent, yet a scent of beauty...",
    },
    80: {
        "stage": "8",
        "name": "Beauty",
        "description": "A rose...swaying with the wind.",
    },
    90: {
        "stage": "9",
        "name": "It speaks.",
        "description": "It is not dead, nor is it alive, yet it whispers something...",
    },
    100: {
        "stage": "10",
        "name": "Answer",
        "description": "Finally, I can understand it.",
    },
}


TASK_XP_REWARD = 10
LEVEL_XP_MULTIPLIER = 100

MAX_TASK_TITLE_LENGTH = 200
MAX_REFLECTION_LENGTH = 1000
MAX_USERNAME_LENGTH = 80
MAX_EMAIL_LENGTH = 120
MAX_PASSWORD_MIN_LENGTH = 6

MAX_HP_PER_LEVEL = 10
BASE_HP = 50

PLACEHOLDER_MAX_HP = 100
PLACEHOLDER_CURRENT_HP = 100

