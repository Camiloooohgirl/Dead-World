# ============================================================
# config.py — Constants, Colors, and Static Data for Dead World
# ============================================================
# All immutable configuration extracted from the main game file.
# Import with: from config import *

import os

# ========================
# SCREEN & DISPLAY
# ========================
WIDTH, HEIGHT = 1680, 1050
FPS = 60
REFERENCE_WIDTH = 1680    
REFERENCE_HEIGHT = 1050

# Resolution Presets (Name, Breite, Höhe)
RESOLUTION_PRESETS = [
    ('Sehr Niedrig', 800, 450),
    ('Niedrig', 1024, 576),
    ('Mittel', 1280, 720),
    ('Hoch', 1680, 1050),
    ('Sehr Hoch', 1920, 1080)
]

# Terminal-Font (Cascadia Code = moderner Microsoft-Monospace-Font)
TERMINAL_FONT_NAME = "cascadiacode"

# ========================
# GAME STATES
# ========================
INTRO = 0
MENU = 1
OPTIONS = 2
GAME = 3
MAP = 4
PAUSED = 5

# ========================
# COLORS — Atmospheric Post-Apocalyptic Palette
# ========================
BLACK = (8, 6, 8)
BLOOD_RED = (170, 20, 20)
DARK_RED = (90, 5, 5)
DEEP_RED = (50, 0, 0)
GRAY = (55, 50, 55)
LIGHT_GRAY = (120, 115, 120)
DARK_GRAY = (22, 18, 22)
HOVER_RED = (220, 40, 30)
GREEN = (0, 255, 0)
TERMINAL_GREEN = (60, 140, 255)
TERMINAL_DIM = (30, 70, 140)
TERMINAL_BG = (8, 10, 18)
EMBER_ORANGE = (255, 120, 30)
EMBER_DIM = (180, 70, 10)
ACCENT_GLOW = (255, 60, 40)
FOG_COLOR = (20, 18, 25)

# ========================
# KEY REPEAT TIMING (ms)
# ========================
backspace_initial_delay = 250
backspace_repeat_delay = 25
key_initial_delay = 250
key_repeat_delay = 35

# ========================
# TYPEWRITER EFFECT
# ========================
TYPEWRITER_SPEED = 1  # Millisekunden pro Zeichen (1 = extrem schnell)

# ========================
# COMBAT SYSTEM
# ========================
ZOMBIE_RESPAWN_COOLDOWN = 300  # 5 Minuten in Sekunden

# Bonus-Stats pro Fäuste-Level
FIST_LEVEL_BONUSES = {
    1: {'damage': [99, 100]},
    2: {'damage': [99, 100]},
    3: {'damage': [12, 22]},
    4: {'damage': [18, 30]},
    5: {'damage': [25, 40]}   # Max Level
}

# QTE defaults
qte_duration = 2.0  # Sekunden

# Waffen, dmg, crit_chance
weapons = {
    'ak': {'name': 'AK-47', 'type': 'ranged', 'damage': [50, 75], 'accuracy': 0.7, 'ammo': 30},
    'pistole': {'name': 'Pistole', 'type': 'ranged', 'damage': [40, 60], 'accuracy': 0.8, 'ammo': 12},
    'küchenmesser': {'name': 'Küchenmesser', 'type': 'melee', 'damage': [20, 35], 'crit_chance': 0.3},
    'kampfmesser': {'name': 'Kampfmesser', 'type': 'melee', 'damage': [25, 40], 'crit_chance': 0.35},
    'feuerlöscher': {'name': 'Feuerlöscher', 'type': 'melee', 'damage': [50, 80], 'crit_chance': 0.25},
    'fäuste': {'name': 'Fäuste', 'type': 'melee', 'damage': [99, 100], 'black_flash': 1.00},
    'baseball_schläger': {'name': 'Bassseball Schläger', 'type': 'melee', 'damage': [25, 35], 'crit_chance': 0.25},
    'axt': {'name': 'Axt', 'type': 'melee', 'damage': [35, 50], 'crit_chance': 0.3},
    'machete': {'name': 'Machete', 'type': 'melee', 'damage': [30, 45], 'crit_chance': 0.35},
}

# Essbare Items (Zork-inspiriert)
food_items = {
    'konserven': {'name': 'Konservendose', 'heal': 25, 'message': 'Du öffnest die Konservendose und isst den Inhalt. Nicht gerade ein Gourmetmahl, aber es füllt den Magen.'},
    'medkit': {'name': 'Medkit', 'heal': 50, 'message': 'Du öffnest das Medkit und versorgst deine Wunden. Schon besser.'},
    'schokoriegel': {'name': 'Schokoriegel', 'heal': 10, 'message': 'Du beißt in den alten Schokoriegel. Etwas trocken, aber der Zucker gibt dir Energie.'},
    'dosenfleisch': {'name': 'Dosenfleisch', 'heal': 30, 'message': 'Du öffnest die Dose Fleisch. Es riecht fragwürdig, schmeckt aber noch... akzeptabel.'},
    'wasser': {'name': 'Wasserflasche', 'heal': 15, 'message': 'Du trinkst die Wasserflasche in großen Zügen leer. Erfrischend.'},
    'energieriegel': {'name': 'Energieriegel', 'heal': 20, 'message': 'Du isst den Energieriegel. Kompakt und nahrhaft - genau was du brauchst.'},
    'crackers': {'name': 'Crackers', 'heal': 10, 'message': 'Du knabberst die trockenen Crackers. Nicht viel, aber besser als nichts.'},
    'apfel': {'name': 'Apfel', 'heal': 12, 'message': 'Du beißt in den Apfel. Etwas schrumpelig, aber erstaunlich saftig.'},
}

# Gegner-Datenbank
enemies = {
    'zombie': {'name': 'Toxoplasma-Zombie', 'health': 100, 'max_health': 100, 'damage': [8, 20], 'distance': 'nah'},
    'infizierter': {'name': 'Infizierter Mensch', 'health': 80, 'max_health': 80, 'damage': [8, 15], 'distance': 'mittel'}
}

# ========================
# SCORING
# ========================
SCORE_VALUES = {
    'zombie_kill': 30,
    'item_pickup': 5,
    'new_room': 2,
    'container_found': 10,
    'move': 0,  # Züge kosten keine Punkte, werden aber gezählt
}

# ========================
# PARSER SYSTEM
# ========================
KNOWN_VERBS = {
    'n', 'norden', 'nord', 'o', 'osten', 'ost', 's', 'süden', 'süd', 'sued',
    'w', 'westen', 'west', 'so', 'südosten', 'nw', 'nordwesten', 'h', 'hoch',
    'r', 'runter', 'gehe', 'nimm', 'lese', 'lies', 'lesen', 'esse', 'iss',
    'inventar', 'inv', 'i', 'schaue', 'schau', 'look', 'l', 'karte', 'map',
    'ausrüsten', 'schieße', 'schiesse', 'schlag', 'schlage', 'stich',
    'clear', 'cls', 'echo', 'time', 'whoami', 'neu',
    'hilfe', 'help', 'öffne', 'oeffne', 'schließ', 'schliess', 'lege',
    'verbose', 'ausführl', 'brief', 'kurz', 'superbrie', 'superkur', 'superkurz',
    'info', 'q', 'quit', 'beenden', 'save', 'speicher', 'speichern',
    'restore', 'laden', 'score', 'punkte', 'zeit', 'diagnose', 'd',
    'schieben', 'schieb', 'brech', 'zerhacke', '?', 'mapedit',
    'nutze', 'benutze',
}

VERBS_NEED_OBJECT = {
    'nimm': 'nehmen', 'lese': 'lesen', 'lies': 'lesen', 'lesen': 'lesen',
    'esse': 'essen', 'iss': 'essen', 'öffne': 'öffnen', 'oeffne': 'öffnen',
    'ausrüsten': 'ausrüsten', 'lege': 'legen',
    'schlag': 'schlagen', 'schlage': 'schlagen',
    'schieße': 'schießen', 'schiesse': 'schießen',
    'stich': 'stechen',
    'nutze': 'benutzen', 'benutze': 'benutzen',
}

UNKNOWN_VERB_RESPONSES = [
    "Das Wort '{verb}' kenne ich nicht.",
    "Ich weiß nicht, was '{verb}' bedeuten soll.",
    "'{verb}'? Das ist kein Befehl, den ich verstehe.",
    "Weder Mensch noch Maschine kennt den Befehl '{verb}'.",
    "Du murmelst '{verb}' vor dich hin. Nichts passiert.",
    "'{verb}' ergibt für mich keinen Sinn.",
    "Selbst in der Apokalypse versteht niemand '{verb}'.",
    "Bitte was? '{verb}' ist mir nicht bekannt.",
]

ILLOGICAL_RESPONSES = {
    'eat_weapon': [
        "Das wäre unglaublich schmerzhaft und überhaupt nicht nahrhaft.",
        "Du versuchst hineinzubeißen... Nein. Einfach nein.",
        "Dein Magen würde das nicht überleben.",
        "Das ist eine Waffe, kein Snack.",
    ],
    'eat_inedible': [
        "Das kannst du nicht essen, so verzweifelt bist du noch nicht.",
        "Das sieht nicht besonders appetitlich aus...",
        "Dein Magen protestiert schon beim Gedanken daran.",
        "Das ist definitiv nicht essbar.",
    ],
    'equip_food': [
        "Du schwingst drohend die Konserve... Nicht sehr angsteinflößend.",
        "Das ist Essen, keine Waffe. Obwohl... nein.",
        "Damit würdest du höchstens dich selbst verletzen.",
    ],
    'equip_non_weapon': [
        "Das lässt sich nicht als Waffe verwenden.",
        "Du versuchst es drohend zu schwingen. Es sieht lächerlich aus.",
        "Das ist keine Waffe.",
    ],
}

# ========================
# FILE PATHS
# ========================
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dead_world_save.json')
MAP_LAYOUT_FILE = os.path.join(os.path.dirname(__file__), 'custom_map_layout.json')
