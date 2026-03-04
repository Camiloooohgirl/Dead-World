import pygame
import sys
import math
import random
import time
import datetime
import os
from game_map import rebuild_game_map, GAME_MAP, get_room_coord, BIOME_COLORS, BIOME_ICONS
# Pygame initialisieren
pygame.init()
pygame.mixer.init()

# Musik-System
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_MUSIC_PATH = os.path.join(BASE_DIR, "Game_music", "Ambient", "julius_galla__atmosphere-horror-2-loop.wav")
menu_music_playing = False

# Zombie Sounds - 4 zufällige Sounds beim Zombie-Auftauchen
ZOMBIE_SOUND_DIR = os.path.join(BASE_DIR, "Game_music", "Zombie Sounds")
ZOMBIE_SOUNDS = []
for _zs_file in sorted(os.listdir(ZOMBIE_SOUND_DIR)):
    if _zs_file.endswith(('.mp3', '.wav', '.ogg')):
        ZOMBIE_SOUNDS.append(pygame.mixer.Sound(os.path.join(ZOMBIE_SOUND_DIR, _zs_file)))

def play_random_zombie_sound():
    """Spielt einen zufälligen Zombie-Sound ab"""
    global _current_zombie_sound
    if ZOMBIE_SOUNDS:
        sound = random.choice(ZOMBIE_SOUNDS)
        sound.set_volume(game_settings.get('sfx_volume', 0.7))
        sound.play()
        _current_zombie_sound = sound

_current_zombie_sound = None

def stop_zombie_sounds():
    """Stoppt den aktuell spielenden Zombie-Sound"""
    global _current_zombie_sound
    if _current_zombie_sound:
        _current_zombie_sound.stop()
        _current_zombie_sound = None

# Konstanten
WIDTH, HEIGHT = 1900, 1000
FPS = 60

# Resolution Presets (Name, Breite, Höhe)
RESOLUTION_PRESETS = [
    ('Sehr Niedrig', 800, 450),
    ('Niedrig', 1024, 576),
    ('Mittel', 1280, 720),
    ('Hoch', 1600, 900),
    ('Sehr Hoch', 1920, 1080)
]
current_resolution_index = 2  # Standard: Sehr Hoch (1920x1080)
# Farben — Atmospheric Post-Apocalyptic Palette
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

# Referenz-Auflösung für Skalierung (Basis-Layout)
REFERENCE_WIDTH = 1280
REFERENCE_HEIGHT = 720

# Font-Cache für skalierte Schriften
_font_cache = {}
_last_scale_factor = None

# Terminal-Font (Cascadia Code = moderner Microsoft-Monospace-Font)
TERMINAL_FONT_NAME = "cascadiacode"

def get_scale_factor():
    """Berechnet einheitlichen Skalierungsfaktor basierend auf Fensterbreite"""
    scale_x = screen.get_width() / REFERENCE_WIDTH
    scale_y = screen.get_height() / REFERENCE_HEIGHT
    return min(scale_x, scale_y)

def scale(value):
    """Skaliert einen Wert proportional zur aktuellen Auflösung"""
    return int(value * get_scale_factor())

def scale_x(value):
    """Skaliert horizontal (für Positionen die sich mit Breite ändern)"""
    return int(value * screen.get_width() / REFERENCE_WIDTH)

def scale_y(value):
    """Skaliert vertikal (für Positionen die sich mit Höhe ändern)"""
    return int(value * screen.get_height() / REFERENCE_HEIGHT)

def scale_pos(x, y):
    """Skaliert eine Position und zentriert bei abweichendem Seitenverhältnis"""
    factor = get_scale_factor()
    offset_x = (screen.get_width() - REFERENCE_WIDTH * factor) / 2
    offset_y = (screen.get_height() - REFERENCE_HEIGHT * factor) / 2
    return (int(x * factor + offset_x), int(y * factor + offset_y))

def get_scaled_font(base_size):
    """Gibt skalierte Schrift zurück (gecacht für Performance)"""
    global _last_scale_factor
    
    current_factor = get_scale_factor()
    # Cache leeren wenn Skalierung sich geändert hat
    if _last_scale_factor != current_factor:
        _font_cache.clear()
        _last_scale_factor = current_factor
    
    scaled_size = max(12, scale(base_size))
    if scaled_size not in _font_cache:
        # Consolas = sauberer Monospace-Font, kein Artefakt-Bug
        _font_cache[scaled_size] = pygame.font.SysFont(TERMINAL_FONT_NAME, scaled_size)
    return _font_cache[scaled_size]

def clear_font_cache():
    """Leert den Font-Cache bei manueller Auflösungsänderung"""
    global _last_scale_factor
    _font_cache.clear()
    _last_scale_factor = None

# Fenster erstellen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Dead World")
clock = pygame.time.Clock()
fullscreen = False

# Fonts
font_large = pygame.font.Font(None, 120)
font_medium = pygame.font.Font(None, 80)
font_small = pygame.font.Font(None, 50)
font_terminal = pygame.font.Font(None, 30)
font_tiny = pygame.font.Font(None, 25)

# Game States
INTRO = 0
MENU = 1
OPTIONS = 2
GAME = 3
MAP = 4
MAP = 4
current_state = INTRO

# Map-System Globals (Graph View)
map_camera_x = 0
map_camera_y = 0
map_zoom = 1.0
map_target_x = 0
map_target_y = 0
map_cursor_room = None
map_dragging = False
map_drag_last_pos = (0, 0)

# Node-Dragging (Customizable Map)
node_dragging = False          # True wenn ein Node gerade gezogen wird
node_drag_key = None           # room_key des gezogenen Nodes
node_hovered_key = None        # room_key des Nodes unter der Maus
MAP_LAYOUT_FILE = os.path.join(os.path.dirname(__file__), 'custom_map_layout.json')

# Building-Dragging (Block dragging)
building_dragging = False      # True wenn ein ganzes Gebäude gezogen wird
building_drag_key = None       # building_key des gezogenen Gebäudes
building_drag_start = (0, 0)   # Graph-Koordinaten beim Start des Drags
building_drag_offsets = {}     # Relative Offsets der Nodes zum Drag-Startpunkt

# Custom Blocks (User-created annotation boxes)
custom_blocks = []             # List of {name, gx, gy, gw, gh, color}
selected_block_idx = None      # Index of selected custom block
block_resizing = False         # True wenn Block gerade resized wird
block_resize_handle = None     # 'tl','tr','bl','br','t','b','l','r'
block_moving = False           # True wenn Block gerade verschoben wird
block_move_offset = (0, 0)     # Offset beim Drag-Start
block_naming = False           # True wenn gerade ein Block-Name eingegeben wird
block_name_input = ""          # Aktueller Name-Input

visited_rooms = set()  # Besuchte Räume (zB. für Resets/Stats)

# Menü-Navigation
menu_selected_index = 0
options_selected_index = 0  # 0=Auflösung, 1=Musik, 2=Effekte

# Game Settings
game_settings = {
    'music_volume': 0.05,
    'sfx_volume': 0.05,
    'difficulty': 'Normal',
    'resolution': 2  # Index in RESOLUTION_PRESETS
}

# Text Adventure Game Data
current_room = 'start'
game_history = []
player_inventory = []
input_text = ""
cursor_position = 0  # Position des Cursors im input_text
prolog_shown = False
prolog_lines = []
prolog_line_index = 0

# Command History für Pfeiltasten
command_history = []
history_index = -1

# Backspace-Repeat
backspace_held = False
backspace_timer = 0
backspace_initial_delay = 250  # ms
backspace_repeat_delay = 25    # ms
last_backspace_time = 0

#Biblio
bibliothek_4_schrank_geschoben = False
#Haus1 Tür
haus1_tür_auf = False

# Key-Repeat für Cursor-Tasten
delete_held = False
last_delete_time = 0
left_held = False
last_left_time = 0
right_held = False
last_right_time = 0
enter_held = False
last_enter_time = 0
key_initial_delay = 250  # ms
key_repeat_delay = 35    # ms

# Scroll-System
scroll_offset = 0
max_scroll = 0

# Typewriter-Effekt System
typewriter_queue = []          # Warteschlange für Zeilen die noch getippt werden
typewriter_current_line = ""   # Die aktuelle Zeile die getippt wird
typewriter_reveal_index = 0    # Wie viele Zeichen sichtbar sind
typewriter_last_time = 0       # Letzter Zeitpunkt an dem ein Zeichen hinzugefügt wurde
TYPEWRITER_SPEED = 1           # Millisekunden pro Zeichen (1 = extrem schnell)
typewriter_active = False      # Ob gerade getippt wird

# Cached CRT-Scanline Surface (nur einmal erstellen)
_scanline_cache = None
_scanline_cache_size = (0, 0)

# Cached static surfaces (vignette, cracks) - nur bei Resize neu erstellen
_vignette_cache = None
_vignette_cache_key = (0, 0, 0)  # (w, h, intensity)
_cracks_cache = None
_cracks_cache_key = (0, 0, 0)  # (w, h, alpha)

# Pre-allokierte Partikel-Surfaces (vermeidet 50 Allokationen pro Frame)
_particle_surfaces = {}  # Cache: (size, color, alpha) -> Surface

# Cached fog circle surface
_fog_circle_cache = {}  # Cache: (radius, alpha) -> Surface
_fog_surface = None     # Reusable fog overlay surface
_fog_surface_size = (0, 0)

# Cached gradient separator surfaces
_gradient_sep_cache = None
_gradient_sep_cache_key = (0, 0, 0)  # (w, padding, color_key)

# Kampfsystem
ZOMBIE_RESPAWN_COOLDOWN = 300  # 5 Minuten in Sekunden
zombie_kill_times = {}  # room_key -> time.time() wann Zombie zuletzt getötet wurde

player_stats = {   
    'health': 100,
    'strength': 100,              # Hidden strength (0-100) – never shown as number
    'hunger': 0,                  # Hidden hunger (0-100) – never shown as number
    'max_weight': 50,             # Hidden carry capacity
    'equipped_weapon': None,
    'weapon_type': None,  # 'ranged', 'melee', None
    'in_combat': False,
    'fist_level': 1,              # Fäuste Level (1-5), Level-Up durch Black Flash
    'turns_since_last_meal': 0,   # Hunger tick counter
    'last_recovery_turn': 0,      # Passive recovery tracker
}

# === CLASSIC MECHANICS: View Mode, Score, Ambiguity ===
view_mode = 'verbose'           # 'verbose', 'brief', 'superbrief'
visited_rooms_desc = set()      # Bereits beschriebene Räume (für brief mode)
game_score = 0                  # Zork-style Punkte
game_moves = 0                  # Zähler für Spielerzüge
game_start_ticks = 0            # pygame.time.get_ticks() beim Spielstart
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dead_world_save.json')

# Pending Ambiguity (wenn der Parser fragt "Was meinst du?")
pending_ambiguity = None        # {'action': str, 'candidates': [...], 'original_cmd': str}

# === ITEM CLASS (Container-System) ===
class Item:
    """Gegenstand mit optionaler Container-Logik."""
    def __init__(self, key, name, description='',
                 is_container=False, capacity=5,
                 is_open=True, is_transparent=False,
                 weight=1, charge=-1):
        self.key = key
        self.name = name
        self.description = description
        self.is_container = is_container
        self.capacity = capacity
        self.is_open = is_open
        self.is_transparent = is_transparent
        self.contents = []          # Liste von Item-Keys
        self.weight = weight        # Gewicht für Encumbrance-System
        self.charge = charge        # -1 = kein Licht, 0+ = verbleibende Züge
        self.max_charge = charge    # Original-Ladung für Reset

# Item-Definitionen – Metadaten für jedes bekannte Item
ITEM_DEFS = {
    'feuerlöscher': Item('feuerlöscher', 'Feuerlöscher', 'Ein schwerer, roter Feuerlöscher.', weight=8),
    'zeitung': Item('zeitung', 'Zeitung', 'Eine zerknitterte Zeitung.', weight=1),
    'schlüssel': Item('schlüssel', 'Schlüssel', 'Ein rostiger Metallschlüssel.', weight=1),
    'ak': Item('ak', 'AK-47', 'Eine automatische Waffe.', weight=7),
    'notizen': Item('notizen', 'Notizen', 'Zerknitterte Labornotizen.', weight=1),
    'fäuste': Item('fäuste', 'Fäuste', 'Deine bloßen Hände.', weight=0),
    'konserven': Item('konserven', 'Konservendose', 'Eine ungeöffnete Konserve.', weight=2),
    'medkit': Item('medkit', 'Medkit', 'Ein Erste-Hilfe-Kasten.', weight=3),
    'schokoriegel': Item('schokoriegel', 'Schokoriegel', 'Ein alter Schokoriegel.', weight=1),
    'dosenfleisch': Item('dosenfleisch', 'Dosenfleisch', 'Fragwürdig riechend.', weight=2),
    'wasser': Item('wasser', 'Wasserflasche', 'Eine Flasche Wasser.', weight=2),
    'energieriegel': Item('energieriegel', 'Energieriegel', 'Kompakt und nahrhaft.', weight=1),
    'crackers': Item('crackers', 'Crackers', 'Trockene Crackers.', weight=1),
    'apfel': Item('apfel', 'Apfel', 'Ein schrumpeliger Apfel.', weight=1),
    'pistole': Item('pistole', 'Pistole', 'Eine halbautomatische Pistole.', weight=3),
    'küchenmesser': Item('küchenmesser', 'Küchenmesser', 'Ein scharfes Küchenmesser.', weight=2),
    'kampfmesser': Item('kampfmesser', 'Kampfmesser', 'Ein robustes Kampfmesser.', weight=2),
    'baseball_schläger': Item('baseball_schläger', 'Baseball Schläger', 'Ein solider Schläger.', weight=4),
    'axt': Item('axt', 'Axt', 'Eine scharfe Axt.', weight=6),
    'machete': Item('machete', 'Machete', 'Eine lange Machete.', weight=4),
    'tagebuch': Item('tagebuch', 'Tagebuch', 'Dein persönliches Tagebuch.', weight=1),
    'stück papier': Item('stück papier', 'Stück Papier', 'Ein blutiges Stück Papier.', weight=1),
    'taschenlampe': Item('taschenlampe', 'Taschenlampe', 'Eine Taschenlampe.', weight=2, charge=100),
    # --- SELTENE CONTAINER ---
    'rucksack': Item('rucksack', 'Rucksack', 'Ein robuster Militärrucksack.',
                     is_container=True, capacity=8, is_open=False, is_transparent=False, weight=3),
    'kiste': Item('kiste', 'Kiste', 'Eine schwere Holzkiste.',
                  is_container=True, capacity=5, is_open=False, is_transparent=False, weight=10),
}

def get_item_name(key):
    """Gibt den Anzeigenamen eines Items zurück."""
    it = ITEM_DEFS.get(key)
    return it.name if it else key.capitalize()

# === QUALITATIVE STATUS SYSTEM (Hidden Stats → Descriptive Text) ===

def get_health_description(hp=None):
    """Gibt eine qualitative Beschreibung des Gesundheitszustands zurück."""
    if hp is None:
        hp = player_stats['health']
    if hp >= 100:
        return "Du bist in perfekter Verfassung."
    elif hp >= 80:
        return "Du hast ein paar Kratzer, nichts Ernstes."
    elif hp >= 60:
        return "Du bist leicht verletzt."
    elif hp >= 40:
        return "Du bist deutlich angeschlagen."
    elif hp >= 20:
        return "Du bist schwer verwundet!"
    else:
        return "Du bist dem Tode nahe!"

def get_strength_description(strength=None):
    """Gibt eine qualitative Beschreibung der Stärke zurück."""
    if strength is None:
        strength = player_stats['strength']
    if strength >= 80:
        return "Du fühlst dich stark und bereit."
    elif strength >= 60:
        return "Du bist etwas erschöpft."
    elif strength >= 40:
        return "Deine Kräfte schwinden merklich."
    elif strength >= 20:
        return "Du bist am Ende deiner Kräfte!"
    else:
        return "Du kannst dich kaum noch auf den Beinen halten!"

def get_hunger_description(hunger=None):
    """Gibt eine Hungerbeschreibung zurück (oder None wenn noch harmlos)."""
    if hunger is None:
        hunger = player_stats['hunger']
    if hunger >= 80:
        return "Du fühlst dich schwach vor Hunger!"
    elif hunger >= 60:
        return "Du spürst einen nagenden Hunger."
    elif hunger >= 40:
        return "Dein Magen knurrt leise."
    return None

def get_damage_reaction(damage, current_hp):
    """Gibt eine reaktive Beschreibung zurück wenn der Spieler Schaden nimmt."""
    if damage >= 25:
        reactions = [
            "Ein brutaler Treffer! Du spürst warmes Blut an deiner Seite.",
            "Der Schmerz durchzuckt deinen ganzen Körper!",
            "Du taumelst zurück, die Wucht des Schlages raubt dir den Atem.",
        ]
    elif damage >= 15:
        reactions = [
            "Dieser Schlag hat wehgetan!",
            "Du beißt die Zähne zusammen. Das wird eine Narbe geben.",
            "Du spürst deinen Arm taub werden nach dem Treffer.",
        ]
    elif damage >= 8:
        reactions = [
            "Ein schmerzhafter Treffer, aber du hältst dich.",
            "Du zuckst zusammen, der Schmerz ist kurz aber heftig.",
            "Der Schlag tut weh, aber du kannst weiterkämpfen.",
        ]
    else:
        reactions = [
            "Ein leichter Kratzer, mehr nicht.",
            "Du spürst kaum etwas — nur ein Kratzen.",
            "Nur eine Schramme. Du schüttelst es ab.",
        ]
    # Add desperation when health is low
    if current_hp <= 20 and current_hp > 0:
        return random.choice(reactions) + " Du spürst deine Kräfte schwinden..."
    return random.choice(reactions)

def get_enemy_damage_reaction(damage, enemy_hp, enemy_max_hp):
    """Gibt eine Beschreibung des Schadens am Gegner zurück."""
    hp_ratio = enemy_hp / max(1, enemy_max_hp)
    if enemy_hp <= 0:
        return "Er bricht zusammen!"
    if damage >= 40:
        return "Ein verheerender Treffer! Der Gegner taumelt schwer."
    elif damage >= 20:
        return "Ein solider Treffer. Der Gegner grunzt vor Schmerz."
    elif damage >= 10:
        return "Ein ordentlicher Treffer!"
    else:
        return "Der Treffer streift ihn gerade so."

def get_enemy_health_description(hp, max_hp):
    """Gibt eine qualitative Beschreibung der Gegner-Gesundheit zurück."""
    if hp <= 0:
        return "Tot"
    ratio = hp / max(1, max_hp)
    if ratio >= 0.9:
        return "Fast unversehrt"
    elif ratio >= 0.7:
        return "Leicht verwundet"
    elif ratio >= 0.5:
        return "Sichtbar verwundet"
    elif ratio >= 0.3:
        return "Schwer verletzt"
    else:
        return "Am Rande des Todes"

def get_player_carry_weight():
    """Berechnet das aktuelle Tragegewicht des Spielers."""
    total = 0
    for item_key in player_inventory:
        idef = ITEM_DEFS.get(item_key)
        if idef:
            total += idef.weight
    return total

def get_encumbrance_description():
    """Gibt eine qualitative Beschreibung der Traglast zurück."""
    weight = get_player_carry_weight()
    max_w = player_stats['max_weight']
    ratio = weight / max(1, max_w)
    if ratio >= 1.0:
        return "Du trägst viel zu viel! Du kannst dich kaum bewegen."
    elif ratio >= 0.8:
        return "Dein Gepäck ist schwer. Jeder Schritt kostet Kraft."
    elif ratio >= 0.5:
        return "Du trägst einiges mit dir. Noch machbar."
    else:
        return None  # Normal — kein Kommentar nötig

def get_light_warning(charge):
    """Gibt eine Warnung zurück wenn die Lichtquelle schwach ist."""
    if charge <= 0:
        return "Deine Taschenlampe erlischt! Die Dunkelheit verschluckt alles."
    elif charge <= 10:
        return "Das Licht deiner Taschenlampe wird immer schwächer!"
    elif charge <= 20:
        return "Deine Taschenlampe flackert besorgniserregend."
    return None

def tick_hidden_systems():
    """Aktualisiert alle versteckten Systeme pro Spielzug. Aufgerufen nach jedem Befehl."""
    messages = []
    
    # --- HUNGER ---
    player_stats['hunger'] = min(100, player_stats['hunger'] + 1)
    player_stats['turns_since_last_meal'] += 1
    
    # Hunger-Warnungen bei Schwellen
    hunger = player_stats['hunger']
    if hunger == 40:
        messages.append("Dein Magen knurrt leise.")
    elif hunger == 60:
        messages.append("Du spürst einen nagenden Hunger.")
    elif hunger == 80:
        messages.append("Du fühlst dich schwach vor Hunger!")
    
    # Bei extremem Hunger: Stärke reduzieren
    if hunger > 80:
        player_stats['strength'] = max(0, player_stats['strength'] - 1)
    
    # --- LICHT ---
    for item_key in player_inventory:
        idef = ITEM_DEFS.get(item_key)
        if idef and idef.charge > 0:
            idef.charge -= 1
            warning = get_light_warning(idef.charge)
            if warning:
                messages.append(warning)
    
    # --- PASSIVE RECOVERY ---
    if not player_stats['in_combat'] and player_stats['hunger'] < 60:
        turn_diff = game_moves - player_stats['last_recovery_turn']
        if turn_diff >= 5 and player_stats['health'] < 100:
            old_hp = player_stats['health']
            player_stats['health'] = min(100, player_stats['health'] + 2)
            player_stats['last_recovery_turn'] = game_moves
            if player_stats['health'] >= 100 and old_hp < 100:
                messages.append("Du fühlst dich wieder vollständig erholt.")
            elif player_stats['health'] > old_hp:
                messages.append("Deine Wunden heilen langsam.")
    
    # --- STÄRKE RECOVERY (langsam) ---
    if player_stats['hunger'] < 40 and player_stats['strength'] < 100:
        if game_moves % 8 == 0:
            player_stats['strength'] = min(100, player_stats['strength'] + 1)
    
    return messages

# Score-Werte für verschiedene Aktionen
SCORE_VALUES = {
    'zombie_kill': 30,
    'item_pickup': 5,
    'new_room': 2,
    'container_found': 10,
    'move': 0,  # Züge kosten keine Punkte, werden aber gezählt
}

# === REACTIVE PARSER SYSTEM ===
# Alle bekannten Verben (für "Unbekanntes Verb" Erkennung)
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
    'schieben', 'schieb', 'brech', 'zerhacke', '?',
}

# Verben die ein Objekt brauchen
VERBS_NEED_OBJECT = {
    'nimm': 'nehmen', 'lese': 'lesen', 'lies': 'lesen', 'lesen': 'lesen',
    'esse': 'essen', 'iss': 'essen', 'öffne': 'öffnen', 'oeffne': 'öffnen',
    'ausrüsten': 'ausrüsten', 'lege': 'legen',
}

# Abwechslungsreiche Antworten für unbekannte Verben (Zork-Stil)
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

# Snarky Antworten für logisch unmögliche Aktionen
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
#
def spawn_chance():
    if random.random() < 0.15:  # 15% statt 50% – weniger Zombie-Spam
        return True
    return False

# Bonus-Stats pro Fäuste-Level
FIST_LEVEL_BONUSES = {
    1: {'damage': [99, 100]},
    2: {'damage': [99, 100]},
    3: {'damage': [12, 22]},
    4: {'damage': [18, 30]},
    5: {'damage': [25, 40]}   # Max Level
}

# QTE System
qte_active = False
qte_sequence = []
qte_input = ""
qte_start_time = 0
qte_duration = 2.0  # Sekunden
qte_callback = None

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

current_enemy = None

# Prolog Text
PROLOG_TEXT = """"...Quarantäne-Protokoll aktiviert... alle Bürger..."
Das Radio knackt. Draußen: Chaos. Schreie. Brennende Autos.

Du bist Albert Wesker Cristal. Die Welt geht unter.

Der Bunker ist drei Blocks entfernt. Du rennst. Die Stahltür öffnet sich.
Du wirfst dich hinein. Die Tür schließt sich laut hinter dir.


Stille. Dunkelheit. Du atmest schwer.


Ein Tropfen. Du bist nicht allein.

Etwas bewegt sich an der Decke. Es lässt sich fallen - SCHMATZ.

Im grünen Notlicht siehst du es:
Graue Haut. Schwarze Adern. Tentakel aus dem Mund.

Ein Toxoplasma-Zombie. Es rennt mit Hunger auf dich zu.

[Drücke ENTER]"""

rooms = {
    'start': {#Intro
        'name': 'Bunker - Eingangshalle',
        'description': 'Die schwere Stahltür ist verschlossen. Schwaches Notlicht erhellt den Raum grünlich. Ein Feuerlöscher hängt an der Wand. Auf dem Boden liegt eine Zeitung.',
        'exits': {},
        'items': ['feuerlöscher', 'zeitung'],
        'enemy': 'zombie',
        'first_visit': True
    },
    'corridor': {
        'name': 'Korridor',
        'description': 'Ein langer Korridor. Blutspuren an den Wänden. Du hörst Tropfen. Im OSTEN ist eine Tür. Im WESTEN auch. SÜDEN führt zurück.',
        'exits': {'süden': 'start', 'osten': 'laboratory', 'westen': 'storage'},
        'items': ['pistole', 'taschenlampe'],
        'enemy': None
    },
    'storage': {
        'name': 'Lagerraum',
        'description': 'Regale umgestürzt. Konserven und Vorräte verstreut. Eine Werkbank steht in der Ecke. Hinter einem umgestürzten Regal siehst du einen TUNNEL der nach NORDEN führt.',
        'exits': {'osten': 'corridor', 'norden': 'tunnel'},
        'items': ['medkit', 'batterien', 'messer', 'konserven']
    },
    'laboratory': {
        'name': 'Labor',
        'description': 'Zerbrochene Reagenzgläser. Tote Ratten in Käfigen. Ein Computer flackert schwach.',
        'exits': {'westen': 'corridor'},
        'items': ['schlüssel', 'ak', 'notizen']
    },
    'tunnel': {
        'name': 'Unterirdischer Tunnel',
        'description': 'Ein enger, dunkler Tunnel. Die Wände sind feucht. Du siehst schwaches Licht am Ende. Der Tunnel führt nach NORDEN weiter. SÜDEN führt zurück zum Lagerraum.',
        'exits': {'süden': 'storage', 'norden': 'spawn'},
        'items': [],
        'trigger_timeskip': True
    },
    'spawn': {
        'name': 'Versteck - Außenbereich',
        'description': 'Ein verlassenes Haus. Überwuchert von Efeu, aber intakt. Dein neues Zuhause für die nächste Zeit.',
        'exits': {},
        'items': [],
        'is_safehouse': True
    },
    'schlafzimmer': {#Spawn haus 
        'name': 'Schlafzimmer',
        'description': 'Dein Schlafzimmer. Das Bett steht NORDÖSTLICH in der Ecke, der Nachttisch links daneben. Die Garderobe ist SÜDÖSTLICH. WESTLICH steht ein Schreibtisch mit einem Schrank daneben. Der Ausgang ist im SÜDEN.',
        'exits': {'süden': 'flur'},
        'items': ['tagebuch', 'kleidung'],
        'first_visit_bedroom': False
    },
    'flur': {#Spawn haus 
        'name': 'Flur',
        'description': 'Ein schmaler Flur. Im NORDEN ist das Schlafzimmer. Im SÜDEN ist das Badezimmer. Nach OSTEN geht es weiter.',
        'exits': {'norden': 'schlafzimmer', 'süden': 'badezimmer', 'osten': 'eingangsbereich'},
        'items': [],
        'in_development': False
    },
    'badezimmer': { #Spawn haus 
        'name': 'Badezimmer',
        'description': 'Du stehst im badezimmer, die Badewanne kaputt mit blut resten dran, spiegel zerschplittert und der Medizin schrank offen und leergeräumt.',
        'exits': {'norden': 'flur'},
        'items': [],
        'in_development': False
    },
    'eingangsbereich': {#Spawn haus 
        'name': 'Eingangsbereich',
        'description': 'Der Eingangsbereich des Hauses. Im SÜDEN ist die Vordertür. Nach NORDEN geht es in den Wohnbereich. Im WESTEN ist der Flur.',
        'exits': {'süden': 'vordertuer', 'norden': 'wohnbereich', 'westen': 'flur','osten': 'wohnzimmer'},
        'items': [],
        'in_development': False
    },
    'wohnzimmer': {#Spawn haus 
        'name': 'Wohnzimmer',
        'description': 'Im wohnzimmer angekommen siehst du eine Couch mit einem Tisch in der Mitte sowie einem geschrotteten Fernseher auf dem Tv-schrank.',
        'exits': {'westen': 'eingangsbereich'},
        'items': [],
        'in_development': False
    },
    'vordertuer': {#Spawn haus 
        'name': 'Vordertür',
        'description': 'Du stehst an der Vordertür deines Verstecks. NORDEN führt zurück ins Haus. SÜDEN führt nach draußen.',
        'exits': {'norden': 'eingangsbereich', 'süden': 'suedlich_haus'},
        'items': [],
        'in_development': False
    },
    'schlafzimmer2': {#Spawn haus 
        'name': 'Schlafzimmer 2',
        'description': 'Im Zweiten Schlafzimmer drin sticht dir der eklige Geruch von Verwesung in die Nase, du siehst die leiche eines zombies in der ecke am verrotten mit einer Axt noch im Oberkörper drinne. Gerade aus ist ein Bett mit einem Nachtschrank daneben, weiter links ist ein schrank und in der linken ecke ist noch ein offener kleiderschrank. Im NORDWESTEN ist der Wohnbereich.',
        'exits': {'nordwesten': 'wohnbereich'},
        'items': ['axt'],
        'in_development': False
    },
     'kueche': {#Spawn haus 
        'name': 'Küche',
        'description': 'Du stehst in der küche, alle wandschränke sind offen, kaputte teller auf dem boden',
        'exits': {'westen': 'wohnbereich'},
        'items': ['dosenfleisch', 'crackers'],
        'in_development': False  
     },
     'wohnbereich': {#Spawn haus 
        'name': 'Wohnbereich',
        'description': 'Der zentrale Wohnbereich. Im SÜDOSTEN ist das zweite Schlafzimmer. Nach OSTEN geht es in die Küche. Im NORDEN führen Treppen nach unten. Nach SÜDEN ist der Eingangsbereich.',
        'exits': {'südosten': 'schlafzimmer2', 'osten': 'kueche', 'norden': 'treppen', 'süden': 'eingangsbereich'},
        'items': [],
        'enemy': 'zombie',
        'in_development': False,
        'zombie_spawn': True
    }, 
    'treppen': {#Spawn haus 
        'name': 'Treppen',
        'description': 'Die Treppen führen nach unten in den keller, nur ein dimmes licht ist von oben zu sehen.',
        'exits': {'süden': 'wohnbereich', 'runter': 'keller'},
        'items': [],
        'in_development': False
    },
    'keller': {#Spawn haus 
        'name': 'Keller',
        'description': 'Du bist im keller, in der rechten ecke steht ein Heizkessel, in der unteren linken ecke ist ein kaputter trockner sowie eine kaputter kaputte waschmaschine. Im süden liegt eine Tür zum Lager Raum und rechts von der Tür steht ein Kabinett',
        'exits': {'süden': 'lagerraum', 'hoch': 'treppen'},
        'items': [],
        'in_development': False
    },
    'lagerraum': {#Spawn haus 
        'name': 'Lager Raum',
        'description': 'Im lagerraum dirnnen stehen 3 Schwerlastregale mit weiterem dosen essen und wasser, ein bett steht in der rechten ecke. Im norden gehts in den ',
        'exits': {'norden': 'keller'},
        'items': ['wasser', 'konserven', 'rucksack'],
        'in_development': False
    },
    'suedlich_haus': {#Stadt
        'name': 'Südliche Straße',
        'description': 'Eine verwüstete Straße. Kaputte Autos und getrocknetes Blut überall. Im NORDEN ist dein Versteck. Nach WESTEN führt eine Weggabelung. Im SÜDEN steht ein Haus. Nach OSTEN geht die Straße weiter.',
        'exits': {'norden': 'vordertuer', 'westen': 'westliche_haus_gabelung', 'süden': 'haus1', 'osten': 'oestlich_weggabelung'},
        'items': [],
        'in_development': False,
        'spawn_chance': True,
        'zombie_spawn': False
    
    },
    'westliche_haus_gabelung': {#Stadt
        'name': 'Westliche Weggabelung',
        'description': 'Eine Weggabelung. Verrostete Straßenschilder zeigen in alle Richtungen. Im OSTEN liegt die südliche Straße. Nach NORDEN geht es zur nordwestlichen Weggabelung. Im SÜDEN führt die Straße Richtung Krankenhaus.',
        'exits': {'osten': 'suedlich_haus', 'norden': 'nord_westliche_weggabelung', 'süden': 'krankenhaus_straße'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_straße': {#Krankenhaus
        'name': 'Krankenhaus Straße',
        'description': 'Du stehst auf der Straße vor dem Krankenhaus. Im NORDEN führt die Straße zur westlichen Weggabelung. Im WESTEN ist der Eingang zum Krankenhaus. Nach SÜDEN geht es zur Home Depot Weggabelung Nord Ost.',
        'exits': {'norden': 'westliche_haus_gabelung', 'westen': 'krankenhaus_eingang', 'süden': 'home_depot_weggabelung_nord_ost'},
        'items': [],
        'in_development': False,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'krankenhaus_eingang': {#Krankenhaus
        'name': 'Krankenhaus Eingang',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'osten': 'krankenhaus_straße'},
        'items': [],
        'in_development': False
    },
    'östliche_straße': {#stadt
        'name': 'Östliche Straße',
        'description': 'Kaputte Autos und Blutspuren bedecken die Straße. Im NORDEN liegt die nordöstliche Weggabelung. Im OSTEN steht ein verlassenes Haus. Nach SÜDEN geht es zur östlichen Weggabelung.',
        'exits': {'norden': 'nord_östliche_weggabelung', 'osten': 'haus2', 'süden': 'oestlich_weggabelung'},
        'items': [],
        'in_development': False,
        'spawn_chance': True,
        'zombie_spawn': False
    },
    'nord_westliche_weggabelung': {#Stadt Norden
        'name': 'Nord Westliche Weggabelung',
        'description': 'Eine Weggabelung im nördlichen Teil der Stadt. Im WESTEN führt die Straße zur Bibliothek. Nach OSTEN geht es zur nordöstlichen Weggabelung. Im SÜDEN liegt die westliche Hausgabelung.',
        'exits': {'osten': 'nord_östliche_weggabelung', 'westen': 'bibliothek_straße', 'süden': 'westliche_haus_gabelung'},
        'items': [],
        'in_development': False,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'bibliothek_straße': {#Bibliothek
        'name': 'Bibliothek Straße',
        'description': 'Eine ruhige Straße. Im NORDEN siehst du den Eingang zur Bibliothek. Im OSTEN führt der Weg zurück zur nordwestlichen Weggabelung.',
        'exits': {'norden': 'bibliothek_eingang', 'osten': 'nord_westliche_weggabelung'},
        'items': [],
        'in_development': False,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'bibliothek_eingang': {#Bibliothek
        'name': 'Bibliothek Eingang',
        'description': 'Du stehst vor den Türen der Bibliothek. Leises Knarzen ist von drinnen zu hören. Im SÜDEN geht es zurück zur Straße. Im NORDEN liegt das Innere der Bibliothek.',
        'exits': {'süden': 'bibliothek_straße', 'norden': 'bibliothek_1.1'},
        'items': [],
        'in_development': False
    },
    'bibliothek_1.1': {#Bibliothek
        'name': 'Bibliothek 1',
        'description': '',
        'exits': {'süden': 'bibliothek_eingang', 'westen': 'bibliothek_1.2', 'osten': 'bibliothek_2'},
        'items': [],
        'in_development': False
    },
    'bibliothek_1.2': {#Bibliothek
        'name': 'Bibliothek ',
        'description': '',
        'exits': {'osten': 'bibliothek_1.1'},
        'items': ['Stück Papier'],
        'in_development': False
    },
    'bibliothek_2': {#Bibliothek
        'name': 'Bibliothek ',
        'description': '',
        'exits': {'norden': 'bibliothek_3', 'westen': 'bibliothek_1.1'},
        'items': [],
        'in_development': False
    },
    'bibliothek_3': {#Bibliothek
        'name': 'Bibliothek',
        'description': '',
        'exits': {'süden': 'bibliothek_2', 'norden': 'bibliothek_4'},
        'items': [],
        'in_development': False
    },
    'bibliothek_4': {#Bibliothek
        'name': 'Bibliothek',
        'description': '',
        'exits': {'westen': 'bibliothek_5', 'süden': 'bibliothek_3'},
        'items': ['kiste'],
        'in_development': False
    },
    'bibliothek_5': {#Bibliothek
        'name': 'Bibliothek',
        'description': '',
        'exits': {'süden': 'bibliothek_6', 'osten': 'bibliothek_4'},
        'items': [],
        'enemy': 'zombie',
        'in_development': False
    },
    'bibliothek_6': {#Bibliothek
        'name': 'Bibliothek 1',
        'description': '',
        'exits': {'westen': 'bibliothek_7', 'norden': 'bibliothek_5'},
        'items': [],
        'in_development': False
    },
    'bibliothek_7': {#Bibliothek
        'name': 'Bibliothek 1',
        'description': '',
        'exits': {'osten': 'bibliothek_6', 'norden': 'bibliothek_8'},
        'items': [],
        'in_development': False
    },
    'bibliothek_8': {#Bibliothek
        'name': 'Bibliothek 1',
        'description': '',
        'exits': {'süden': 'bibliothek_7'},
        'items': ['kampfmesser'],
        'in_development': False
    },
    'nord_östliche_weggabelung': {#Stadt Norden
        'name': 'Nord Östliche Weggabelung',
        'description': 'Eine breite Weggabelung. Im NORDEN führt die Straße weiter. Im WESTEN liegt die nordwestliche Weggabelung. Nach SÜDEN geht es zur östlichen Straße. Im OSTEN siehst du den Parkplatz von Walmart.',
        'exits': {'norden': 'norden_straße', 'westen': 'nord_westliche_weggabelung', 'süden': 'östliche_straße', 'nord_osten': 'parkplatz'},
        'items': [],
        'in_development': False,
        'spawn_chance': True,
        'zombie_spawn': False
    },
    'parkplatz': {#Walmart
        'name': 'Parkplatz',
        'description': 'Du stehst auf dem Parkplatz von Walmart, es stehen viele kaputte autos, manche davon auch umgekippt. Richtung westen  und im süden gehst zur weggabelung zurück',
        'exits': {'westen': 'norden_straße', 'süden': 'nord_östliche_weggabelung', 'norden': 'walmart_eingang'},
        'items': [],
        'in_development': False,
        'spawn_chance': True,
        'zombie_spawn': False
    },
    'walmart_eingang': {#Walmart
        'name': 'Walmart Eingang',
        'description': 'Die Schiebetüren aus glas sind kaputt, boden voller scherben, die kannst im Walmart zombies durch Regale sehen ',
        'exits': {'süden': 'parkplatz', 'norden': 'walmart_1'},
        'items': [],
        'in_development': False
    },
    'walmart_1': {#Walmart
        'name': 'Walmart',
        'description': 'Du stehst im walmart, die siehst viele umgefallene Regale, und viele Artikel liegen auf dem Boden. Links von dir bemerkst du einen durchgang',
        'exits': {'süden': 'parkplatz', 'westen': 'walmart_2'},
        'items': [],
        'in_development': True
    },
    'walmart_2': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'norden': 'walmart_3','osten': 'walmart_3'},
        'items': [],
        'in_development': True
    },
    'walmart_3': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'süden': 'walmart_2', 'osten': 'walmart_4'},
        'items': ['schokoriegel', 'energieriegel'],
        'in_development': True
    },
    'walmart_4': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'osten': 'walmart_5', 'westen': 'walmart_3'},
        'items': [],
        'in_development': True
    },
    'walmart_5': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'norden': 'walmart_6', 'westen': 'walmart_4'},
        'items': [],
        'enemy': 'zombie',
        'in_development': True,
        'zombie_spawn': True
    },
    'walmart_6': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'westen': 'walmart_7', 'süden': 'walmart_5'},
        'items': [],
        'in_development': True
    },
    'walmart_7': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'norden': 'walmart_8', 'osten': 'walmart_6'},
        'items': [],
        'in_development': True
    },
    'walmart_8': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'norden': 'walmart_9', 'süden': 'walmart_7'},
        'items': [],
        'in_development': True
    },
    'walmart_9': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'osten': 'walmart_10', 'süden': 'walmart_8'},
        'items': [],
        'enemy': 'zombie',
        'in_development': True,
        'zombie_spawn': True
    },
    'walmart_10': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'süden': 'walmart_11', 'westen': 'walmart_9'},
        'items': [],
        'in_development': True
    },
    'walmart_11': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'westen': 'walmart_12.1', 'norden': 'walmart_10', 'süden': 'walmart_12.2'},
        'items': [],
        'in_development': True
    },
    'walmart_12.1': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'süden': 'walmart_13', 'norden': 'walmart_11'},
        'items': [],
        'in_development': True
    },
    'walmart_12.2': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'norden': 'walmart_11'},
        'items': [],
        'in_development': True
    },
    'walmart_13': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'westen': 'walmart_14', 'norden': 'walmart_12.1'},
        'items': [],
        'in_development': True
    },
    'walmart_14': {#Walmart
        'name': 'Walmart',
        'description': '',
        'exits': {'süden': 'walmart_13'},
        'items': [],
        'in_development': True
    },
    'norden_straße': {#Stadt Norden
        'name': 'Norden Straße',
        'description': 'Eine Straße im Norden der Stadt. Im WESTEN steht ein Haus mit offenen Türen. Im OSTEN liegt der Parkplatz von Walmart. Nach SÜDEN geht es zurück zur Weggabelung.',
        'exits': {'westen': 'haus_3_eingang', 'süden': 'nord_östliche_weggabelung', 'osten': 'parkplatz'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'haus_3_eingang': {#Haus3
        'name': 'eingang',
        'description': '.',
        'exits': {'westen': 'haus_3_v'},
        'items': [],
        'in_development': True
    },
    'haus_3_v': {#Haus3
        'name': 'Haus 3 vordertür',
        'description': '.',
        'exits': {'osten': 'haus_3_eingang', 'norden': 'wohnzimmer_h3', 'süden': 'bedroom_2', 'westen': 'haus_3_wohnbereich'},
        'items': [],
        'in_development': True
    },
    'haus_3_wohnbereich': {#Haus3
        'name': 'Wohnbereich',
        'description': '.',
        'exits': {'osten': 'haus_3_v', 'norden': 'küche_h3', 'süden': 'bathroom_3', 'westen': 'bedroom_3'},
        'items': [],
        'in_development': True
    },
    'wohnzimmer_h3': {#Haus3
        'name': 'Wohnzimmer',
        'description': '.',
        'exits': {'süden': 'haus_3_wohnbereich'},
        'items': [],
        'in_development': True
    },
    'küche_h3': {#Haus3
        'name': 'Küche',
        'description': '.',
        'exits': {'osten': 'haus_3_wohnbereich'},
        'items': ['apfel'],
        'in_development': True
    },
    'bathroom_3': {#Haus3
        'name': 'Badezimmer',
        'description': '.',
        'exits': {'norden': 'haus_3_wohnbereich'},
        'items': [],
        'in_development': True
    },
    'bedroom_3': {#Haus3
        'name': 'Schlafzimmer',
        'description': '.',
        'exits': {'osten': 'haus_3_wohnbereich'},
        'items': [],
        'in_development': True
    },
    'oestlich_weggabelung': {#Stadt
        'name': 'Östliche Weggabelung',
        'description': 'Kaputte Autos und Blutspuren liegen auf der Straße. Im NORDEN ist die östliche Straße. Nach WESTEN geht es zur südlichen Straße. Im OSTEN liegt ein verwilderter Park. Nach SÜDEN führt die Park Straße.',
        'exits': {'norden': 'östliche_straße', 'westen': 'suedlich_haus', 'süd_osten': 'park', 'süden': 'park_straße'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'park_straße': {#Stadt
        'name': 'Park Straße',
        'description': 'Eine Straße entlang des Parks. Im NORDEN liegt die östliche Weggabelung. Im OSTEN erstreckt sich der Park. Nach SÜDEN führt der Weg zur Skyscraper Weggabelung.',
        'exits': {'norden': 'oestlich_weggabelung', 'osten': 'park', 'süden': 'skyscraper_weggabelung'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'skyscraper_weggabelung': {#Stadt
        'name': 'Skyscraper Weggabelung',
        'description': 'Ein Hochhaus ragt über dir in den Himmel. Im NORDEN ist die Park Straße. Nach WESTEN führt die Straße zur Pizzeria. Im OSTEN liegt die südöstliche Skyscraper Weggabelung. Nach SÜDEN führt die Straße weiter.',
        'exits': {'norden': 'park_straße', 'westen': 'straße_pizzeria', 'osten': 'süd_östliche_skyscraper_weggabelung', 'süden': 'westliche_skyscraper2_weggabelung'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'süd_östliche_skyscraper_weggabelung': {#Stadt
        'name': 'Süd Östliche Skyscraper Weggabelung',
        'description': 'Eine Weggabelung im Schatten der Hochhäuser. Im WESTEN liegt die Skyscraper Weggabelung. Nach SÜDEN führt die Straße weiter.',
        'exits': {'westen': 'skyscraper_weggabelung', 'süden': 'östliche_skyscraper2_straße'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'östliche_skyscraper2_straße': {#Stadt
        'name': 'Östliche Skyscraper Straße 2',
        'description': 'Eine verwüstete Straße zwischen Hochhäusern. Im NORDEN liegt die südöstliche Skyscraper Weggabelung.',
        'exits': {'norden': 'süd_östliche_skyscraper_weggabelung'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'westliche_skyscraper2_weggabelung': {#Stadt
        'name': 'Westliche Skyscraper2 Weggabelung',
        'description': 'Eine Weggabelung. Im NORDEN liegt die Skyscraper Weggabelung. Nach WESTEN führt die Straße zur südlichen Pizzeria Straße.',
        'exits': {'norden': 'skyscraper_weggabelung', 'westen': 'südliche_pizzeria_straße'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'südliche_pizzeria_straße': {#Stadt
        'name': 'Südliche Pizzeria Straße',
        'description': 'Eine Straße südlich der Pizzeria. Im OSTEN liegt die Skyscraper Weggabelung. Nach WESTEN geht es zur Home Depot Weggabelung Osten.',
        'exits': {'osten': 'skyscraper_weggabelung', 'westen': 'home_depot_weggabelung_osten'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_weggabelung_osten': {#Stadt
        'name': 'Home Depot Weggabelung Osten',
        'description': 'Eine Straße nahe dem Home Depot. Im NORDEN liegt die Home Depot Weggabelung Nord Ost. Im OSTEN ist die südliche Pizzeria Straße. Nach SÜDEN geht es zur Home Depot Weggabelung Süd Ost.',
        'exits': {'norden': 'home_depot_weggabelung_nord_ost', 'osten': 'südliche_pizzeria_straße', 'süden': 'home_depot_weggabelung_süd_ost'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_weggabelung_süd_ost': {#Stadt
        'name': 'Home Depot Weggabelung Süd Ost',
        'description': 'Eine Weggabelung an der Südostseite des Home Depot. Im NORDEN liegt die Home Depot Weggabelung Osten. Nach WESTEN führt die Home Depot Straße Süd.',
        'exits': {'norden': 'home_depot_weggabelung_osten', 'westen': 'home_depot_straße_süd'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_straße_süd': {#Stadt
        'name': 'Home Depot Straße Süd',
        'description': 'Eine Straße an der Südseite des Home Depot. Im OSTEN liegt die Home Depot Weggabelung Süd Ost. Nach WESTEN führt die Straße zur Home Depot Weggabelung West Süd.',
        'exits': {'osten': 'home_depot_weggabelung_süd_ost', 'westen': 'home_depot_weggabelung_west_süd'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_weggabelung_west_süd': {#Stadt
        'name': 'Home Depot Weggabelung West Süd',
        'description': 'Eine Weggabelung an der Südwestseite des Home Depot. Im OSTEN liegt die Home Depot Straße Süd. Nach NORDEN führt die Home Depot Straße West.',
        'exits': {'osten': 'home_depot_straße_süd', 'norden': 'home_depot_straße_west'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_straße_west': {#Stadt
        'name': 'Home Depot Straße West',
        'description': 'Eine Straße an der Westseite des Home Depot. Im SÜDEN liegt die Home Depot Weggabelung West Süd. Nach NORDEN führt die Straße zur Home Depot Weggabelung West Nord.',
        'exits': {'süden': 'home_depot_weggabelung_west_süd', 'norden': 'home_depot_weggabelung_west_nord'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_weggabelung_west_nord': {#Stadt
        'name': 'Home Depot Weggabelung West Nord',
        'description': 'Eine Weggabelung an der Nordwestseite des Home Depot. Im SÜDEN liegt die Home Depot Weggabelung West. Nach OSTEN führt die Home Depot Straße Nord.',
        'exits': {'süden': 'home_depot_straße_west', 'osten': 'home_depot_straße_nord'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_straße_nord': {#Stadt
        'name': 'Home Depot Straße Nord',
        'description': 'Eine Straße an der Nordseite des Home Depot. Im OSTEN liegt die Home Depot Weggabelung Nord Ost. Nach WESTEN führt die Straße zur Home Depot Weggabelung Nord West.',
        'exits': {'osten': 'home_depot_weggabelung_nord_ost', 'westen': 'home_depot_weggabelung_nord_west'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'haus1': {#Haus1
        'name': 'Haus 1',
        'description': 'Du stehst vor der Haustür vom Haus doch sie lässt sich nicht öffnen.',
        'exits': {'norden': 'suedlich_haus', 'osten': 'haus1_vordertür'},
        'items': [],
        'in_development': True
    },
    'haus1_vordertür': {#Haus1
        'name': 'Haus 1 - Vordertür',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'westen': 'haus1'},
        'items': [],
        'in_development': True
    },
    'haus2': {#Haus2
        'name': 'Haus 2',
        'description': 'Du stehst vor einem verlassenen Haus. Die Tür ist verriegelt, durch die zerbrochenen Fenster siehst du nur Dunkelheit.',
        'exits': {'westen': 'östliche_straße'},
        'items': [],
        'in_development': True
    },
    'straße_pizzeria': {#Stadt
        'name': 'Straße Pizzeria',
        'description': 'Eine Straße vor einer alten Pizzeria. Im OSTEN geht es zur Skyscraper Weggabelung. Nach WESTEN führt der Weg Richtung Home Depot.',
        'exits': {'osten': 'skyscraper_weggabelung', 'westen': 'home_depot_weggabelung_nord_ost'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'home_depot_weggabelung_nord_ost': {#Stadt
        'name': 'Home Depot Weggabelung Nord Ost',
        'description': 'Eine breite Straße an der Nordostseite des Home Depot. Im OSTEN liegt die Pizzeria Straße. Nach WESTEN führt die Home Depot Straße Nord. Im NORDEN geht es zur Krankenhaus Straße.',
        'exits': {'osten': 'straße_pizzeria', 'westen': 'home_depot_straße_nord', 'norden': 'krankenhaus_straße'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'park': {#Stadt
        'name': 'Park',
        'description': 'Ein verwilderter Park. Überwucherte Bänke und ein rostiger Spielplatz. Die Natur holt sich alles zurück. Im WESTEN liegt die östliche Weggabelung. Nach NORDEN führt die Park Straße.',
        'exits': {'westen': 'oestlich_weggabelung', 'norden': 'park_straße'},
        'items': [],
        'in_development': True,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'bedroom_2': {#Haus3
        'name': 'Schlafzimmer 2',
        'description': 'Ein kleines Schlafzimmer. Das Bett ist umgeworfen, Kleidung liegt verstreut auf dem Boden.',
        'exits': {'norden': 'haus_3_v'},
        'items': [],
        'in_development': True
    },
}

# Build the spatial GAME_MAP from the rooms dictionary
rebuild_game_map(rooms)

# ========================
# HIERARCHICAL CONTAINER SYSTEM
# ========================
# Architecture: World → Building → Floor → Room → Objects
# All movement between rooms passes through Discrete Transition Nodes.

BUILDING_HIERARCHY = {
    'bunker': {
        'name': 'Bunker',
        'floors': {
            'main': ['start', 'corridor', 'laboratory', 'storage', 'tunnel'],
        },
    },
    'versteck': {
        'name': 'Versteck (Safehouse)',
        'floors': {
            'erdgeschoss': ['spawn', 'schlafzimmer', 'flur', 'badezimmer',
                           'eingangsbereich', 'wohnzimmer', 'wohnbereich',
                           'schlafzimmer2', 'kueche', 'vordertuer', 'treppen'],
            'keller': ['keller', 'lagerraum'],
        },
    },
    'stadt': {
        'name': 'Stadt',
        'floors': {
            'straßen': ['suedlich_haus', 'westliche_haus_gabelung',
                       'oestlich_weggabelung', 'nord_westliche_weggabelung',
                       'nord_östliche_weggabelung', 'östliche_straße',
                       'norden_straße', 'park_straße', 'skyscraper_weggabelung',
                       'straße_pizzeria',
                       'home_depot_weggabelung_nord_ost',
                       'süd_östliche_skyscraper_weggabelung',
                       'östliche_skyscraper2_straße',
                       'westliche_skyscraper2_weggabelung',
                       'südliche_pizzeria_straße',
                       'home_depot_weggabelung_osten',
                       'home_depot_weggabelung_süd_ost',
                       'home_depot_straße_süd',
                       'home_depot_weggabelung_west_süd',
                       'home_depot_straße_west',
                       'home_depot_weggabelung_west_nord',
                       'home_depot_straße_nord'],
        },
    },
    'krankenhaus': {
        'name': 'Krankenhaus',
        'floors': {
            'main': ['krankenhaus_straße', 'krankenhaus_eingang'],
        },
    },
    'bibliothek': {
        'name': 'Bibliothek',
        'floors': {
            'main': ['bibliothek_straße', 'bibliothek_eingang',
                    'bibliothek_1.1', 'bibliothek_1.2', 'bibliothek_2',
                    'bibliothek_3', 'bibliothek_4', 'bibliothek_5',
                    'bibliothek_6', 'bibliothek_7', 'bibliothek_8'],
        },
    },
    'walmart': {
        'name': 'Walmart',
        'floors': {
            'main': ['parkplatz', 'walmart_eingang', 'walmart_1', 'walmart_2',
                    'walmart_3', 'walmart_4', 'walmart_5', 'walmart_6',
                    'walmart_7', 'walmart_8', 'walmart_9', 'walmart_10',
                    'walmart_11', 'walmart_12.1', 'walmart_12.2',
                    'walmart_13', 'walmart_14'],
        },
    },
    'haus1': {
        'name': 'Haus 1',
        'floors': {'main': ['haus1', 'haus1_vordertür']},
    },
    'haus2': {
        'name': 'Haus 2',
        'floors': {'main': ['haus2']},
    },
    'haus3': {
        'name': 'Haus 3',
        'floors': {
            'main': ['haus_3_eingang', 'haus_3_v', 'haus_3_wohnbereich',
                    'wohnzimmer_h3', 'küche_h3', 'bathroom_3', 'bedroom_3',
                    'bedroom_2'],
        },
    },
    'park': {
        'name': 'Park',
        'floors': {'main': ['park']},
    },
}

# Reverse lookup: room_key → (building_key, floor_key)
_room_to_container = {}
for _bk, _bd in BUILDING_HIERARCHY.items():
    for _fk, _fr in _bd['floors'].items():
        for _rk in _fr:
            _room_to_container[_rk] = (_bk, _fk)

# ===== DISCRETE TRANSITION NODES =====
# Every connection between rooms is an explicit transition node.
# type: 'door', 'passage', 'stairs', 'entrance', 'exit'
# locked: if True, movement is blocked until unlocked
TRANSITIONS = [
    # --- BUNKER ---
    {'id': 'start_corridor', 'type': 'door', 'from': 'start', 'to': 'corridor',
     'dir_from': 'norden', 'dir_to': 'süden', 'locked': True},
    {'id': 'corridor_lab', 'type': 'door', 'from': 'corridor', 'to': 'laboratory',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'corridor_storage', 'type': 'door', 'from': 'corridor', 'to': 'storage',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'storage_tunnel', 'type': 'passage', 'from': 'storage', 'to': 'tunnel',
     'dir_from': 'norden', 'dir_to': 'süden'},
    # Bunker → Versteck (cross-building, triggers timeskip)
    {'id': 'tunnel_spawn', 'type': 'passage', 'from': 'tunnel', 'to': 'spawn',
     'dir_from': 'norden', 'dir_to': None, 'trigger': 'timeskip'},
    # --- VERSTECK ERDGESCHOSS ---
    {'id': 'schlaf_flur', 'type': 'door', 'from': 'schlafzimmer', 'to': 'flur',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'flur_bad', 'type': 'door', 'from': 'flur', 'to': 'badezimmer',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'flur_eingang', 'type': 'door', 'from': 'flur', 'to': 'eingangsbereich',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'eingang_wohnbereich', 'type': 'door', 'from': 'eingangsbereich', 'to': 'wohnbereich',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'eingang_wohnzimmer', 'type': 'door', 'from': 'eingangsbereich', 'to': 'wohnzimmer',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'eingang_vordertuer', 'type': 'door', 'from': 'eingangsbereich', 'to': 'vordertuer',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'wb_schlaf2', 'type': 'door', 'from': 'wohnbereich', 'to': 'schlafzimmer2',
     'dir_from': 'südosten', 'dir_to': 'nordwesten'},
    {'id': 'wb_kueche', 'type': 'door', 'from': 'wohnbereich', 'to': 'kueche',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'wb_treppen', 'type': 'passage', 'from': 'wohnbereich', 'to': 'treppen',
     'dir_from': 'norden', 'dir_to': 'süden'},
    # Versteck floor transition (stairs)
    {'id': 'treppen_keller', 'type': 'stairs', 'from': 'treppen', 'to': 'keller',
     'dir_from': 'runter', 'dir_to': 'hoch'},
    {'id': 'keller_lager', 'type': 'door', 'from': 'keller', 'to': 'lagerraum',
     'dir_from': 'süden', 'dir_to': 'norden'},
    # Versteck exit → Stadt
    {'id': 'vordertuer_strasse', 'type': 'entrance', 'from': 'vordertuer', 'to': 'suedlich_haus',
     'dir_from': 'süden', 'dir_to': 'norden'},
    # --- STADT ---
    {'id': 'sued_west', 'type': 'passage', 'from': 'suedlich_haus', 'to': 'westliche_haus_gabelung',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'sued_ost', 'type': 'passage', 'from': 'suedlich_haus', 'to': 'oestlich_weggabelung',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'sued_haus1', 'type': 'passage', 'from': 'suedlich_haus', 'to': 'haus1',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'west_nw', 'type': 'passage', 'from': 'westliche_haus_gabelung', 'to': 'nord_westliche_weggabelung',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'west_kh', 'type': 'passage', 'from': 'westliche_haus_gabelung', 'to': 'krankenhaus_straße',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'kh_str_eing', 'type': 'entrance', 'from': 'krankenhaus_straße', 'to': 'krankenhaus_eingang',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'nw_no', 'type': 'passage', 'from': 'nord_westliche_weggabelung', 'to': 'nord_östliche_weggabelung',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'ost_str_no', 'type': 'passage', 'from': 'östliche_straße', 'to': 'nord_östliche_weggabelung',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'nw_bib', 'type': 'passage', 'from': 'nord_westliche_weggabelung', 'to': 'bibliothek_straße',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'ost_str_ost_gab', 'type': 'passage', 'from': 'östliche_straße', 'to': 'oestlich_weggabelung',
     'dir_from': 'süden', 'dir_to': 'westen'},
    {'id': 'ost_gab_ost_str', 'type': 'passage', 'from': 'oestlich_weggabelung', 'to': 'östliche_straße',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'ost_gab_park', 'type': 'passage', 'from': 'oestlich_weggabelung', 'to': 'park_straße',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'park_sky', 'type': 'passage', 'from': 'park_straße', 'to': 'skyscraper_weggabelung',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'sky_pizzeria', 'type': 'passage', 'from': 'skyscraper_weggabelung', 'to': 'straße_pizzeria',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'pizzeria_homedepot', 'type': 'passage', 'from': 'straße_pizzeria', 'to': 'home_depot_weggabelung_nord_ost',
     'dir_from': 'westen', 'dir_to': 'osten'},

    {'id': 'no_nord_str', 'type': 'passage', 'from': 'nord_östliche_weggabelung', 'to': 'norden_straße',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'no_parkplatz', 'type': 'passage', 'from': 'nord_östliche_weggabelung', 'to': 'parkplatz',
     'dir_from': 'nord_osten', 'dir_to': 'süden'},
    {'id': 'nord_str_park', 'type': 'passage', 'from': 'norden_straße', 'to': 'parkplatz',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'nord_str_h3', 'type': 'entrance', 'from': 'norden_straße', 'to': 'haus_3_eingang',
     'dir_from': 'westen', 'dir_to': None},
    # --- BIBLIOTHEK ---
    {'id': 'bib_str_eing', 'type': 'entrance', 'from': 'bibliothek_straße', 'to': 'bibliothek_eingang',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'bib_eing_1', 'type': 'door', 'from': 'bibliothek_eingang', 'to': 'bibliothek_1.1',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'bib_1_12', 'type': 'passage', 'from': 'bibliothek_1.1', 'to': 'bibliothek_1.2',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'bib_1_2', 'type': 'passage', 'from': 'bibliothek_1.1', 'to': 'bibliothek_2',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'bib_2_3', 'type': 'passage', 'from': 'bibliothek_2', 'to': 'bibliothek_3',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'bib_3_4', 'type': 'passage', 'from': 'bibliothek_3', 'to': 'bibliothek_4',
     'dir_from': 'norden', 'dir_to': 'süden', 'locked': True, 'lock_msg': 'Ein großes Bücherregal versperrt den Weg nach NORDEN.\nVielleicht kannst du es zur Seite schieben?'},
    {'id': 'bib_4_5', 'type': 'passage', 'from': 'bibliothek_4', 'to': 'bibliothek_5',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'bib_5_6', 'type': 'passage', 'from': 'bibliothek_5', 'to': 'bibliothek_6',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'bib_6_7', 'type': 'passage', 'from': 'bibliothek_6', 'to': 'bibliothek_7',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'bib_7_8', 'type': 'passage', 'from': 'bibliothek_7', 'to': 'bibliothek_8',
     'dir_from': 'norden', 'dir_to': 'süden'},
    # --- WALMART ---
    {'id': 'park_wm_eing', 'type': 'entrance', 'from': 'parkplatz', 'to': 'walmart_eingang',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'wm_e_1', 'type': 'passage', 'from': 'walmart_eingang', 'to': 'walmart_1',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'wm_1_2', 'type': 'passage', 'from': 'walmart_1', 'to': 'walmart_2',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'wm_2_3', 'type': 'passage', 'from': 'walmart_2', 'to': 'walmart_3',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'wm_3_4', 'type': 'passage', 'from': 'walmart_3', 'to': 'walmart_4',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'wm_4_5', 'type': 'passage', 'from': 'walmart_4', 'to': 'walmart_5',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'wm_5_6', 'type': 'passage', 'from': 'walmart_5', 'to': 'walmart_6',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'wm_6_7', 'type': 'passage', 'from': 'walmart_6', 'to': 'walmart_7',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'wm_7_8', 'type': 'passage', 'from': 'walmart_7', 'to': 'walmart_8',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'wm_8_9', 'type': 'passage', 'from': 'walmart_8', 'to': 'walmart_9',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'wm_9_10', 'type': 'passage', 'from': 'walmart_9', 'to': 'walmart_10',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'wm_10_11', 'type': 'passage', 'from': 'walmart_10', 'to': 'walmart_11',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'wm_11_121', 'type': 'passage', 'from': 'walmart_11', 'to': 'walmart_12.1',
     'dir_from': 'westen', 'dir_to': 'norden'},
    {'id': 'wm_11_122', 'type': 'passage', 'from': 'walmart_11', 'to': 'walmart_12.2',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'wm_121_13', 'type': 'passage', 'from': 'walmart_12.1', 'to': 'walmart_13',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'wm_13_14', 'type': 'passage', 'from': 'walmart_13', 'to': 'walmart_14',
     'dir_from': 'westen', 'dir_to': 'süden'},
    # --- HAUS 1 ---
    {'id': 'haus1_tuer', 'type': 'door', 'from': 'haus1', 'to': 'haus1_vordertür',
     'dir_from': 'osten', 'dir_to': None, 'locked': True, 'lock_msg': 'Die Tür ist fest verschlossen.\nVielleicht kannst du sie aufbrechen?'},
    # --- HAUS 3 ---
    {'id': 'h3_eing_v', 'type': 'entrance', 'from': 'haus_3_eingang', 'to': 'haus_3_v',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'h3_v_wz', 'type': 'door', 'from': 'haus_3_v', 'to': 'wohnzimmer_h3',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'h3_v_wb', 'type': 'door', 'from': 'haus_3_v', 'to': 'haus_3_wohnbereich',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'h3_wb_kueche', 'type': 'door', 'from': 'haus_3_wohnbereich', 'to': 'küche_h3',
     'dir_from': 'norden', 'dir_to': 'osten'},
    {'id': 'h3_wb_bath', 'type': 'door', 'from': 'haus_3_wohnbereich', 'to': 'bathroom_3',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'h3_wb_bed', 'type': 'door', 'from': 'haus_3_wohnbereich', 'to': 'bedroom_3',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'h3_v_bed2', 'type': 'door', 'from': 'haus_3_v', 'to': 'bedroom_2',
     'dir_from': 'süden', 'dir_to': 'norden'},
    # --- HAUS 2 ---
    {'id': 'ost_str_haus2', 'type': 'entrance', 'from': 'östliche_straße', 'to': 'haus2',
     'dir_from': 'osten', 'dir_to': 'westen'},
    # --- PARK ---
    {'id': 'ost_gab_park_ort', 'type': 'passage', 'from': 'oestlich_weggabelung', 'to': 'park',
     'dir_from': 'süd_osten', 'dir_to': 'westen'},
    {'id': 'park_str_park', 'type': 'passage', 'from': 'park_straße', 'to': 'park',
     'dir_from': 'osten', 'dir_to': 'norden'},
    # --- NEUE STADT VERBINDUNGEN ---
    {'id': 'nw_west', 'type': 'passage', 'from': 'nord_westliche_weggabelung', 'to': 'westliche_haus_gabelung',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'kh_homedepot', 'type': 'passage', 'from': 'krankenhaus_straße', 'to': 'home_depot_weggabelung_nord_ost',
     'dir_from': 'süden', 'dir_to': 'norden'},
    # --- SKYSCRAPER BEREICH ---
    {'id': 'sky_sued_ost', 'type': 'passage', 'from': 'skyscraper_weggabelung', 'to': 'süd_östliche_skyscraper_weggabelung',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'sky_west_sky2', 'type': 'passage', 'from': 'skyscraper_weggabelung', 'to': 'westliche_skyscraper2_weggabelung',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'sued_ost_sky_ost_sky2', 'type': 'passage', 'from': 'süd_östliche_skyscraper_weggabelung', 'to': 'östliche_skyscraper2_straße',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'west_sky2_sued_pizza', 'type': 'passage', 'from': 'westliche_skyscraper2_weggabelung', 'to': 'südliche_pizzeria_straße',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'sued_pizza_hd_ost', 'type': 'passage', 'from': 'südliche_pizzeria_straße', 'to': 'home_depot_weggabelung_osten',
     'dir_from': 'westen', 'dir_to': 'osten'},
    # --- HOME DEPOT PERIMETER ---
    {'id': 'hd_ost_hd_no', 'type': 'passage', 'from': 'home_depot_weggabelung_osten', 'to': 'home_depot_weggabelung_nord_ost',
     'dir_from': 'norden', 'dir_to': None},
    {'id': 'hd_ost_hd_so', 'type': 'passage', 'from': 'home_depot_weggabelung_osten', 'to': 'home_depot_weggabelung_süd_ost',
     'dir_from': 'süden', 'dir_to': 'norden'},
    {'id': 'hd_so_hd_sued', 'type': 'passage', 'from': 'home_depot_weggabelung_süd_ost', 'to': 'home_depot_straße_süd',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'hd_sued_hd_ws', 'type': 'passage', 'from': 'home_depot_straße_süd', 'to': 'home_depot_weggabelung_west_süd',
     'dir_from': 'westen', 'dir_to': 'osten'},
    {'id': 'hd_ws_hd_west', 'type': 'passage', 'from': 'home_depot_weggabelung_west_süd', 'to': 'home_depot_straße_west',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'hd_west_hd_wn', 'type': 'passage', 'from': 'home_depot_straße_west', 'to': 'home_depot_weggabelung_west_nord',
     'dir_from': 'norden', 'dir_to': 'süden'},
    {'id': 'hd_wn_hd_nord', 'type': 'passage', 'from': 'home_depot_weggabelung_west_nord', 'to': 'home_depot_straße_nord',
     'dir_from': 'osten', 'dir_to': 'westen'},
    {'id': 'hd_nord_hd_no', 'type': 'passage', 'from': 'home_depot_straße_nord', 'to': 'home_depot_weggabelung_nord_ost',
     'dir_from': 'osten', 'dir_to': 'westen'},
]

# Build transition lookup: room_key → list of transitions from that room
_transitions_from = {}
_transitions_by_id = {}
for _t in TRANSITIONS:
    _t.setdefault('locked', False)
    _t.setdefault('trigger', None)
    _t.setdefault('lock_msg', None)
    _transitions_by_id[_t['id']] = _t
    _transitions_from.setdefault(_t['from'], []).append(_t)
    if _t.get('dir_to'):  # bidirectional
        _transitions_from.setdefault(_t['to'], []).append(_t)

def get_room_context(room_key):
    """Returns (building_key, building_name, floor_key) for a room"""
    ctx = _room_to_container.get(room_key)
    if ctx:
        bldg = BUILDING_HIERARCHY[ctx[0]]
        return (ctx[0], bldg['name'], ctx[1])
    return ('unbekannt', 'Unbekannt', 'unbekannt')

def get_transitions_from(room_key):
    """Returns list of (direction, target_room, transition) from this room"""
    result = []
    for t in _transitions_from.get(room_key, []):
        if t['from'] == room_key:
            result.append((t['dir_from'], t['to'], t))
        elif t['to'] == room_key and t.get('dir_to'):
            result.append((t['dir_to'], t['from'], t))
    return result

def try_transition(room_key, direction):
    """Attempt to move from room_key in direction. Returns (success, target, transition, message)"""
    for d, target, t in get_transitions_from(room_key):
        if d == direction:
            if t.get('locked'):
                msg = t.get('lock_msg', 'Der Weg ist versperrt.')
                return (False, None, t, msg)
            return (True, target, t, None)
    return (False, None, None, 'Du kannst nicht in diese Richtung gehen.')

def unlock_transition(transition_id):
    """Unlocks a transition node by ID"""
    t = _transitions_by_id.get(transition_id)
    if t:
        t['locked'] = False

def reset_transitions():
    """Resets all transitions to initial state"""
    for t in TRANSITIONS:
        if t['id'] == 'start_corridor':
            t['locked'] = True
        elif t['id'] == 'bib_3_4':
            t['locked'] = True
        elif t['id'] == 'haus1_tuer':
            t['locked'] = True
        else:
            t['locked'] = False


def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

def _draw_gradient_line(surface, center_x, y, half_width, color, max_alpha=80):
    """Zeichnet eine gecachte Gradient-Linie (vermeidet per-pixel draw calls)"""
    global _gradient_sep_cache, _gradient_sep_cache_key
    key = (half_width, color, max_alpha)
    
    if _gradient_sep_cache is None or _gradient_sep_cache_key != key:
        w = half_width * 2
        _gradient_sep_cache = pygame.Surface((w, 1), pygame.SRCALPHA)
        for i in range(half_width):
            t = i / half_width
            a = int(max_alpha * (1.0 - t))
            _gradient_sep_cache.set_at((half_width - i, 0), (*color, a))
            _gradient_sep_cache.set_at((half_width + i, 0), (*color, a))
        _gradient_sep_cache_key = key
    
    surface.blit(_gradient_sep_cache, (center_x - half_width, y))

def draw_vignette(surface, intensity=180):
    """Zeichnet einen dunklen Vignette-Rahmen um den Bildschirm (gecacht)"""
    global _vignette_cache, _vignette_cache_key
    w, h = surface.get_width(), surface.get_height()
    key = (w, h, intensity)
    
    if _vignette_cache is None or _vignette_cache_key != key:
        vig = pygame.Surface((w, h), pygame.SRCALPHA)
        steps = 20
        for i in range(steps):
            t = (i / steps)
            a = int(intensity * t * t)
            border = i * max(w, h) // (steps * 5)
            pygame.draw.rect(vig, (0, 0, 0, a), (0, 0, w, border))
            pygame.draw.rect(vig, (0, 0, 0, a), (0, h - border, w, border))
            pygame.draw.rect(vig, (0, 0, 0, a), (0, 0, border, h))
            pygame.draw.rect(vig, (0, 0, 0, a), (w - border, 0, border, h))
        _vignette_cache = vig
        _vignette_cache_key = key
    
    surface.blit(_vignette_cache, (0, 0))

def draw_cracked_text(surface, text, pos, color, time, font=None):
    """Zeichnet Text mit weichem Hintergrund-Glow und Schatten"""
    if font is None:
        font = get_scaled_font(120)
    
    # Subtile Erschütterung
    shake_x = math.sin(time * 0.003) * scale(2)
    shake_y = math.cos(time * 0.004) * scale(1)
    
    # Schatten (nur 1 Offset, sauber) — convert_alpha() für echte Transparenz
    shadow = font.render(text, True, DEEP_RED).convert_alpha()
    shadow_off = scale(3)
    shadow_rect = shadow.get_rect(center=(pos[0] + shadow_off + shake_x, pos[1] + shadow_off + shake_y))
    surface.blit(shadow, shadow_rect)
    
    # Haupt-Text — convert_alpha() für echte Transparenz
    text_surface = font.render(text, True, color).convert_alpha()
    text_rect = text_surface.get_rect(center=pos)
    final_rect = text_rect.move(shake_x, shake_y)
    surface.blit(text_surface, final_rect)

def draw_particles(surface, time, alpha):
    """Zeichnet Asche-Partikel und glühende Ember-Funken (optimiert)"""
    global _particle_surfaces
    w, h = surface.get_width(), surface.get_height()
    
    # Asche-Partikel (subtil, grau, langsam)
    for i in range(35):
        seed = i * 137
        drift = math.sin(time * 0.001 + seed) * 30
        x = (seed + int(time * 0.4) + int(drift)) % w
        y = (i * 79 + int(time * 0.6)) % h
        size = (i % 3) + 1
        a = min(255, int(alpha * 0.6))
        
        cache_key = (size, LIGHT_GRAY, a)
        if cache_key not in _particle_surfaces:
            ps = pygame.Surface((size, size), pygame.SRCALPHA)
            ps.fill((*LIGHT_GRAY, a))
            _particle_surfaces[cache_key] = ps
        surface.blit(_particle_surfaces[cache_key], (x, y))
    
    # Ember-Funken (orange, klein, steigen auf)
    for i in range(15):
        seed = i * 211 + 500
        drift = math.sin(time * 0.002 + seed * 0.7) * 20
        x = (seed + int(drift)) % w
        y = h - ((i * 97 + int(time * 1.2)) % h)
        life = (time * 0.003 + i) % 1.0
        size = max(1, int(3 * (1.0 - life)))
        a = min(255, int(alpha * (1.0 - life)))
        
        color = EMBER_ORANGE if i % 3 != 0 else EMBER_DIM
        cache_key = (size, color, a)
        if cache_key not in _particle_surfaces:
            ps = pygame.Surface((size, size), pygame.SRCALPHA)
            ps.fill((*color, a))
            _particle_surfaces[cache_key] = ps
        surface.blit(_particle_surfaces[cache_key], (int(x), int(y)))

def draw_cracks(surface, alpha):
    """Zeichnet rot-getönte Risse mit organischeren Mustern (gecacht)"""
    global _cracks_cache, _cracks_cache_key
    w, h = surface.get_width(), surface.get_height()
    key = (w, h, alpha)
    
    if _cracks_cache is None or _cracks_cache_key != key:
        crack_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        
        for i in range(10):
            start_x = int(i * w / 10 + 30)
            points = [(start_x, 0)]
            
            y = 0
            while y < h:
                primary = math.sin(y * 0.015 + i * 1.7) * 25
                secondary = math.sin(y * 0.04 + i * 3.1) * 10
                offset = primary + secondary
                points.append((int(start_x + offset), y))
                y += 35
            
            if len(points) > 1:
                crack_r = min(255, DARK_RED[0] + 30)
                crack_g = DARK_RED[1]
                crack_b = DARK_RED[2]
                pygame.draw.lines(crack_surface, (crack_r, crack_g, crack_b, min(255, alpha)), False, points, 2)
                offset_points = [(p[0] + 2, p[1]) for p in points]
                pygame.draw.lines(crack_surface, (crack_r // 2, crack_g, crack_b, min(255, alpha // 2)), False, offset_points, 1)
        
        _cracks_cache = crack_surface
        _cracks_cache_key = key
    
    surface.blit(_cracks_cache, (0, 0))

def draw_fog(surface, time, alpha):
    """Zeichnet subtilen Nebel / Rauch Overlay (optimiert)"""
    global _fog_circle_cache, _fog_surface, _fog_surface_size
    w, h = surface.get_width(), surface.get_height()
    
    # Reuse fog overlay surface statt jedes Frame neu zu erstellen
    if _fog_surface is None or _fog_surface_size != (w, h):
        _fog_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        _fog_surface_size = (w, h)
    _fog_surface.fill((0, 0, 0, 0))  # Clear statt neu erstellen
    
    for i in range(6):
        cx = int((i * w / 5 + math.sin(time * 0.0005 + i * 2) * 100) % w)
        cy = int(h * 0.6 + math.sin(time * 0.0003 + i) * h * 0.2)
        radius = scale(120 + i * 30)
        fog_a = min(255, int(alpha * 0.15))
        
        cache_key = (radius, fog_a)
        if cache_key not in _fog_circle_cache:
            fog_circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(fog_circle, (*FOG_COLOR, fog_a), (radius, radius), radius)
            _fog_circle_cache[cache_key] = fog_circle
        _fog_surface.blit(_fog_circle_cache[cache_key], (cx - radius, cy - radius))
    
    surface.blit(_fog_surface, (0, 0))

def draw_intro(current_time):
    """Zeichnet das atmosphärische Intro"""
    FADE_IN_DURATION = 2500
    HOLD_DURATION = 3500
    FADE_OUT_DURATION = 2000
    
    if current_time < FADE_IN_DURATION:
        alpha = int((current_time / FADE_IN_DURATION) * 255)
    elif current_time < FADE_IN_DURATION + HOLD_DURATION:
        alpha = 255
    elif current_time < FADE_IN_DURATION + HOLD_DURATION + FADE_OUT_DURATION:
        fade_progress = (current_time - FADE_IN_DURATION - HOLD_DURATION) / FADE_OUT_DURATION
        alpha = int((1 - fade_progress) * 255)
    else:
        return True
    
    screen.fill(BLACK)
    
    # Atmosphärische Schichten
    draw_fog(screen, current_time, alpha)
    draw_particles(screen, current_time, alpha // 2)
    
    # Vignette für Tiefe
    draw_vignette(screen, int(200 * (alpha / 255)))
    
    # Titel mit Glow - direkt auf Screen zeichnen statt extra Surface
    intro_font = get_scaled_font(120)
    draw_cracked_text(screen, "DEAD WORLD", 
                     (screen.get_width() // 2, screen.get_height() // 2 - scale(20)), 
                     (BLOOD_RED[0], BLOOD_RED[1], BLOOD_RED[2]), 
                     current_time,
                     intro_font)
    
    # "Press any key" hint mit Puls-Fade
    if current_time > FADE_IN_DURATION:
        hint_pulse = int(120 + 80 * math.sin(current_time * 0.003))
        hint_font = get_scaled_font(22)
        hint_surf = hint_font.render("LEERTASTE ZUM FORTFAHREN", True, (hint_pulse, hint_pulse // 3, hint_pulse // 4))
        hint_rect = hint_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + scale(80)))
        screen.blit(hint_surf, hint_rect)
    
    return False

class MenuButton:
    def __init__(self, text, pos, action):
        self.text = text
        self.pos = pos
        self.action = action
        self.hovered = False
        self.rect = None
    
    def draw(self, surface, current_time):
        button_font = get_scaled_font(50)
        
        if self.hovered:
            color = HOVER_RED
        else:
            color = BLOOD_RED
        
        # Schatten
        shadow = button_font.render(self.text, True, DEEP_RED)
        shadow_rect = shadow.get_rect(center=(self.pos[0] + scale(2), self.pos[1] + scale(2)))
        surface.blit(shadow, shadow_rect)
        
        # Haupt-Text
        text_surf = button_font.render(self.text, True, color)
        self.rect = text_surf.get_rect(center=self.pos)
        surface.blit(text_surf, self.rect)
        
        # Unterstreichungs-Animation bei Hover
        if self.hovered:
            line_width = int(self.rect.width * (0.5 + 0.5 * math.sin(current_time * 0.005)))
            line_x = self.rect.centerx - line_width // 2
            line_y = self.rect.bottom + scale(4)
            pygame.draw.line(surface, HOVER_RED, (line_x, line_y), (line_x + line_width, line_y), max(1, scale(2)))
    
    def check_hover(self, mouse_pos):
        if self.rect:
            self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered
    
    def click(self):
        if self.hovered and self.action:
            self.action()

def start_game():
    global current_state, game_history, current_room, player_inventory, prolog_shown, prolog_lines, prolog_line_index, menu_music_playing, visited_rooms, map_coords_dirty, zombie_kill_times
    global game_score, game_moves, view_mode, visited_rooms_desc, game_start_ticks, pending_ambiguity
    current_state = GAME
    game_history = []
    current_room = 'start'
    player_inventory = ['fäuste']
    prolog_shown = False
    prolog_line_index = 0
    visited_rooms = {'start'}  # Start-Raum als besucht markieren
    visited_rooms_desc = set()
    map_coords_dirty = True
    zombie_kill_times = {}  # Respawn-Cooldowns zurücksetzen
    game_score = 0
    game_moves = 0
    view_mode = 'verbose'
    pending_ambiguity = None
    game_start_ticks = pygame.time.get_ticks()
    # Reset hidden stats
    player_stats['health'] = 100
    player_stats['strength'] = 100
    player_stats['hunger'] = 0
    player_stats['turns_since_last_meal'] = 0
    player_stats['last_recovery_turn'] = 0
    player_stats['equipped_weapon'] = None
    player_stats['weapon_type'] = None
    player_stats['in_combat'] = False
    player_stats['fist_level'] = 1
    # Container-Inhalte zurücksetzen
    for idef in ITEM_DEFS.values():
        if idef.is_container:
            idef.contents = []
            idef.is_open = False
        # Reset light charges
        if idef.max_charge >= 0:
            idef.charge = idef.max_charge
    
    # Menü-Musik ausblenden
    pygame.mixer.music.fadeout(800)
    menu_music_playing = False
    
    # Prolog in Zeilen aufteilen
    prolog_lines = [line for line in PROLOG_TEXT.split('\n') if line.strip() or line == '']
    
    # Prolog-Text sofort anzeigen (process_command übernimmt die Logik)
    process_command("")

def show_options():
    global current_state
    current_state = OPTIONS

def back_to_menu():
    global current_state
    current_state = MENU
    _start_menu_music()

def _start_menu_music():
    """Startet die Menü-Musik falls nicht bereits aktiv"""
    global menu_music_playing
    if not menu_music_playing and os.path.exists(MENU_MUSIC_PATH):
        try:
            pygame.mixer.music.load(MENU_MUSIC_PATH)
            pygame.mixer.music.set_volume(game_settings['music_volume'])
            pygame.mixer.music.play(-1)  # Loop endlos
            menu_music_playing = True
        except Exception:
            pass  # Kein Crash wenn Musik nicht geladen werden kann

def change_resolution(direction):
    """Ändert die Auflösung (direction: -1 für niedriger, +1 für höher)"""
    global current_resolution_index, screen, fullscreen
    
    # Nicht ändern wenn Fullscreen aktiv
    if fullscreen:
        return
    
    # Neuen Index berechnen
    new_index = current_resolution_index + direction
    
    # Grenzen prüfen
    if new_index < 0 or new_index >= len(RESOLUTION_PRESETS):
        return
    
    current_resolution_index = new_index
    game_settings['resolution'] = new_index
    
    # Neue Auflösung anwenden
    name, width, height = RESOLUTION_PRESETS[new_index]
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

def get_current_resolution_name():
    """Gibt den Namen der aktuellen Auflösung zurück"""
    name, width, height = RESOLUTION_PRESETS[current_resolution_index]
    return f"{name} ({width}x{height})"

def quit_game():
    pygame.quit()
    sys.exit()

def get_max_chars():
    """Berechnet maximale Zeichen pro Zeile basierend auf Fensterbreite"""
    text_padding = scale(20)
    scaled_char_width = scale(12)
    return max(40, (screen.get_width() - text_padding * 2) // max(1, scaled_char_width))

def wrap_text(text, max_chars):
    """Bricht Text an Wortgrenzen um (Word-Wrapping)"""
    if len(text) <= max_chars:
        return [text]
    
    lines = []
    words = text.split(' ')
    current_line = ""
    
    for word in words:
        # Wenn das Wort selbst zu lang ist, hart umbrechen
        while len(word) > max_chars:
            if current_line:
                lines.append(current_line)
                current_line = ""
            lines.append(word[:max_chars-1] + "-")
            word = word[max_chars-1:]
        
        # Prüfe ob Wort noch in aktuelle Zeile passt
        if current_line:
            test_line = current_line + " " + word
        else:
            test_line = word
        
        if len(test_line) <= max_chars:
            current_line = test_line
        else:
            # Zeile voll, neue Zeile beginnen
            if current_line:
                lines.append(current_line)
            current_line = word
    
    # Letzte Zeile hinzufügen
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [""]

def add_to_history(text):
    """Fügt Text zur Spielhistorie hinzu mit automatischem Word-Wrapping und Typewriter-Effekt"""
    global scroll_offset, typewriter_active, typewriter_queue
    
    max_chars = get_max_chars()
    
    # Leere Zeilen direkt in die Queue
    if not text or text.strip() == "":
        typewriter_queue.append(text if text else "")
    else:
        # Text mit Word-Wrapping aufteilen
        wrapped_lines = wrap_text(text, max_chars)
        for line in wrapped_lines:
            typewriter_queue.append(line)
    
    # Typewriter starten falls nicht aktiv
    if not typewriter_active and typewriter_queue:
        _start_next_typewriter_line()
    
    # Automatisch nach unten scrollen bei neuen Nachrichten
    scroll_offset = 0

def _start_next_typewriter_line():
    """Startet die nächste Zeile im Typewriter-Effekt"""
    global typewriter_active, typewriter_current_line, typewriter_reveal_index, typewriter_last_time
    
    if typewriter_queue:
        typewriter_current_line = typewriter_queue.pop(0)
        typewriter_reveal_index = 0
        typewriter_last_time = pygame.time.get_ticks()
        typewriter_active = True
    else:
        typewriter_active = False
        typewriter_current_line = ""
        typewriter_reveal_index = 0

def update_typewriter():
    """Aktualisiert den Typewriter-Effekt - aufgerufen jeden Frame"""
    global typewriter_active, typewriter_reveal_index, typewriter_last_time, typewriter_current_line
    
    if not typewriter_active:
        return
    
    current_ms = pygame.time.get_ticks()
    
    # Leere Zeilen sofort fertigstellen
    if not typewriter_current_line or not typewriter_current_line.strip():
        game_history.append(typewriter_current_line)
        _start_next_typewriter_line()
        return
    
    # Berechne wie viele Zeichen seit dem letzten Update hinzugefügt werden sollen
    elapsed = current_ms - typewriter_last_time
    chars_to_add = elapsed // TYPEWRITER_SPEED
    
    if chars_to_add > 0:
        typewriter_reveal_index += chars_to_add
        typewriter_last_time = current_ms
        
        # Zeile fertig getippt?
        if typewriter_reveal_index >= len(typewriter_current_line):
            typewriter_reveal_index = len(typewriter_current_line)
            game_history.append(typewriter_current_line)
            _start_next_typewriter_line()

def move_direction(direction):
    """Bewege Spieler in eine Richtung (via Transition Nodes)"""
    global current_room
    
    # Try to find and use a transition node
    success, target, transition, msg = try_transition(current_room, direction)
    
    if not success:
        # Locked or no exit in that direction
        if msg:
            for line in msg.split('\n'):
                add_to_history(line)
        add_to_history("")
        return
    
    # Check for triggers on this transition
    if transition and transition.get('trigger') == 'timeskip':
        trigger_two_year_timeskip()
        return
    
    # 50% Zombie-Spawn in target rooms with spawn_chance (mit 5-Min-Cooldown)
    next_room = rooms.get(target)
    if next_room and next_room.get('spawn_chance') and spawn_chance():
        last_kill = zombie_kill_times.get(target, 0)
        if time.time() - last_kill >= ZOMBIE_RESPAWN_COOLDOWN:
            enemies['zombie']['health'] = enemies['zombie']['max_health']
            next_room['enemy'] = 'zombie'
            next_room['zombie_spawn'] = True
    
    # Move player
    current_room = target
    visited_rooms.add(current_room)
    add_to_history(f"Du gehst nach {direction.upper()}...")
    add_to_history("")
    describe_room()

def trigger_two_year_timeskip():
    """Triggert den 2-Jahres-Zeitsprung zum Spawn-Haus"""
    global current_room
    
    add_to_history("")
    add_to_history("Du kriechst durch den Tunnel...")
    add_to_history("")
    add_to_history("Am Ende siehst du Tageslicht. Ein verlassenes Haus.")
    add_to_history("")
    add_to_history("Du trittst hinaus. Frische Luft. Stille.")
    add_to_history("")
    add_to_history("Albert atmet tief durch.")
    add_to_history("")
    add_to_history("\"Endlich... raus aus diesem Alptraum.\"")
    add_to_history("")
    add_to_history("\"Ich brauche eine Pause. Eine lange Pause.\"")
    add_to_history("")
    add_to_history("Du verriegelst die Türen. Sammelst Vorräte.")
    add_to_history("Das Haus wird dein Versteck.")
    add_to_history("")
    add_to_history("=" * 40)
    add_to_history("")
    add_to_history("        ... 2 JAHRE SPÄTER ...")
    add_to_history("")
    add_to_history("=" * 40)
    add_to_history("")
    add_to_history("")
    add_to_history("")
    add_to_history("Du öffnest langsam die Augen.")
    add_to_history("")
    add_to_history("Du hiefst dich von der Matratze auf die auf dem Boden des Lagerraum im Keller liegt.")
    add_to_history("Geweckt vom geräusch eines Zombies der in der Nacht rein kam.")
    add_to_history("")
    
    # Teleportiere zum Lagerraum
    current_room = 'lagerraum'
    visited_rooms.add('lagerraum')  # Neuen Raum als besucht markieren
    
    add_to_history("")
    describe_room()

def describe_room():
    """Beschreibt den aktuellen Raum"""
    global game_score
    room = rooms[current_room]
    
    # Score für neuen Raum
    if current_room not in visited_rooms_desc:
        add_score('new_room')
    
    # Erste Begegnung mit Zombie im Startroom
    if current_room == 'start' and room.get('first_visit'):
        play_random_zombie_sound()
        add_to_history("")
        add_to_history("Der Zombie taumelt auf dich zu!")
        add_to_history("Tentakel zucken aus seinem Mund.")
        add_to_history("")
        room['first_visit'] = False
        return
    
    # View Mode Logik
    if view_mode == 'superbrief':
        add_to_history(f"> {room['name']}")
    elif view_mode == 'brief' and current_room in visited_rooms_desc:
        add_to_history(f"> {room['name']}")
    else:
        add_to_history(f"> {room['name']}")
        add_to_history(room['description'])
    
    visited_rooms_desc.add(current_room)
    
    # Exits anzeigen
    transitions = get_transitions_from(current_room)
    if transitions:
        exit_dirs = [d.capitalize() for d, tgt, t in transitions if not t.get('locked')]
        locked_dirs = [d.capitalize() + " (Verschlossen)" for d, tgt, t in transitions if t.get('locked')]
        all_exits = exit_dirs + locked_dirs
        add_to_history(f"Ausgänge: {', '.join(all_exits)}")
    
    if room.get('items'):
        add_to_history(f"Du siehst: {', '.join(room['items'])}")
    
    if current_room == 'wohnbereich' and room.get('zombie_spawn'):
        last_kill = zombie_kill_times.get(current_room, 0)
        if time.time() - last_kill >= ZOMBIE_RESPAWN_COOLDOWN:
            # Neuer Zombie im Wohnbereich - Health zurücksetzen
            enemies['zombie']['health'] = enemies['zombie']['max_health']
            play_random_zombie_sound()
            add_to_history("")
            add_to_history("Der Zombie taumelt auf dich zu!")
            add_to_history("Tentakel zucken aus seinem Mund.")
            add_to_history("")
            room['zombie_spawn'] = False
            return
        else:
            room['zombie_spawn'] = False
    
    if current_room == 'walmart_5' and room.get('zombie_spawn'):
        last_kill = zombie_kill_times.get(current_room, 0)
        if time.time() - last_kill >= ZOMBIE_RESPAWN_COOLDOWN:
            # Neuer Zombie im Walmart 5 - Health zurücksetzen
            enemies['zombie']['health'] = enemies['zombie']['max_health']
            play_random_zombie_sound()
            add_to_history("")
            add_to_history("Der Zombie taumelt auf dich zu!")
            add_to_history("Tentakel zucken aus seinem Mund.")
            add_to_history("")
            room['zombie_spawn'] = False
            return
        else:
            room['zombie_spawn'] = False

    if current_room == 'walmart_9' and room.get('zombie_spawn'):
        last_kill = zombie_kill_times.get(current_room, 0)
        if time.time() - last_kill >= ZOMBIE_RESPAWN_COOLDOWN:
            # Neuer Zombie im Walmart 9 - Health zurücksetzen
            enemies['zombie']['health'] = enemies['zombie']['max_health']
            play_random_zombie_sound()
            add_to_history("")
            add_to_history("Der Zombie taumelt auf dich zu!")
            add_to_history("Tentakel zucken aus seinem Mund.")
            add_to_history("")
            room['zombie_spawn'] = False
            return
        else:
            room['zombie_spawn'] = False
    # Gegner im Raum?
    if room.get('enemy'):
        enemy_key = room['enemy']
        enemy = enemies.get(enemy_key)
        if enemy and enemy['health'] > 0:
            if enemy_key in ('zombie', 'infizierter'):
                play_random_zombie_sound()
            add_to_history("")
            add_to_history(f">>> {enemy['name']} ist hier! <<<")
            add_to_history(f"Zustand: {get_enemy_health_description(enemy['health'], enemy['max_health'])}")
            player_stats['in_combat'] = True
    
    add_to_history("")


# ========================
# GRAPHISCHES KARTEN-SYSTEM (Node Graph)
# ========================

# Auto-generated node coordinates from game_map.py BFS solver
# Scaled by 2x for visual spacing in the graph view
GRAPH_LAYOUT = {rk: (coord[0] * 2, coord[1] * 2) for rk, coord in ((r, get_room_coord(r)) for r in rooms) if coord is not None}

# Load custom positions from JSON if file exists
import json as _json
try:
    with open(MAP_LAYOUT_FILE, 'r', encoding='utf-8') as _f:
        _custom = _json.load(_f)
    # Support both old format (flat dict) and new format (nested)
    if 'nodes' in _custom:
        for _rk, _pos in _custom['nodes'].items():
            if _rk in GRAPH_LAYOUT:
                GRAPH_LAYOUT[_rk] = tuple(_pos)
        custom_blocks = _custom.get('custom_blocks', [])
    else:
        # Old format: flat dict of room positions
        for _rk, _pos in _custom.items():
            if _rk in GRAPH_LAYOUT:
                GRAPH_LAYOUT[_rk] = tuple(_pos)
    print(f"[MAP] Custom layout loaded from {MAP_LAYOUT_FILE}")
except FileNotFoundError:
    pass
except Exception as _e:
    print(f"[MAP] Could not load custom layout: {_e}")

def save_map_layout():
    """Save current GRAPH_LAYOUT and custom_blocks to JSON file."""
    import json
    data = {
        'nodes': {rk: list(pos) for rk, pos in GRAPH_LAYOUT.items()},
        'custom_blocks': custom_blocks
    }
    with open(MAP_LAYOUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return MAP_LAYOUT_FILE

def get_node_at_screen_pos(mx, my, unit, cx, cy):
    """Return room_key of node at screen position (mx, my), or None."""
    hit_radius = max(8, int(20 * map_zoom))
    for rk, (rx, ry) in GRAPH_LAYOUT.items():
        nx = int(cx + rx * unit)
        ny = int(cy + ry * unit)
        if (mx - nx) ** 2 + (my - ny) ** 2 <= hit_radius ** 2:
            return rk
    return None

def screen_to_graph(sx, sy, unit, cx, cy):
    """Convert screen pixel coords to GRAPH_LAYOUT coords."""
    gx = (sx - cx) / unit
    gy = (sy - cy) / unit
    return (gx, gy)

def get_building_at_screen_pos(mx, my, unit, cx, cy):
    """Return building_key if (mx, my) is inside a building bounding box, or None."""
    for b_key, b_data in BUILDING_HIERARCHY.items():
        b_rooms = []
        for f_key, f_rooms in b_data.get('floors', {}).items():
            b_rooms.extend(f_rooms)
        if not b_rooms:
            continue
        coords = [GRAPH_LAYOUT.get(r, (0,0)) for r in b_rooms]
        min_x = min(c[0] for c in coords)
        max_x = max(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_y = max(c[1] for c in coords)
        pad = 1.2
        bx1 = cx + (min_x - pad) * unit
        by1 = cy + (min_y - pad) * unit
        bx2 = cx + (max_x + pad) * unit
        by2 = cy + (max_y + pad) * unit
        if bx1 <= mx <= bx2 and by1 <= my <= by2:
            return b_key
    return None

def get_block_at_screen_pos(mx, my, unit, cx, cy):
    """Return (block_index, handle_or_None) for custom block at screen pos.
    handle is one of 'tl','tr','bl','br' for resize corners, or 'move' for body/border."""
    handle_size = max(6, int(10 * map_zoom))
    for i, blk in enumerate(custom_blocks):
        bx1 = int(cx + blk['gx'] * unit)
        by1 = int(cy + blk['gy'] * unit)
        bx2 = int(cx + (blk['gx'] + blk['gw']) * unit)
        by2 = int(cy + (blk['gy'] + blk['gh']) * unit)
        # Check resize corners first
        corners = {
            'tl': (bx1, by1), 'tr': (bx2, by1),
            'bl': (bx1, by2), 'br': (bx2, by2)
        }
        for handle, (hx, hy) in corners.items():
            if abs(mx - hx) <= handle_size and abs(my - hy) <= handle_size:
                return (i, handle)
        # Check entire body for moving
        if bx1 <= mx <= bx2 and by1 <= my <= by2:
            return (i, 'move')
    return (None, None)

def draw_map(current_time):
    """Zeichnet den Hierarchischen Node Graph basierend auf Nested Containern"""
    screen.fill((20, 20, 25))
    
    UNIT = scale(50) * map_zoom
    center_x = screen.get_width() / 2 - (map_camera_x * map_zoom * 50)
    center_y = screen.get_height() / 2 - (map_camera_y * map_zoom * 50)
    
    def get_pos(room_k):
        rx, ry = GRAPH_LAYOUT.get(room_k, (0, 0))
        return (int(center_x + rx * UNIT), int(center_y + ry * UNIT))
        
    # (Building hierarchy boxes removed - use custom blocks [N] for grouping)


    # 1.5) Custom Blocks (User-created annotation boxes)
    for i, blk in enumerate(custom_blocks):
        bx1 = int(center_x + blk['gx'] * UNIT)
        by1 = int(center_y + blk['gy'] * UNIT)
        bx2 = int(center_x + (blk['gx'] + blk['gw']) * UNIT)
        by2 = int(center_y + (blk['gy'] + blk['gh']) * UNIT)
        bw, bh = bx2 - bx1, by2 - by1
        
        c = blk.get('color', [80, 60, 120])
        fill = (max(0, c[0]-30), max(0, c[1]-30), max(0, c[2]-30))
        border = tuple(c)
        border_w = max(1, int(2*map_zoom))
        
        if i == selected_block_idx:
            border = (255, 220, 80)
            border_w = max(2, int(3*map_zoom))
        
        pygame.draw.rect(screen, fill, (bx1, by1, bw, bh))
        pygame.draw.rect(screen, border, (bx1, by1, bw, bh), border_w)
        
        # Block name
        name = blk.get('name', 'Block')
        if block_naming and i == selected_block_idx:
            name = block_name_input + '█'
        name_surf = font_terminal.render(name.upper(), True, (200, 200, 200))
        screen.blit(name_surf, (bx1 + 10, by1 + 10))
        
        # Resize handles on selected block
        if i == selected_block_idx:
            handle_size = max(4, int(6*map_zoom))
            for hx, hy in [(bx1, by1), (bx2, by1), (bx1, by2), (bx2, by2)]:
                pygame.draw.rect(screen, (255, 220, 80), 
                    (hx - handle_size, hy - handle_size, handle_size*2, handle_size*2))

    # 2) Transitions (Kanten/Edges)
    for t in TRANSITIONS:
        r_from = t.get('from')
        r_to = t.get('to')
        
        if not r_from or not r_to: continue
        # if r_from not in visited_rooms and r_to not in visited_rooms: continue
        
        p1 = get_pos(r_from)
        p2 = get_pos(r_to)
        
        locked = t.get('locked', False)
        t_type = t.get('type', 'passage')
        
        color = (200, 50, 50) if locked else (100, 150, 200)
        thickness = max(1, int(3 * map_zoom)) if locked else max(1, int(2 * map_zoom))
        
        if t_type == 'stairs':
            # Draw dashed line for stairs
            import math
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.hypot(dx, dy)
            if dist > 0:
                dx, dy = dx / dist, dy / dist
                curr = 0
                while curr < dist:
                    nxt = min(curr + 10*map_zoom, dist)
                    start = (int(p1[0] + dx * curr), int(p1[1] + dy * curr))
                    end = (int(p1[0] + dx * nxt), int(p1[1] + dy * nxt))
                    pygame.draw.line(screen, (200, 200, 50), start, end, thickness)
                    curr += 20*map_zoom
        else:
            pygame.draw.line(screen, color, p1, p2, thickness)
            
            # Wenn gesperrt, zeichne ein kleines X in der Mitte
            if locked:
                mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
                esize = 5 * map_zoom
                pygame.draw.line(screen, (255, 50, 50), (mx-esize, my-esize), (mx+esize, my+esize), thickness)
                pygame.draw.line(screen, (255, 50, 50), (mx+esize, my-esize), (mx-esize, my+esize), thickness)

    # 3) Nodes (Räume)
    node_radius = max(4, int(15 * map_zoom))
    
    for r_key, (rx, ry) in GRAPH_LAYOUT.items():
        # if r_key not in visited_rooms and r_key != current_room: continue
        
        pos = get_pos(r_key)
        
        # Raumfarbe entscheidet Besuchs-Status
        fill_color = (60, 120, 80) if r_key in visited_rooms else (40, 40, 40)
        border_color = (100, 200, 150) if r_key in visited_rooms else (80, 80, 80)
        
        # Highlight hovered/dragged node
        if r_key == node_drag_key:
            border_color = (255, 200, 50)
            fill_color = (100, 80, 30)
        elif r_key == node_hovered_key:
            border_color = (200, 200, 100)
        
        pygame.draw.circle(screen, fill_color, pos, node_radius)
        pygame.draw.circle(screen, border_color, pos, node_radius, max(1, int(2*map_zoom)))
        
        # Highlight Player
        if r_key == current_room:
            # Pulsing ring
            pulse = abs(math.sin(current_time * 0.005)) * 150 + 50
            pygame.draw.circle(screen, (200, 255, 255), pos, int(node_radius * 1.5), max(1, int(2*map_zoom)))
            # Player dot
            pygame.draw.circle(screen, (255, 255, 255), pos, int(node_radius * 0.5))
            
        # Raumnamen anzeigen (nur wenn man nah herangezoomt hat, um Clutter zu vermeiden)
        if map_zoom > 0.6 or r_key == current_room:
            lbl = r_key.replace('_', ' ').title()
            # Wenn current room, zeige fett / groß
            fnt = font_terminal if r_key == current_room else font_tiny
            col = (255, 255, 255) if r_key == current_room else (180, 180, 180)
            
            lbl_surf = fnt.render(lbl, True, col)
            screen.blit(lbl_surf, (pos[0] - lbl_surf.get_width()//2, pos[1] + node_radius + 5))
            
    # UI Overlay Legend
    title_text = "HIERARCHICAL CONTAINER SYSTEM MAP"
    title_surf = font_terminal.render(title_text, True, (200, 255, 255))
    screen.blit(title_surf, (30, 30))
    pygame.draw.line(screen, (200, 255, 255), (30, 30 + title_surf.get_height() + 5), (30 + title_surf.get_width() + 50, 30 + title_surf.get_height() + 5), 2)
    
    # Legend Box
    leg_x, leg_y = 30, screen.get_height() - 150
    pygame.draw.rect(screen, (30, 30, 30, 200), (leg_x-10, leg_y-10, 250, 130))
    pygame.draw.rect(screen, (100, 100, 100), (leg_x-10, leg_y-10, 250, 130), 1)
    
    screen.blit(font_tiny.render("LEGENDE:", True, (200, 200, 200)), (leg_x, leg_y))
    
    pygame.draw.line(screen, (100, 150, 200), (leg_x, leg_y+30), (leg_x+25, leg_y+30), 3)
    screen.blit(font_tiny.render("Offen. Übergang", True, (150, 150, 150)), (leg_x+35, leg_y+20))
    
    pygame.draw.line(screen, (200, 50, 50), (leg_x, leg_y+55), (leg_x+25, leg_y+55), 3)
    screen.blit(font_tiny.render("Gesperrter Übergang", True, (150, 150, 150)), (leg_x+35, leg_y+45))
    
    # Treppen strich-linie als legend
    pygame.draw.line(screen, (200, 200, 50), (leg_x, leg_y+80), (leg_x+5, leg_y+80), 2)
    pygame.draw.line(screen, (200, 200, 50), (leg_x+10, leg_y+80), (leg_x+15, leg_y+80), 2)
    pygame.draw.line(screen, (200, 200, 50), (leg_x+20, leg_y+80), (leg_x+25, leg_y+80), 2)
    screen.blit(font_tiny.render("Treppen / Etage", True, (150, 150, 150)), (leg_x+35, leg_y+70))
    
    # Controls Help Bottom Right
    # Controls Help Bottom Right
    help_surf = font_tiny.render("[M/ESC] Zurück  [Drag] Pan  [Rechtsklick] Node/Block ziehen  [S] Speichern  [N] Neuer Block  [F2] Umbenennen  [Entf] Löschen", True, (150, 180, 200))
    screen.blit(help_surf, (screen.get_width() - help_surf.get_width() - 30, screen.get_height() - 40))
    
    # Show save indicator
    if hasattr(draw_map, '_save_msg_time') and current_time - draw_map._save_msg_time < 2000:
        save_surf = font_terminal.render("✔ Layout gespeichert!", True, (100, 255, 100))
        screen.blit(save_surf, (screen.get_width()//2 - save_surf.get_width()//2, 80))

# === CLASSIC MECHANICS: Helper-Funktionen ===

def add_score(action_key, amount=None):
    """Zork-style Punkte vergeben."""
    global game_score
    pts = amount if amount is not None else SCORE_VALUES.get(action_key, 0)
    if pts > 0:
        game_score += pts

def format_elapsed_time():
    """Formatiert verstrichene Pygame-Ticks als HH:MM:SS."""
    if game_start_ticks == 0:
        return "00:00:00"
    elapsed_ms = pygame.time.get_ticks() - game_start_ticks
    total_secs = elapsed_ms // 1000
    h = total_secs // 3600
    m = (total_secs % 3600) // 60
    s = total_secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def save_game():
    """Speichert den Spielstand als JSON."""
    import json
    room_items_state = {}
    for rk, rd in rooms.items():
        room_items_state[rk] = rd.get('items', [])[:]
    container_states = {}
    for ik, idef in ITEM_DEFS.items():
        if idef.is_container:
            container_states[ik] = {
                'contents': idef.contents[:],
                'is_open': idef.is_open
            }
    transition_locks = {}
    for t in TRANSITIONS:
        transition_locks[t['id']] = t.get('locked', False)
    save_data = {
        'current_room': current_room,
        'player_inventory': player_inventory[:],
        'player_stats': dict(player_stats),
        'game_score': game_score,
        'game_moves': game_moves,
        'view_mode': view_mode,
        'visited_rooms': list(visited_rooms),
        'visited_rooms_desc': list(visited_rooms_desc),
        'room_items': room_items_state,
        'container_states': container_states,
        'transition_locks': transition_locks,
        'elapsed_ms': pygame.time.get_ticks() - game_start_ticks,
        'bibliothek_4_schrank_geschoben': bibliothek_4_schrank_geschoben,
        'haus1_tür_auf': haus1_tür_auf,
        'item_charges': {ik: idef.charge for ik, idef in ITEM_DEFS.items() if idef.max_charge >= 0},
    }
    try:
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        add_to_history("Spiel gespeichert.")
        add_to_history("")
    except Exception as e:
        add_to_history(f"Fehler beim Speichern: {e}")
        add_to_history("")

def restore_game():
    """Lädt einen gespeicherten Spielstand."""
    import json
    global current_room, player_inventory, game_score, game_moves, view_mode
    global visited_rooms, visited_rooms_desc, game_start_ticks
    global bibliothek_4_schrank_geschoben, haus1_tür_auf
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        add_to_history("Kein Spielstand gefunden.")
        add_to_history("")
        return
    except Exception as e:
        add_to_history(f"Fehler beim Laden: {e}")
        add_to_history("")
        return
    current_room = data['current_room']
    player_inventory.clear()
    player_inventory.extend(data['player_inventory'])
    player_stats.update(data['player_stats'])
    game_score = data.get('game_score', 0)
    game_moves = data.get('game_moves', 0)
    view_mode = data.get('view_mode', 'verbose')
    visited_rooms.clear()
    visited_rooms.update(data.get('visited_rooms', []))
    visited_rooms_desc.clear()
    visited_rooms_desc.update(data.get('visited_rooms_desc', []))
    for rk, items_list in data.get('room_items', {}).items():
        if rk in rooms:
            rooms[rk]['items'] = items_list
    for ik, cstate in data.get('container_states', {}).items():
        if ik in ITEM_DEFS and ITEM_DEFS[ik].is_container:
            ITEM_DEFS[ik].contents = cstate.get('contents', [])
            ITEM_DEFS[ik].is_open = cstate.get('is_open', False)
    for t in TRANSITIONS:
        if t['id'] in data.get('transition_locks', {}):
            t['locked'] = data['transition_locks'][t['id']]
    bibliothek_4_schrank_geschoben = data.get('bibliothek_4_schrank_geschoben', False)
    haus1_tür_auf = data.get('haus1_tür_auf', False)
    # Restore item charges (light sources)
    for ik, charge_val in data.get('item_charges', {}).items():
        if ik in ITEM_DEFS:
            ITEM_DEFS[ik].charge = charge_val
    elapsed = data.get('elapsed_ms', 0)
    game_start_ticks = pygame.time.get_ticks() - elapsed
    game_history.clear()
    add_to_history("Spielstand geladen.")
    add_to_history("")
    describe_room()

def handle_container_open(container_key):
    """Öffne einen Container."""
    idef = ITEM_DEFS.get(container_key)
    if not idef or not idef.is_container:
        add_to_history(f"'{get_item_name(container_key)}' ist kein Behälter.")
        add_to_history("")
        return
    if container_key not in player_inventory and container_key not in rooms[current_room].get('items', []):
        add_to_history(f"Du siehst hier keinen '{get_item_name(container_key)}'.")
        add_to_history("")
        return
    if idef.is_open:
        add_to_history(f"{get_item_name(container_key)} ist bereits offen.")
    else:
        idef.is_open = True
        add_to_history(f"Du öffnest {get_item_name(container_key)}.")
        if idef.contents:
            names = [get_item_name(k) for k in idef.contents]
            add_to_history(f"Darin: {', '.join(names)}")
        else:
            add_to_history("Es ist leer.")
    add_to_history("")

def handle_container_close(container_key):
    """Schließe einen Container."""
    idef = ITEM_DEFS.get(container_key)
    if not idef or not idef.is_container:
        add_to_history(f"'{get_item_name(container_key)}' ist kein Behälter.")
        add_to_history("")
        return
    if not idef.is_open:
        add_to_history(f"{get_item_name(container_key)} ist bereits geschlossen.")
    else:
        idef.is_open = False
        add_to_history(f"Du schließt {get_item_name(container_key)}.")
    add_to_history("")

def handle_put_in(item_key, container_key):
    """Lege Item in Container (mit Implicit Take)."""
    global game_score
    idef_c = ITEM_DEFS.get(container_key)
    if not idef_c or not idef_c.is_container:
        add_to_history(f"'{get_item_name(container_key)}' ist kein Behälter.")
        add_to_history("")
        return
    if not idef_c.is_open:
        add_to_history(f"{get_item_name(container_key)} ist geschlossen. Öffne ihn zuerst.")
        add_to_history("")
        return
    # Check nesting: item itself cannot be a container with contents inside another container
    idef_item = ITEM_DEFS.get(item_key)
    if idef_item and idef_item.is_container and idef_item.contents:
        add_to_history("Du kannst keinen gefüllten Behälter in einen anderen legen.")
        add_to_history("")
        return
    # Check if container is nested inside another container
    for other_key, other_def in ITEM_DEFS.items():
        if other_def.is_container and container_key in other_def.contents:
            add_to_history("Du kannst nicht hineingreifen – der Behälter ist zu tief verschachtelt.")
            add_to_history("")
            return
    # Implicit Take: if item is in room but not in inventory, take it first
    room = rooms[current_room]
    if item_key not in player_inventory:
        if item_key in room.get('items', []):
            room['items'].remove(item_key)
            player_inventory.append(item_key)
            add_to_history(f"(Zuerst genommen: {get_item_name(item_key)})")
            add_score('item_pickup')
        else:
            add_to_history(f"Du hast kein '{get_item_name(item_key)}'.")
            add_to_history("")
            return
    if len(idef_c.contents) >= idef_c.capacity:
        add_to_history(f"{get_item_name(container_key)} ist voll.")
        add_to_history("")
        return
    player_inventory.remove(item_key)
    idef_c.contents.append(item_key)
    add_to_history(f"Du legst {get_item_name(item_key)} in {get_item_name(container_key)}.")
    add_to_history("")

def handle_take_from(item_key, container_key):
    """Nimm Item aus Container."""
    idef_c = ITEM_DEFS.get(container_key)
    if not idef_c or not idef_c.is_container:
        add_to_history(f"'{get_item_name(container_key)}' ist kein Behälter.")
        add_to_history("")
        return
    if not idef_c.is_open:
        add_to_history(f"{get_item_name(container_key)} ist geschlossen.")
        add_to_history("")
        return
    # Check nesting depth
    for other_key, other_def in ITEM_DEFS.items():
        if other_def.is_container and container_key in other_def.contents:
            add_to_history("Du kannst nicht hineingreifen – zu tief verschachtelt.")
            add_to_history("")
            return
    if item_key not in idef_c.contents:
        add_to_history(f"'{get_item_name(item_key)}' ist nicht in {get_item_name(container_key)}.")
        add_to_history("")
        return
    idef_c.contents.remove(item_key)
    player_inventory.append(item_key)
    add_to_history(f"Du nimmst {get_item_name(item_key)} aus {get_item_name(container_key)}.")
    add_score('item_pickup')
    add_to_history("")

def handle_look_in(container_key):
    """Schaue in einen Container."""
    idef = ITEM_DEFS.get(container_key)
    if not idef or not idef.is_container:
        add_to_history(f"'{get_item_name(container_key)}' ist kein Behälter.")
        add_to_history("")
        return
    if not idef.is_open and not idef.is_transparent:
        add_to_history(f"{get_item_name(container_key)} ist geschlossen.")
        add_to_history("")
        return
    if idef.contents:
        names = [get_item_name(k) for k in idef.contents]
        add_to_history(f"In {get_item_name(container_key)}: {', '.join(names)}")
    else:
        add_to_history(f"{get_item_name(container_key)} ist leer.")
    add_to_history("")

def process_command(command):
    """Verarbeitet Spielerbefehle"""
    global current_room, prolog_shown, prolog_line_index, qte_active, qte_input, command_history, history_index, current_state, map_camera_x, map_camera_y, map_zoom, map_coords_dirty, map_cursor_room
    global pending_ambiguity, game_moves, view_mode, game_score
    
    # Füge Command zur History hinzu (außer im QTE oder Prolog)
    if prolog_shown and not qte_active and command.strip():
        command_history.append(command)
        # Begrenze History auf 50 Einträge
        if len(command_history) > 50:
            command_history.pop(0)
    
    # Reset history index
    history_index = -1
    
    # QTE-Modus: Taste eingeben
    if qte_active:
        qte_input += command.upper()
        return
    
    # Prolog-Modus: Enter drücken zeigt mehr Text
    if not prolog_shown:
        if prolog_line_index < len(prolog_lines):
            # Zeige nächste 3 Zeilen
            end_index = min(prolog_line_index + 3, len(prolog_lines))
            for i in range(prolog_line_index, end_index):
                add_to_history(prolog_lines[i])
            prolog_line_index = end_index
            
            # Prüfe ob Prolog fertig
            if prolog_line_index >= len(prolog_lines):
                prolog_shown = True
                add_to_history("")
                add_to_history("=== TERMINAL AKTIVIERT ===")
                add_to_history("")
                describe_room()
        return
    
    cmd = command.lower().strip()

    # === 9-Letter Truncation ===
    words = cmd.split()
    words = [w[:9] for w in words]
    # Resolve truncated words back to full item/weapon keys (prefix match)
    room = rooms.get(current_room, {})
    all_keys = set(ITEM_DEFS.keys()) | set(weapons.keys()) | set(room.get('items', [])) | set(player_inventory)
    resolved_words = []
    for w in words:
        matches = [k for k in all_keys if k[:9] == w and k != w]
        if len(matches) == 1:
            resolved_words.append(matches[0])
        else:
            resolved_words.append(w)
    words = resolved_words
    cmd = ' '.join(words)

    # === Ambiguity Resolution ===
    if pending_ambiguity is not None:
        choice = cmd.strip()
        candidates = pending_ambiguity['candidates']
        matched = [c for c in candidates if c.startswith(choice) or choice in c]
        if len(matched) == 1:
            resolved_cmd = f"{pending_ambiguity['action']} {matched[0]}"
            pending_ambiguity = None
            process_command(resolved_cmd)
            return
        elif choice.isdigit() and 1 <= int(choice) <= len(candidates):
            resolved_cmd = f"{pending_ambiguity['action']} {candidates[int(choice)-1]}"
            pending_ambiguity = None
            process_command(resolved_cmd)
            return
        else:
            add_to_history("Abgebrochen.")
            add_to_history("")
            pending_ambiguity = None
            return

    # Zähle Züge (nur echte Spielerbefehle)
    if cmd and prolog_shown:
        game_moves += 1
        # Tick hidden systems (hunger, light, recovery)
        tick_msgs = tick_hidden_systems()
        for _tmsg in tick_msgs:
            add_to_history(_tmsg)

    if cmd in ['hilfe', 'help', '?']:
        add_to_history("DEAD WORLD - BEFEHLE")
        add_to_history("")
        add_to_history("Bewegung:")
        add_to_history("  n, norden - Gehe nach Norden")
        add_to_history("  o, osten - Gehe nach Osten")
        add_to_history("  s, süden - Gehe nach Süden")
        add_to_history("  w, westen - Gehe nach Westen")
        add_to_history("  r, runter - Gehe nach Unten")
        add_to_history("  h, hoch - Gehe nach Oben")
        add_to_history("  gehe [richtung] - Alternative Schreibweise")
        add_to_history("  schaue, look - Raum beschreiben")
        add_to_history("")
        add_to_history("Gegenstände:")
        add_to_history("  nimm [item] - Item aufheben")
        add_to_history("  lese [item] - Item lesen (Zeitung, Notizen)")
        add_to_history("  esse [item] - Essen/Trinken konsumieren")
        add_to_history("  inventar, inv - Inventar anzeigen")
        add_to_history("")
        add_to_history("Kampf:")
        add_to_history("  ausrüsten [waffe] - Waffe ausrüsten")
        add_to_history("  schlag [ziel] - Nahkampf")
        add_to_history("  stich auf [ziel] - Mit Messer angreifen")
        add_to_history("  schieße auf [ziel] - Schusswaffe nutzen")
        add_to_history("")
        add_to_history("Terminal:")
        add_to_history("  clear, cls - Terminal leeren")
        add_to_history("  echo [text] - Text ausgeben")
        add_to_history("  time - Aktuelle Zeit anzeigen")
        add_to_history("  whoami - Charakter-Info")
        add_to_history("  karte, map - Weltkarte anzeigen")
        add_to_history("")
        add_to_history("System:")
        add_to_history("  save, speichern - Spiel speichern")
        add_to_history("  restore, laden - Spiel laden")
        add_to_history("  score, punkte - Punkte anzeigen")
        add_to_history("  zeit - Spielzeit anzeigen")
        add_to_history("  diagnose, d - Gesundheits- und Zustandsbericht")
        add_to_history("  info - Spielinfo")
        add_to_history("  q, quit - Beenden")
        add_to_history("  verbose/brief/superbrief - Beschreibungsmodus")
        add_to_history("  neu - Neustart nach Tod")
        add_to_history("")
        add_to_history("Behälter:")
        add_to_history("  öffne/schließe [behälter]")
        add_to_history("  lege [item] in [behälter]")
        add_to_history("  nimm [item] aus [behälter]")
        add_to_history("  schaue in [behälter]")
        add_to_history("")
    
    elif cmd.startswith('gehe '):
        direction = cmd[5:].strip()
        move_direction(direction)
    
    # Direkte Richtungsbefehle: n, o, s, w
    elif cmd in ['n', 'norden', 'nord']:
        move_direction('norden')
    
    elif cmd in ['o', 'osten', 'ost']:
        move_direction('osten')
    
    elif cmd in ['s', 'süden', 'süd', 'sued']:
        move_direction('süden')
    
    elif cmd in ['w', 'westen', 'west']:
        move_direction('westen')
    
    elif cmd in ['so', 'südosten', 'suedosten', 'süd-osten', 'sued-osten']:
        move_direction('südosten')
    
    elif cmd in ['nw', 'nordwesten', 'nord-westen']:
        move_direction('nordwesten')

    elif cmd in ['h', 'hoch', 'up']:
        move_direction('hoch')
    
    elif cmd in ['r', 'runter', 'down']:
        move_direction('runter')
    
    elif cmd == 'nimm':
        # Ambiguity: kein Objekt angegeben
        room = rooms[current_room]
        available = room.get('items', [])
        if len(available) == 1:
            process_command(f'nimm {available[0]}')
        elif len(available) > 1:
            add_to_history("Was möchtest du nehmen?")
            for idx, it in enumerate(available, 1):
                add_to_history(f"  {idx}. {get_item_name(it)}")
            pending_ambiguity = {'action': 'nimm', 'candidates': available[:], 'original_cmd': 'nimm'}
            add_to_history("")
        else:
            add_to_history("Hier gibt es nichts zum Nehmen.")
            add_to_history("")
    
    elif cmd.startswith('nimm ') and ' aus ' not in cmd:
        item = cmd[5:].strip()
        room = rooms[current_room]
        if item in room['items']:
            # Encumbrance check
            idef = ITEM_DEFS.get(item)
            item_weight = idef.weight if idef else 1
            if get_player_carry_weight() + item_weight > player_stats['max_weight']:
                add_to_history("Deine Last ist zu schwer. Du kannst nichts mehr tragen.")
                add_to_history("")
            else:
                room['items'].remove(item)
                player_inventory.append(item)
                add_to_history(f"Du nimmst {get_item_name(item)}.")
                add_score('item_pickup')
                enc = get_encumbrance_description()
                if enc:
                    add_to_history(enc)
                add_to_history("")
        else:
            add_to_history(f"Hier gibt es kein '{item}'.")
            add_to_history("")
    
    elif cmd.startswith('lese ') or cmd.startswith('lies ') or cmd.startswith('lesen '):
        # Extrahiere Item-Name
        if cmd.startswith('lese '):
            item = cmd[5:].strip()
        elif cmd.startswith('lies '):
            item = cmd[5:].strip()
        elif cmd.startswith('lesen '):
            item = cmd[6:].strip()
        
        read_item(item)
        if item == 'tagebuch':
            add_to_history("Im Tagebuch hast du deine letzen 2 Jahre in diesem haus Dokumentiert.")
            add_to_history("Jeder einzelne zombie oder Mensch der versuchte reinzukommen.")
        elif item == 'Stück Papier':
            add_to_history("Ein stück Papier, es hat blut schmieren drauf, teile der Notiz dadurch unlesbar.")
            add_to_history("Sie sind üb....... nirgends ist man sicher. Alles geshah nu........... em Präs......... abor.")
    
    elif cmd in ['inventar', 'inv', 'i']:
        add_to_history("INVENTAR")
        add_to_history("")
        
        if player_inventory:
            item_names = [get_item_name(it) for it in player_inventory]
            add_to_history(f"Items: {', '.join(item_names)}")
        else:
            add_to_history("Items: Leer")
        
        if player_stats['equipped_weapon']:
            weapon = weapons[player_stats['equipped_weapon']]
            add_to_history(f"Waffe: {weapon['name']}")
        else:
            add_to_history("Waffe: Keine")
        
        # Fäuste Level anzeigen (qualitativ)
        fist_level = player_stats['fist_level']
        if fist_level >= 5:
            add_to_history("Fäuste: Meisterhaft")
        elif fist_level >= 3:
            add_to_history("Fäuste: Erfahren")
        else:
            add_to_history("Fäuste: Untrainiert")
        
        # Qualitative Zustandsanzeige
        add_to_history("")
        add_to_history(get_health_description())
        enc = get_encumbrance_description()
        if enc:
            add_to_history(enc)
        add_to_history("")
        
    elif cmd.startswith('esse ') or cmd.startswith('iss '):
        # Esse-Befehl: Essen/Trinken konsumieren (Zork-inspiriert)
        if cmd.startswith('esse '):
            item = cmd[5:].strip()
        else:
            item = cmd[4:].strip()
        
        if item not in player_inventory:
            add_to_history(f"Du hast kein '{item}' im Inventar.")
            add_to_history("")
        elif item not in food_items:
            add_to_history(f"'{item}' kann man nicht essen.")
            add_to_history("")
        else:
            food = food_items[item]
            old_hp = player_stats['health']
            player_stats['health'] = min(100, player_stats['health'] + food['heal'])
            healed = player_stats['health'] - old_hp
            player_inventory.remove(item)
            # Reset hunger and boost strength
            player_stats['hunger'] = max(0, player_stats['hunger'] - 30)
            player_stats['turns_since_last_meal'] = 0
            player_stats['strength'] = min(100, player_stats['strength'] + food['heal'] // 2)
            
            add_to_history(food['message'])
            if healed > 0:
                if healed >= 30:
                    add_to_history("Du fühlst dich deutlich besser.")
                elif healed >= 15:
                    add_to_history("Etwas Kraft kehrt in deinen Körper zurück.")
                else:
                    add_to_history("Du fühlst dich ein wenig gestärkt.")
            else:
                add_to_history("Du bist bereits in guter Verfassung.")
            if player_stats['hunger'] <= 0:
                add_to_history("Dein Hunger ist gestillt.")
            add_to_history("")
    
    elif cmd in ['schaue', 'look', 'l']:
        describe_room()
    
    elif cmd in ['karte', 'map']:
        bldg_name, bldg_title, floor = get_room_context(current_room)
        room_name = rooms.get(current_room, {}).get('name', current_room)
        
        add_to_history(">>> STANDORT INFO <<<")
        add_to_history(f"Gebäude: {bldg_title}")
        add_to_history(f"Etage:   {floor.capitalize()}")
        add_to_history(f"Raum:    {room_name}")
        add_to_history("")
        add_to_history("Gefundene Ausgänge:")
        
        transitions = get_transitions_from(current_room)
        if not transitions:
            add_to_history("  (Keine sichtbaren Ausgänge)")
        else:
            for d, tgt, t in transitions:
                tgt_name = rooms.get(tgt, {}).get('name', tgt)
                t_type = t.get('type', 'passage')
                lock_str = " [VERSCHLOSSEN]" if t.get('locked') else ""
                icon = "🚪" if t_type in ['door', 'entrance'] else "🪜" if t_type == 'stairs' else "➡️"
                add_to_history(f"  {d.capitalize():<12} {icon} {tgt_name} {lock_str}")
        
        add_to_history("")
    
    elif cmd.startswith('ausrüsten '):
        weapon_key = cmd[10:].strip()
        equip_weapon(weapon_key)
    
    elif cmd.startswith('schieße auf ') or cmd.startswith('schiesse auf ') or cmd.startswith('schieße ') or cmd.startswith('schiesse '):
        # Extrahiere Ziel
        if 'auf ' in cmd:
            target = cmd.split('auf ', 1)[1].strip()
        else:
            target = cmd.split('schieße ', 1)[1].strip() if 'schieße ' in cmd else cmd.split('schiesse ', 1)[1].strip()
        
        # Spezialfall: Schießen ohne Waffe im ersten Raum
        room = rooms[current_room]
        if current_room == 'start' and room.get('enemy') == 'zombie' and not player_stats['equipped_weapon']:
            add_to_history("Du hast keine Waffe!")
            add_to_history("Du versuchst wild um dich zu schlagen...")
            add_to_history("")
            
            # 30% Chance zu sterben
            if random.random() < 0.3:
                add_to_history("Der Zombie ist schneller!")
                add_to_history("Tentakel durchbohren deine Brust.")
                add_to_history("Schwärze übernimmt deine Vision...")
                add_to_history("")
                add_to_history("=== DU BIST GESTORBEN ===")
                add_to_history("")
                player_stats['health'] = 0
                # Reset Player Stats
                player_stats['health'] = 100
                player_stats['strength'] = 100
                player_stats['hunger'] = 0
                player_stats['turns_since_last_meal'] = 0
                player_stats['last_recovery_turn'] = 0
                player_stats['equipped_weapon'] = None
                player_stats['weapon_type'] = None
                player_stats['in_combat'] = False
                player_stats['fist_level'] = 1
                
                # Reset Enemies
                for enemy_key in enemies:
                    enemies[enemy_key]['health'] = enemies[enemy_key]['max_health']
                
                # Reset Rooms
                rooms['start']['first_visit'] = True
                rooms['start']['enemy'] = 'zombie'
                rooms['start']['items'] = ['feuerlöscher', 'zeitung']
                reset_transitions()
                
                start_game()
            else:
                add_to_history("Du stolperst zurück und weichst aus!")
                add_to_history("Schnell, nimm eine Waffe!")
            add_to_history("")
        else:
            ranged_attack(target)
    
    elif cmd.startswith('schlag ') or cmd.startswith('schlage '):
        # Prüfe ob "mit" im Befehl ist
        if ' mit ' in cmd:
            # Format: "schlag [ziel] mit [waffe]"
            parts = cmd.split(' ', 1)[1]  # Entferne "schlag"/"schlage"
            target_and_weapon = parts.split(' mit ')
            if len(target_and_weapon) == 2:
                target = target_and_weapon[0].strip()
                weapon_name = target_and_weapon[1].strip()
                # Ziel-Validierung
                room = rooms[current_room]
                enemy_in_room = room.get('enemy', None)
                if not enemy_in_room:
                    add_to_history("Es gibt hier nichts zum Angreifen!")
                    add_to_history("")
                else:
                    enemy = enemies.get(enemy_in_room)
                    t = target.lower().strip()
                    enemy_words = [enemy_in_room] + enemy['name'].lower().replace('-', ' ').split()
                    if t == enemy_in_room or t in enemy_words:
                        attack_with_weapon(target, weapon_name)
                    else:
                        add_to_history(f"Hier ist kein '{target}'.")
                        if enemy:
                            add_to_history(f"Hier ist: {enemy['name']}")
                        add_to_history("")
            else:
                add_to_history("Falsches Format. Nutze: schlag [ziel] mit [waffe]")
                add_to_history("")
        else:
            target = cmd.split(' ', 1)[1].strip()
            # Ziel-Validierung
            room = rooms[current_room]
            enemy_in_room = room.get('enemy', None)
            if not enemy_in_room:
                add_to_history("Es gibt hier nichts zum Angreifen!")
                add_to_history("")
            else:
                enemy = enemies.get(enemy_in_room)
                t = target.lower().strip()
                enemy_words = [enemy_in_room] + enemy['name'].lower().replace('-', ' ').split()
                if t == enemy_in_room or t in enemy_words:
                    unarmed_attack(target)
                else:
                    add_to_history(f"Hier ist kein '{target}'.")
                    if enemy:
                        add_to_history(f"Hier ist: {enemy['name']}")
                    add_to_history("")
    
    elif cmd == 'clear' or cmd == 'cls':
        game_history.clear()
        add_to_history("Terminal geleert.")
        add_to_history("")
    
    # status/stats removed — use 'diagnose' or 'd' instead
    
    elif cmd.startswith('stich auf '):
        target = cmd[10:].strip()
        melee_attack(target)
    
    # Terminal-Befehle
    elif cmd == 'neu':
        # Neues Spiel starten - setzt alles zurück
        # Reset Player Stats
        player_stats['health'] = 100
        player_stats['strength'] = 100
        player_stats['hunger'] = 0
        player_stats['turns_since_last_meal'] = 0
        player_stats['last_recovery_turn'] = 0
        player_stats['equipped_weapon'] = None
        player_stats['weapon_type'] = None
        player_stats['in_combat'] = False
        player_stats['fist_level'] = 1
        
        # Reset Enemies
        for enemy_key in enemies:
            enemies[enemy_key]['health'] = enemies[enemy_key]['max_health']
        
        # Reset Light charges
        for idef in ITEM_DEFS.values():
            if idef.max_charge >= 0:
                idef.charge = idef.max_charge
        
        # Reset Rooms
        rooms['start']['first_visit'] = True
        rooms['start']['enemy'] = 'zombie'
        rooms['start']['items'] = ['feuerlöscher', 'zeitung']
        reset_transitions()
        
        start_game()
    
    
    elif cmd.startswith('echo '):
        text = cmd[5:].strip()
        add_to_history(text)
        add_to_history("")
    
    elif cmd == 'time':
        now = datetime.datetime.now()
        add_to_history(f"Aktuelle Zeit: {now.strftime('%H:%M:%S')}")
        add_to_history(f"Datum: {now.strftime('%d.%m.%Y')}")
        add_to_history("")
    
    elif cmd == 'whoami':
        add_to_history("Name: Albert Wesker Cristal")
        add_to_history("Status: Überlebender")
        add_to_history("Standort: Bunker")
        add_to_history("")
    
    elif cmd in ['karte', 'map']:
        bldg_name, bldg_title, floor = get_room_context(current_room)
        room_name = rooms.get(current_room, {}).get('name', current_room)
        
        add_to_history(">>> STANDORT INFO <<<")
        add_to_history(f"Gebäude: {bldg_title}")
        add_to_history(f"Etage:   {floor.capitalize()}")
        add_to_history(f"Raum:    {room_name}")
        add_to_history("")
        add_to_history("Gefundene Ausgänge:")
        
        transitions = get_transitions_from(current_room)
        if not transitions:
            add_to_history("  (Keine sichtbaren Ausgänge)")
        else:
            for d, tgt, t in transitions:
                tgt_name = rooms.get(tgt, {}).get('name', tgt)
                t_type = t.get('type', 'passage')
                lock_str = " [VERSCHLOSSEN]" if t.get('locked') else ""
                icon = "🚪" if t_type in ['door', 'entrance'] else "🪜" if t_type == 'stairs' else "➡️"
                add_to_history(f"  {d.capitalize():<12} {icon} {tgt_name} {lock_str}")
        
        add_to_history("")
    
    elif cmd in ['schieben', 'schieb', 'regal schieben', 'schrank schieben', 'bücherregal schieben']:
        global bibliothek_4_schrank_geschoben
        if current_room == 'bibliothek_3':
            if not bibliothek_4_schrank_geschoben:
                bibliothek_4_schrank_geschoben = True
                unlock_transition('bib_3_4')
                add_to_history("Du stemmst dich gegen das schwere Bücherregal...")
                add_to_history("Mit aller Kraft schiebst du es zur Seite!")
                add_to_history("Der Weg nach NORDEN ist jetzt frei.")
                add_to_history("")
            else:
                add_to_history("Das Bücherregal wurde bereits zur Seite geschoben.")
                add_to_history("")
        else:
            add_to_history("Hier gibt es nichts zum Schieben.")#Haustür
            add_to_history("") 

    elif cmd in ['Brech auf', 'Zerhacke tür', 'schlage tür auf', 'tür aufbrechen', 'tür mit Axt aufschalgen']:
        global haus1_tür_auf
        if current_room == 'haus1' and 'axt' in player_inventory:
            if not haus1_tür_auf:
                haus1_tür_auf = True
                unlock_transition('haus1_tuer')
                add_to_history("Du nimmst die Axt in die Hände")
                add_to_history("Mit wucht schlägst du mit der Axt auf die Tür ein")
                add_to_history("Man kann nun ins Haus rein")
                add_to_history("")
            else:
                add_to_history("Die Tür ist bereits aufgebrochen")
                add_to_history("")
        else:
            add_to_history("Du hast nichts um die Tür zu öffnen.")
            add_to_history("")
    
    # === CONTAINER-BEFEHLE ===
    elif cmd.startswith('öffne ') or cmd.startswith('oeffne '):
        target = cmd.split(' ', 1)[1].strip()[:9]
        handle_container_open(target)
    
    elif cmd.startswith('schließ') or cmd.startswith('schliess'):
        parts = cmd.split(' ', 1)
        if len(parts) > 1:
            target = parts[1].strip()[:9]
            handle_container_close(target)
        else:
            add_to_history("Was willst du schließen?")
            add_to_history("")
    
    elif ' in ' in cmd and cmd.startswith('lege '):
        # lege X in Y
        rest = cmd[5:].strip()
        parts = rest.split(' in ', 1)
        if len(parts) == 2:
            handle_put_in(parts[0].strip(), parts[1].strip())
        else:
            add_to_history("Format: lege [item] in [behälter]")
            add_to_history("")
    
    elif ' aus ' in cmd and cmd.startswith('nimm '):
        # nimm X aus Y
        rest = cmd[5:].strip()
        parts = rest.split(' aus ', 1)
        if len(parts) == 2:
            handle_take_from(parts[0].strip(), parts[1].strip())
        else:
            add_to_history("Format: nimm [item] aus [behälter]")
            add_to_history("")
    
    elif cmd.startswith('schaue in ') or cmd.startswith('schau in '):
        target = cmd.split(' in ', 1)[1].strip()
        handle_look_in(target)
    
    # === VIEW MODE BEFEHLE ===
    elif cmd in ['verbose', 'ausführl', 'ausführli']:
        view_mode = 'verbose'
        add_to_history("Modus: VERBOSE – Volle Beschreibungen.")
        add_to_history("")
    
    elif cmd in ['brief', 'kurz']:
        view_mode = 'brief'
        add_to_history("Modus: BRIEF – Kurze Beschreibungen bei Wiederbesuch.")
        add_to_history("")
    
    elif cmd in ['superbrie', 'superkur', 'superkurz']:
        view_mode = 'superbrief'
        add_to_history("Modus: SUPERBRIEF – Nur Raumnamen.")
        add_to_history("")
    
    # === SYSTEM-BEFEHLE ===
    elif cmd == 'info':
        add_to_history("═══════════════════════════════")
        add_to_history("  DEAD WORLD v1.0")
        add_to_history("  Ein Zork-inspiriertes")
        add_to_history("  Survival Text-Adventure")
        add_to_history("  mit Pygame Terminal-UI")
        add_to_history("═══════════════════════════════")
        add_to_history(f"  Züge: {game_moves}")
        add_to_history(f"  Punkte: {game_score}")
        add_to_history(f"  Spielzeit: {format_elapsed_time()}")
        add_to_history("")
    
    elif cmd in ['q', 'quit', 'beenden']:
        add_to_history("═══ SPIELENDE ═══")
        add_to_history(f"Punkte: {game_score}")
        add_to_history(f"Züge: {game_moves}")
        add_to_history(f"Spielzeit: {format_elapsed_time()}")
        add_to_history("")
        add_to_history("Willst du wirklich beenden? (Tippe 'neu' für Neustart)")
        add_to_history("")
    
    elif cmd in ['save', 'speicher', 'speichern']:
        save_game()
    
    elif cmd in ['restore', 'laden']:
        restore_game()
    
    elif cmd in ['score', 'punkte']:
        add_to_history(f"Punkte: {game_score}")
        add_to_history(f"Züge: {game_moves}")
        add_to_history("")
    
    elif cmd in ['zeit']:
        add_to_history(f"Spielzeit: {format_elapsed_time()}")
        ticks_total = pygame.time.get_ticks() - game_start_ticks
        add_to_history(f"Pygame Ticks: {ticks_total}")
        add_to_history("")
    
    elif cmd in ['diagnose', 'd']:
        add_to_history("═══ DIAGNOSE ═══")
        add_to_history(get_health_description())
        add_to_history(get_strength_description())
        hunger_desc = get_hunger_description()
        if hunger_desc:
            add_to_history(hunger_desc)
        if player_stats['equipped_weapon']:
            w = weapons[player_stats['equipped_weapon']]
            add_to_history(f"Waffe: {w['name']}")
        else:
            add_to_history("Waffe: Keine")
        add_to_history(f"Kampfstatus: {'IM KAMPF' if player_stats['in_combat'] else 'Sicher'}")
        enc = get_encumbrance_description()
        if enc:
            add_to_history(enc)
        # Light status
        for litem in player_inventory:
            lidef = ITEM_DEFS.get(litem)
            if lidef and lidef.max_charge >= 0:
                if lidef.charge <= 0:
                    add_to_history(f"{lidef.name}: Erloschen")
                elif lidef.charge <= 20:
                    add_to_history(f"{lidef.name}: Schwaches Licht")
                else:
                    add_to_history(f"{lidef.name}: Leuchtet")
        add_to_history("")
    
    else:
        # === REACTIVE PARSER ===
        verb = words[0] if words else ''
        obj = ' '.join(words[1:]) if len(words) > 1 else ''
        room = rooms[current_room]
        all_known_items = set(ITEM_DEFS.keys())
        room_items = set(room.get('items', []))
        inv_items = set(player_inventory)
        
        # 1) Verb braucht Objekt aber keins angegeben -> fragen
        if verb in VERBS_NEED_OBJECT and not obj:
            infinitiv = VERBS_NEED_OBJECT[verb]
            add_to_history(f"Was willst du {infinitiv}?")
            pending_ambiguity = {'action': verb, 'candidates': list(room_items | inv_items), 'original_cmd': verb}
            add_to_history("")
            return
        
        # 2) Logisch unmögliche Aktionen
        if verb in ('esse', 'iss') and obj:
            if obj in weapons:
                add_to_history(random.choice(ILLOGICAL_RESPONSES['eat_weapon']))
                add_to_history("")
                return
            if obj in all_known_items and obj not in food_items:
                add_to_history(random.choice(ILLOGICAL_RESPONSES['eat_inedible']))
                add_to_history("")
                return
        if verb in ('ausrüsten',) and obj:
            if obj in food_items:
                add_to_history(random.choice(ILLOGICAL_RESPONSES['equip_food']))
                add_to_history("")
                return
            if obj in all_known_items and obj not in weapons:
                add_to_history(random.choice(ILLOGICAL_RESPONSES['equip_non_weapon']))
                add_to_history("")
                return
        
        # 3) Objekt existiert im Spiel aber nicht hier
        if obj and obj in all_known_items:
            if obj not in room_items and obj not in inv_items:
                add_to_history(f"Du siehst hier kein '{get_item_name(obj)}'.")
                add_to_history("")
                return
        
        # 4) Partielle Objekterkennung / Disambiguation
        if obj:
            available = list(room_items | inv_items)
            matches = [it for it in available if obj in it or it.startswith(obj)]
            if len(matches) == 1 and verb in VERBS_NEED_OBJECT:
                process_command(f"{verb} {matches[0]}")
                return
            elif len(matches) > 1:
                add_to_history(f"Was meinst du?")
                for idx, m in enumerate(matches, 1):
                    add_to_history(f"  {idx}. {get_item_name(m)}")
                pending_ambiguity = {'action': verb, 'candidates': matches, 'original_cmd': cmd}
                add_to_history("")
                return
        
        # 5) Unbekanntes Verb
        if verb and verb[:9] not in KNOWN_VERBS:
            resp = random.choice(UNKNOWN_VERB_RESPONSES).format(verb=verb)
            add_to_history(resp)
            add_to_history("")
        else:
            add_to_history("Unbekannter Befehl. Tippe 'hilfe' für Befehle.")
            add_to_history("")

def equip_weapon(weapon_key):
    """Rüste eine Waffe aus"""
    if weapon_key not in weapons:
        add_to_history(f"'{weapon_key}' ist keine gültige Waffe.")
        add_to_history("")
        return
    
    if weapon_key not in player_inventory:
        add_to_history(f"Du hast '{weapon_key}' nicht im Inventar.")
        add_to_history("")
        return
    
    weapon = weapons[weapon_key]
    player_stats['equipped_weapon'] = weapon_key
    player_stats['weapon_type'] = weapon['type']
    
    add_to_history(f"Du rüstest {weapon['name']} aus.")
    
    if weapon['type'] == 'ranged':
        add_to_history(f"Munition: {weapon.get('ammo', 0)}")
        add_to_history("Bereit zum Feuern. Nutze: schieße auf [ziel]")
    else:
        add_to_history("Bereit für Nahkampf. Nutze: stich auf [ziel]")
    
    add_to_history("")

def ranged_attack(target):
    """Fernkampf mit Schusswaffen"""
    if not player_stats['equipped_weapon']:
        add_to_history("Du hast keine Waffe ausgerüstet!")
        add_to_history("")
        return
    
    weapon_key = player_stats['equipped_weapon']
    weapon = weapons[weapon_key]
    
    if weapon['type'] != 'ranged':
        add_to_history(f"{weapon['name']} ist keine Fernkampfwaffe!")
        add_to_history("")
        return
    
    if weapon.get('ammo', 0) <= 0:
        add_to_history("Keine Munition mehr!")
        add_to_history("")
        return
    
    # Finde Gegner im Raum
    room = rooms[current_room]
    enemy_in_room = room.get('enemy', None)
    
    if not enemy_in_room:
        add_to_history("Hier gibt es kein Ziel zum Angreifen!")
        add_to_history("")
        return
    
    enemy = enemies.get(enemy_in_room, None)
    if not enemy or enemy['health'] <= 0:
        add_to_history("Fehler: Gegner nicht gefunden.")
        add_to_history("")
        return
    
    # Ziel-Validierung: target muss zum Gegner passen
    t = target.lower().strip()
    enemy_words = [enemy_in_room] + enemy['name'].lower().replace('-', ' ').split()
    if t != enemy_in_room and t not in enemy_words:
        add_to_history(f"Hier ist kein '{target}'. Hier ist: {enemy['name']}")
        add_to_history("")
        return
    
    # Schussberechnung
    add_to_history(f"Du legst die {weapon['name']} an...")
    
    # Trefferchance basierend auf Entfernung
    hit_chance = weapon['accuracy']
    if enemy.get('distance') == 'weit':
        hit_chance *= 0.6
    elif enemy.get('distance') == 'mittel':
        hit_chance *= 0.8
    
    # Schuss
    weapon['ammo'] -= 1
    
    if random.random() < hit_chance:
        # Berechne Schaden (Min-Max Range)
        min_dmg, max_dmg = weapon['damage']
        damage = random.randint(min_dmg, max_dmg)
        
        enemy['health'] -= damage
        add_to_history(get_enemy_damage_reaction(damage, enemy['health'], enemy['max_health']))
        add_to_history(f"Zustand: {get_enemy_health_description(enemy['health'], enemy['max_health'])}")
        
        if enemy['health'] <= 0:
            stop_zombie_sounds()
            add_to_history(f"Der {enemy['name']} bricht zusammen!")
            room['enemy'] = None
            player_stats['in_combat'] = False
            zombie_kill_times[current_room] = time.time()  # Respawn-Cooldown starten
            add_score('zombie_kill')
        else:
            # Gegner-Gegenangriff
            enemy_counterattack(enemy)
    else:
        add_to_history("VERFEHLT! Der Schuss geht daneben.")
        # Gegner-Gegenangriff
        enemy_counterattack(enemy)
    
    add_to_history("")

def enemy_counterattack(enemy):
    """Gegner greift zurück an"""
    min_dmg, max_dmg = enemy['damage']
    damage = random.randint(min_dmg, max_dmg)
    
    player_stats['health'] -= damage
    add_to_history(f"{enemy['name']} greift an!")
    add_to_history(get_damage_reaction(damage, player_stats['health']))
    
    if player_stats['health'] <= 0:
        add_to_history("")
        add_to_history("=== DU BIST GESTORBEN ===")
        # Reset Player Stats
        player_stats['health'] = 100
        player_stats['strength'] = 100
        player_stats['hunger'] = 0
        player_stats['turns_since_last_meal'] = 0
        player_stats['last_recovery_turn'] = 0
        player_stats['equipped_weapon'] = None
        player_stats['weapon_type'] = None
        player_stats['in_combat'] = False
        player_stats['fist_level'] = 1
        
        # Reset Enemies
        for enemy_key in enemies:
            enemies[enemy_key]['health'] = enemies[enemy_key]['max_health']
        
        # Reset Rooms
        rooms['start']['first_visit'] = True
        rooms['start']['enemy'] = 'zombie'
        rooms['start']['items'] = ['feuerlöscher', 'zeitung']
        if 'norden' in rooms['start']['exits']:
            del rooms['start']['exits']['norden']
        
        start_game()

def melee_attack(target):
    """Nahkampf mit Stichwaffen"""
    if not player_stats['equipped_weapon']:
        add_to_history("Du hast keine Waffe ausgerüstet!")
        add_to_history("")
        return
    
    weapon_key = player_stats['equipped_weapon']
    weapon = weapons[weapon_key]
    
    if weapon['type'] != 'melee':
        add_to_history(f"{weapon['name']} ist keine Nahkampfwaffe!")
        add_to_history("")
        return
    
    # Finde Gegner im Raum
    room = rooms[current_room]
    enemy_in_room = room.get('enemy', None)
    
    if not enemy_in_room:
        add_to_history("Hier gibt es kein Ziel zum Angreifen!")
        add_to_history("")
        return
    
    enemy = enemies.get(enemy_in_room, None)
    if not enemy:
        add_to_history("Fehler: Gegner nicht gefunden.")
        add_to_history("")
        return
    
    add_to_history(f"Du ziehst das {weapon['name']}...")
    
    # QTE für Nahkampf starten
    start_qte_sequence('melee_strike', {'weapon': weapon, 'enemy': enemy})

def start_qte_sequence(qte_type, data=None):
    """Startet eine Quick-Time-Event Sequenz"""
    global qte_active, qte_sequence, qte_input, qte_start_time, qte_callback
    
    qte_active = True
    qte_input = ""
    qte_start_time = time.time()
    
    # Generiere zufällige Tastensequenz
    keys = ['W', 'A', 'S', 'D', 'E']
    qte_sequence = [random.choice(keys) for _ in range(3)]
    
    if qte_type == 'melee_strike':
        add_to_history(">>> QTE AKTIV <<<")
        add_to_history(f"EINGABE: {' - '.join(qte_sequence)}")
        add_to_history("Du hast 2 Sekunden!")
        add_to_history("")
        qte_callback = lambda success: handle_melee_qte(success, data)
    
    elif qte_type == 'combat_dodge':
        add_to_history(">>> QTE AUSWEICHEN <<<")
        add_to_history(f"EINGABE: {' - '.join(qte_sequence)}")
        add_to_history("Schnell ausweichen!")
        add_to_history("")
        qte_callback = lambda success: handle_dodge_qte(success)
    
    elif qte_type == 'fishing':
        add_to_history(">>> FISCH BEISST AN <<<")
        add_to_history(f"EINGABE: {' - '.join(qte_sequence)}")
        add_to_history("Schnell einholen!")
        add_to_history("")
        qte_callback = lambda success: handle_fishing_qte(success)

def check_qte_result():
    """Prüft QTE Ergebnis"""
    global qte_active, qte_input, qte_callback
    
    if not qte_active:
        return
    
    # Zeitlimit prüfen
    elapsed = time.time() - qte_start_time
    
    # Prüfe ob Sequenz komplett
    if qte_input == ''.join(qte_sequence):
        qte_active = False
        add_to_history(">>> PERFEKT! <<<")
        add_to_history("")
        if qte_callback:
            qte_callback(True)
        qte_callback = None
        qte_input = ""
    
    elif elapsed > qte_duration:
        qte_active = False
        add_to_history(">>> ZU LANGSAM! <<<")
        add_to_history("")
        if qte_callback:
            qte_callback(False)
        qte_callback = None
        qte_input = ""
        
    elif len(qte_input) > 0 and not ''.join(qte_sequence).startswith(qte_input):
        qte_active = False
        add_to_history(">>> FALSCHE TASTE! <<<")
        add_to_history("")
        if qte_callback:
            qte_callback(False)
        qte_callback = None
        qte_input = ""

def read_item(item):
    """Lese ein Item (Zeitung, Notizen, etc.)"""
    if item not in player_inventory: 
        add_to_history(f"Du hast '{item}' nicht im Inventar.")
        add_to_history("")
        return
    
    readable_items = {
        'zeitung': """DEAD WORLD ZEITUNG
Letzte Ausgabe - Tag 0
QUARANTÄNE VERHÄNGT - INFEKTIONSWELLE BREITET SICH AUS
Gestern Nacht bestätigten Behörden den Ausbruch eines unbekannten Parasiten. Betroffene zeigen aggressives Verhalten und physische Mutationen.
Überlebende werden aufgefordert, Bunker aufzusuchen.
---
Für neue Überlebende: Du bist neu in dieser Welt? Tippe 'help' oder 'hilfe' um die wichtigsten Befehle zu sehen.
Überlebe. Kämpfe. Erforsche.
""",
        'notizen': "Labornotizen: 'Test-Subjekt 7 zeigt Resistenz... Parasiten-DNA mutiert...'",
        'notiz': "Eine hastige Notiz: 'Sie kommen durch die Lüftung. Gott hilf uns.'"
    }
    
    if item in readable_items:
        add_to_history(readable_items[item])
        add_to_history("")
    else:
        add_to_history(f"'{item}' kann nicht gelesen werden.")
        add_to_history("")

def attack_with_weapon(target, weapon_name):
    """Greife ein Ziel mit einer bestimmten Waffe an"""
    room = rooms[current_room]
    enemy_in_room = room.get('enemy', None)
    
    # Normalisiere Waffen-Name
    weapon_key = weapon_name.lower().strip()
    
    # Prüfe ob Gegner im Raum ist
    if not enemy_in_room:
        add_to_history("Es gibt hier nichts zum Angreifen!")
        add_to_history("")
        return
    
    # Finde den Gegner
    enemy = enemies.get(enemy_in_room)
    if not enemy or enemy['health'] <= 0:
        add_to_history("Der Gegner wurde bereits besiegt.")
        add_to_history("")
        return
    
    # Ziel-Validierung: target muss zum Gegner passen
    t = target.lower().strip()
    enemy_words = [enemy_in_room] + enemy['name'].lower().replace('-', ' ').split()
    if t != enemy_in_room and t not in enemy_words:
        add_to_history(f"Hier ist kein '{target}'. Hier ist: {enemy['name']}")
        add_to_history("")
        return
    
    # Prüfe ob die Waffe existiert
    if weapon_key not in weapons:
        add_to_history(f"'{weapon_name}' ist keine bekannte Waffe.")
        add_to_history("")
        return
    
    # Prüfe ob Spieler die Waffe hat (Inventar oder im Raum)
    has_weapon = weapon_key in player_inventory
    weapon_in_room = weapon_key in room.get('items', [])
    
    if not has_weapon and not weapon_in_room:
        add_to_history(f"Du hast keinen {weapons[weapon_key]['name']} und siehst auch keinen hier.")
        add_to_history("")
        return
    
    # Wenn Waffe im Raum liegt, nimm sie automatisch auf
    if weapon_in_room and not has_weapon:
        room['items'].remove(weapon_key)
        player_inventory.append(weapon_key)
        add_to_history(f"Du schnappst dir den {weapons[weapon_key]['name']} vom Boden!")
        add_to_history("")
    
    # Waffe ist jetzt im Inventar - führe Angriff aus
    weapon = weapons[weapon_key]
    add_to_history(f"Du schwingst den {weapon['name']}!")
    add_to_history("")
    
    # Starte QTE für Nahkampf
    start_qte_sequence('melee_strike', {
        'weapon': weapon,
        'enemy': enemy,
        'target': enemy_in_room
    })

def unarmed_attack(target):
    """Unbewaffneter Angriff oder mit improvisierten Waffen"""
    room = rooms[current_room]
    enemy_in_room = room.get('enemy', None)
    
    if not enemy_in_room:
        add_to_history("Es gibt hier nichts zum Angreifen!")
        add_to_history("")
        return
    
    # Ziel-Validierung: target muss zum Gegner passen
    enemy = enemies.get(enemy_in_room)
    if enemy:
        t = target.lower().strip()
        enemy_words = [enemy_in_room] + enemy['name'].lower().replace('-', ' ').split()
        if t != enemy_in_room and t not in enemy_words:
            add_to_history(f"Hier ist kein '{target}'. Hier ist: {enemy['name']}")
            add_to_history("")
            return
    
    # Spezialfall: Zombie mit Feuerlöscher (im Inventar oder Raum)
    if current_room == 'start' and enemy_in_room == 'zombie':
        if 'feuerlöscher' in player_inventory:
            add_to_history("Du schwingst den Feuerlöscher!")
            add_to_history("")
            start_qte_sequence('melee_strike', {
                'weapon': weapons['feuerlöscher'], 
                'enemy': enemies['zombie'],
                'target': 'zombie'
            })
        elif 'fäuste' in player_inventory:
            add_to_history("Du schlägst mit bloßen Fäusten!")
            add_to_history("")
            start_qte_sequence('melee_strike', {
                'weapon': weapons['fäuste'], 
                'enemy': enemies['zombie'],
                'target': 'zombie'
            })
        elif 'feuerlöscher' in room.get('items', []):
            # Feuerlöscher ist im Raum - nimm und benutze ihn
            room['items'].remove('feuerlöscher')
            player_inventory.append('feuerlöscher')
            add_to_history("Du reißt den Feuerlöscher von der Wand!")
            add_to_history("")
            start_qte_sequence('melee_strike', {
                'weapon': weapons['feuerlöscher'], 
                'enemy': enemies['zombie'],
                'target': 'zombie'
            })
        else:
            add_to_history("Du schlägst mit bloßen Fäusten!")
            add_to_history("Der Zombie weicht kaum zurück.")
            add_to_history("Du brauchst eine Waffe!")
            add_to_history("")
    else:
        # Generischer Nahkampf in allen anderen Räumen
        enemy = enemies.get(enemy_in_room)
        if not enemy or enemy['health'] <= 0:
            add_to_history("Der Gegner wurde bereits besiegt.")
            add_to_history("")
            return
        
        add_to_history("Du schlägst mit bloßen Fäusten!")
        add_to_history("")
        start_qte_sequence('melee_strike', {
            'weapon': weapons['fäuste'],
            'enemy': enemy,
            'target': enemy_in_room
        })

def level_up_fists():
    """Level-Up der Fäuste bei Black Flash"""
    if player_stats['fist_level'] >= 5:
        add_to_history("Fäuste bereits auf MAX LEVEL!")
        return
    
    player_stats['fist_level'] += 1
    new_level = player_stats['fist_level']
    
    level_names = {2: 'Straßenkämpfer', 3: 'Erfahren', 4: 'Fortgeschritten', 5: 'Meisterhaft'}
    level_name = level_names.get(new_level, f'Level {new_level}')
    
    add_to_history("")
    add_to_history("=================================")
    add_to_history(f">>> FÄUSTE LEVEL UP! <<<")
    add_to_history(f"Kampfstil: {level_name}")
    add_to_history("Du spürst wie deine Schläge mächtiger werden.")
    add_to_history("=================================")


def handle_melee_qte(success, data):
    """Verarbeitet Nahkampf QTE Ergebnis"""
    weapon = data['weapon']
    enemy = data['enemy']
    target = data.get('target', 'enemy')
    is_fists = (weapon.get('name') == 'Fäuste')
    
    room = rooms[current_room]
    got_black_flash = False  # Tracker für Level-Up
    
    if success:
        # Für Fäuste: Nutze Level-basierte Stats (KEINE Crit-Chance!)
        if is_fists:
            fist_level = player_stats['fist_level']
            fist_bonus = FIST_LEVEL_BONUSES[fist_level]
            min_dmg, max_dmg = fist_bonus['damage']
            black_flash = weapon.get('black_flash', 0.01)
        else:
            min_dmg, max_dmg = weapon['damage']
            black_flash = weapon.get('black_flash', 0.01)
        
        damage = random.randint(min_dmg, max_dmg)
        
        # Kritischer Treffer (nicht für Fäuste)
        crit = weapon.get('crit_chance', 0)
        if crit > 0 and random.random() < crit:
            damage = int(damage * 1.5)
            add_to_history(">>> KRITISCHER TREFFER! <<<")
        
        # Black Flash
        if random.random() < black_flash:
            damage = int(damage * 2.5)
            add_to_history(">>> BLACK FLASH! <<<")
            got_black_flash = True
            
        enemy['health'] -= damage
        add_to_history(get_enemy_damage_reaction(damage, enemy['health'], enemy['max_health']))
        add_to_history(f"Zustand: {get_enemy_health_description(enemy['health'], enemy['max_health'])}")
        
        # Level-Up bei Black Flash (statt XP-System)
        if is_fists and got_black_flash:
            level_up_fists()
        
        if enemy['health'] <= 0:
            stop_zombie_sounds()
            add_to_history("")
            add_to_history("Der Zombie zuckt ein letztes Mal.")
            add_to_history("Schwarze Flüssigkeit sickert aus dem zerschmetterten Schädel.")
            add_to_history("")
            add_to_history("=== SIEG ===")
            add_to_history("")
            
            # Gegner besiegt - entferne aus Raum
            room['enemy'] = None
            player_stats['in_combat'] = False
            zombie_kill_times[current_room] = time.time()  # Respawn-Cooldown starten
            add_score('zombie_kill')
            
            # Raumspezifische Belohnungen
            if current_room == 'start':
                unlock_transition('start_corridor')
                room['items'].append('taschenlampe')
                add_to_history("Der Bunker ist still. Du bist vorerst sicher.")
                add_to_history("Im NORDEN siehst du nun einen Korridor.")
            else:
                add_to_history("Der Raum ist jetzt sicher.")
        else:
            # Gegner schlägt zurück
            min_dmg, max_dmg = enemy['damage']
            damage = random.randint(min_dmg, max_dmg)
            player_stats['health'] -= damage
            add_to_history(f"{enemy['name']} krallt sich in deine Schulter!")
            add_to_history(get_damage_reaction(damage, player_stats['health']))
            
            if player_stats['health'] <= 0:
                add_to_history("")
                add_to_history("=== DU BIST GESTORBEN ===")
                # Reset Player Stats
                player_stats['health'] = 100
                player_stats['strength'] = 100
                player_stats['hunger'] = 0
                player_stats['turns_since_last_meal'] = 0
                player_stats['last_recovery_turn'] = 0
                player_stats['equipped_weapon'] = None
                player_stats['weapon_type'] = None
                player_stats['in_combat'] = False
                player_stats['fist_level'] = 1
                
                # Reset Enemies
                for enemy_key in enemies:
                    enemies[enemy_key]['health'] = enemies[enemy_key]['max_health']
                
                # Reset Rooms
                rooms['start']['first_visit'] = True
                rooms['start']['enemy'] = 'zombie'
                rooms['start']['items'] = ['feuerlöscher', 'zeitung']
                reset_transitions()
                
                start_game()
    else:
        add_to_history("Du verfehlst!")
        min_dmg, max_dmg = enemy['damage']
        damage = random.randint(min_dmg, max_dmg)
        player_stats['health'] -= damage
        add_to_history(f"Der Zombie beißt zu!")
        add_to_history(get_damage_reaction(damage, player_stats['health']))
        
        if player_stats['health'] <= 0:
            add_to_history("")
            add_to_history("=== DU BIST GESTORBEN ===")
            # Reset Player Stats
            player_stats['health'] = 100
            player_stats['strength'] = 100
            player_stats['hunger'] = 0
            player_stats['turns_since_last_meal'] = 0
            player_stats['last_recovery_turn'] = 0
            player_stats['equipped_weapon'] = None
            player_stats['weapon_type'] = None
            player_stats['in_combat'] = False
            player_stats['fist_level'] = 1
            
            # Reset Enemies
            for enemy_key in enemies:
                enemies[enemy_key]['health'] = enemies[enemy_key]['max_health']
            
            # Reset Rooms
            rooms['start']['first_visit'] = True
            rooms['start']['enemy'] = 'zombie'
            rooms['start']['items'] = ['feuerlöscher', 'zeitung']
            reset_transitions()
            
            start_game()
    
    add_to_history("")

def handle_dodge_qte(success):
    """Verarbeitet Ausweich QTE Ergebnis"""
    room = rooms[current_room]
    enemy_key = room.get('enemy', None)
    
    if not enemy_key:
        return
    
    enemy = enemies.get(enemy_key)
    
    if success:
        add_to_history("Du weichst dem Angriff aus!")
    else:
        min_dmg, max_dmg = enemy['damage']
        damage = random.randint(min_dmg, max_dmg)
        player_stats['health'] -= damage
        add_to_history(f"Getroffen!")
        add_to_history(get_damage_reaction(damage, player_stats['health']))
        
        if player_stats['health'] <= 0:
            add_to_history("")
            add_to_history("=== DU BIST GESTORBEN ===")
            # Reset Player Stats
            player_stats['health'] = 100
            player_stats['strength'] = 100
            player_stats['hunger'] = 0
            player_stats['turns_since_last_meal'] = 0
            player_stats['last_recovery_turn'] = 0
            player_stats['equipped_weapon'] = None
            player_stats['weapon_type'] = None
            player_stats['in_combat'] = False
            player_stats['fist_level'] = 1
            
            # Reset Enemies
            for enemy_key in enemies:
                enemies[enemy_key]['health'] = enemies[enemy_key]['max_health']
            
            # Reset Rooms
            rooms['start']['first_visit'] = True
            rooms['start']['enemy'] = 'zombie'
            rooms['start']['items'] = ['feuerlöscher', 'zeitung']
            if 'norden' in rooms['start']['exits']:
                del rooms['start']['exits']['norden']
            
            start_game()
    
    add_to_history("")

def handle_fishing_qte(success):
    """Verarbeitet Angel QTE Ergebnis"""
    if success:
        add_to_history("Du ziehst einen Fisch an Land!")
        player_inventory.append('fisch')
    else:
        add_to_history("Der Fisch ist entkommen...")
    
    add_to_history("")

def draw_game(current_time):
    """Zeichnet das Text-Adventure Terminal mit CRT-Effekt"""
    global max_scroll
    
    screen.fill(TERMINAL_BG)
    
    # Skalierte Werte für konsistentes Layout
    padding = scale(10)
    text_padding = scale(20)
    header_y = scale(10)
    separator_y = scale(40)
    line_height = scale(25)
    input_area_height = scale(60)
    
    # Skalierte Fonts
    font_header = get_scaled_font(25)
    font_text = get_scaled_font(30)
    font_hint = get_scaled_font(25)
    
    # Terminal-Header
    if qte_active:
        header_text = "=== QTE AKTIV === [Drücke die richtigen Tasten!]"
        header_color = (255, 40, 40)
    elif prolog_shown:
        if scroll_offset > 0:
            header_text = f"=== DEAD WORLD === [Gescrollt: {scroll_offset} Zeilen] [Ende: Zurück] [Mausrad/↑↓/PgUp/PgDn]"
        else:
            header_text = "=== DEAD WORLD TERMINAL === [F11: Fullscreen] [ESC: Menü] [↑↓: History]"
        header_color = TERMINAL_GREEN
    else:
        header_text = "=== DEAD WORLD - PROLOG === [ENTER: Weiter]"
        header_color = TERMINAL_GREEN
    
    header_surf = font_header.render(header_text, True, header_color)
    screen.blit(header_surf, (padding, header_y))
    
    # Gradient-Separator (simple Linie statt per-pixel loop)
    w = screen.get_width()
    pygame.draw.line(screen, TERMINAL_GREEN, (padding, separator_y), (w - padding, separator_y), 1)
    
    # QTE Timer anzeigen
    qte_offset = 0
    if qte_active:
        elapsed = time.time() - qte_start_time
        remaining = max(0, qte_duration - elapsed)
        timer_text = f"ZEIT: {remaining:.1f}s | EINGABE: {qte_input}"
        timer_surf = font_text.render(timer_text, True, (255, 0, 0))
        screen.blit(timer_surf, (text_padding, scale(45)))
        qte_offset = scale(30)
    
    # Game History (scrollendes Text-Fenster mit vollständigem Verlauf)
    y_start = separator_y + scale(10) + qte_offset
    y_offset = y_start
    
    # Berechne verfügbare Höhe für Text
    available_height = screen.get_height() - y_start - input_area_height
    visible_lines = max(1, available_height // line_height)
    
    # Berechne max scroll basierend auf Gesamtzahl der Zeilen
    total_lines = len(game_history)
    max_scroll = max(0, total_lines - visible_lines)
    
    # Bestimme welche Zeilen angezeigt werden (mit Scroll)
    if prolog_shown and not qte_active:
        # Invertiert: scroll_offset = 0 zeigt neueste, höherer offset = ältere Nachrichten
        end_idx = total_lines - scroll_offset
        start_idx = max(0, end_idx - visible_lines)
    else:
        # Standard: Zeige die letzten Zeilen
        start_idx = max(0, total_lines - visible_lines)
        end_idx = total_lines
    
    # Zeichne sichtbare Zeilen (Word-Wrapping passiert bereits in add_to_history)
    for i in range(start_idx, end_idx):
        if i < len(game_history):
            line = game_history[i]
            # Leerzeilen nicht rendern, aber Abstand beibehalten
            # font.render("") kann Artefakte/Vierecke erzeugen
            if line.strip():
                text_surf = font_text.render(line, True, TERMINAL_GREEN)
                screen.blit(text_surf, (text_padding, y_offset))
            # y_offset wird IMMER erhöht - auch für Leerzeilen (vertikaler Abstand)
            y_offset += line_height
    
    # Typewriter: Zeige die aktuell getippte Zeile (teilweise sichtbar)
    if typewriter_active and typewriter_current_line and typewriter_current_line.strip():
        visible_text = typewriter_current_line[:typewriter_reveal_index]
        if visible_text.strip():
            tw_surf = font_text.render(visible_text, True, TERMINAL_GREEN)
            screen.blit(tw_surf, (text_padding, y_offset))
        y_offset += line_height
    
    # Scroll-Indikator (wenn gescrollt)
    if prolog_shown and not qte_active and scroll_offset > 0:
        indicator_x = screen.get_width() - scale(30)
        indicator_y = y_start + scale(20)
        
        # Scroll-Bar
        bar_height = available_height - scale(40)
        bar_y = indicator_y
        
        # Berechne Position des Scroll-Thumb (invertiert)
        if max_scroll > 0:
            thumb_height = max(scale(20), bar_height * visible_lines // total_lines)
            thumb_y = bar_y + (bar_height - thumb_height) * (1 - scroll_offset / max_scroll)
        else:
            thumb_height = bar_height
            thumb_y = bar_y
        
        # Zeichne Bar (Hintergrund)
        pygame.draw.rect(screen, DARK_GRAY, (indicator_x, bar_y, scale(10), bar_height))
        # Zeichne Thumb (aktueller Scroll)
        pygame.draw.rect(screen, TERMINAL_GREEN, (indicator_x, int(thumb_y), scale(10), int(thumb_height)))
    
    # Input-Bereich (nur im Spiel-Modus, nicht im Prolog oder QTE)
    if prolog_shown and not qte_active:
        input_y = screen.get_height() - input_area_height
        # Input separator (simple Linie statt per-pixel loop)
        w = screen.get_width()
        pygame.draw.line(screen, TERMINAL_DIM, (padding, input_y - scale(10)), (w - padding, input_y - scale(10)), 1)
        
        # Text vor und nach dem Cursor
        text_before_cursor = input_text[:cursor_position]
        text_after_cursor = input_text[cursor_position:]
        
        # Blinkender Cursor
        if (current_time // 500) % 2 == 0:
            cursor_char = "|"
        else:
            cursor_char = " "
        
        prompt = f"> {text_before_cursor}{cursor_char}{text_after_cursor}"
        
        # Subtiler Glow auf der Prompt-Zeile
        glow_surf = font_text.render(prompt, True, (*TERMINAL_DIM, 60))
        screen.blit(glow_surf, (text_padding - 1, input_y - 1))
        
        input_surf = font_text.render(prompt, True, TERMINAL_GREEN)
        screen.blit(input_surf, (text_padding, input_y))
        
        # History-Hinweis anzeigen wenn History vorhanden
        if command_history and history_index != -1:
            hint_text = f"[History: {history_index + 1}/{len(command_history)}]"
            hint_surf = font_hint.render(hint_text, True, GRAY)
            screen.blit(hint_surf, (screen.get_width() - scale(200), input_y + scale(35)))
    
    elif not prolog_shown and not qte_active:
        # Prolog-Hinweis mit Puls
        hint_y = screen.get_height() - scale(40)
        pulse = int(180 + 60 * math.sin(current_time * 0.003))
        hint_surf = font_text.render("[Drücke ENTER um fortzufahren]", True, (pulse // 6, pulse // 3, pulse))
        hint_rect = hint_surf.get_rect(center=(screen.get_width() // 2, hint_y))
        screen.blit(hint_surf, hint_rect)
    
    # CRT-Scanline Overlay (gecacht für Performance)
    global _scanline_cache, _scanline_cache_size
    sw, sh = screen.get_width(), screen.get_height()
    if _scanline_cache is None or _scanline_cache_size != (sw, sh):
        _scanline_cache = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(0, sh, 3):
            pygame.draw.line(_scanline_cache, (0, 0, 0, 18), (0, y), (sw, y), 1)
        _scanline_cache_size = (sw, sh)
    screen.blit(_scanline_cache, (0, 0))


def draw_options(current_time):
    """Zeichnet das atmosphärische Options-Menü"""
    screen.fill(BLACK)
    draw_cracks(screen, 35)
    draw_fog(screen, current_time, 150)
    draw_particles(screen, current_time, 60)
    draw_vignette(screen, 140)
    
    # Skalierte Fonts
    font_title = get_scaled_font(80)
    font_option = get_scaled_font(50)
    font_small_hint = get_scaled_font(25)
    
    # Titel
    title_surf = font_title.render("OPTIONEN", True, BLOOD_RED)
    title_rect = title_surf.get_rect(center=(screen.get_width() // 2, scale_y(80)))
    screen.blit(title_surf, title_rect)
    
    # Optionen anzeigen
    center_x = screen.get_width() // 2
    y = scale_y(180)
    spacing = scale(50)
    arrow_offset = scale(220)
    
    # Helper: Zeichne eine Option mit < > Pfeilen und Highlight
    def draw_option_row(label, value, row_y, row_index, left_active=True, right_active=True):
        is_selected = (row_index == options_selected_index)
        text_color = TERMINAL_GREEN if is_selected else LIGHT_GRAY
        arrow_color = TERMINAL_GREEN if is_selected else GRAY
        
        # Label
        label_surf = font_option.render(label, True, text_color)
        label_rect = label_surf.get_rect(center=(center_x, row_y))
        screen.blit(label_surf, label_rect)
        
        row_y += spacing
        
        # Linker Pfeil
        left_color = arrow_color if left_active else GRAY
        left_arrow = font_option.render("<", True, left_color)
        left_rect = left_arrow.get_rect(center=(center_x - arrow_offset, row_y))
        screen.blit(left_arrow, left_rect)
        
        # Wert
        value_surf = font_option.render(value, True, text_color)
        value_rect = value_surf.get_rect(center=(center_x, row_y))
        screen.blit(value_surf, value_rect)
        
        # Rechter Pfeil
        right_color = arrow_color if right_active else GRAY
        right_arrow = font_option.render(">", True, right_color)
        right_rect = right_arrow.get_rect(center=(center_x + arrow_offset, row_y))
        screen.blit(right_arrow, right_rect)
        
        # Selektions-Indikator (pulsierender Balken)
        if is_selected:
            pulse = int(40 + 20 * math.sin(current_time * 0.004))
            indicator_surf = pygame.Surface((scale(500), spacing * 2 + scale(10)), pygame.SRCALPHA)
            indicator_surf.fill((0, 255, 0, pulse))
            indicator_rect = indicator_surf.get_rect(center=(center_x, row_y - spacing // 2 + scale(5)))
            screen.blit(indicator_surf, indicator_rect)
        
        return row_y + spacing
    
    # === AUFLÖSUNG (Index 0) ===
    res_name = get_current_resolution_name()
    can_left_res = not fullscreen and current_resolution_index > 0
    can_right_res = not fullscreen and current_resolution_index < len(RESOLUTION_PRESETS) - 1
    y = draw_option_row("Auflösung:", res_name, y, 0, can_left_res, can_right_res)
    
    # Fullscreen-Warnung
    if fullscreen and options_selected_index == 0:
        warn_text = font_small_hint.render("(Deaktiviere Fullscreen mit F11 um Auflösung zu ändern)", True, HOVER_RED)
        warn_rect = warn_text.get_rect(center=(center_x, y - scale(30)))
        screen.blit(warn_text, warn_rect)
    
    y += scale(20)
    
    # === MUSIK (Index 1) ===
    music_pct = int(game_settings['music_volume'] * 100)
    music_val = f"{music_pct}%"
    can_left_music = music_pct > 0
    can_right_music = music_pct < 100
    y = draw_option_row("Musik:", music_val, y, 1, can_left_music, can_right_music)
    
    y += scale(20)
    
    # === SFX (Index 2) ===
    sfx_pct = int(game_settings['sfx_volume'] * 100)
    sfx_val = f"{sfx_pct}%"
    can_left_sfx = sfx_pct > 0
    can_right_sfx = sfx_pct < 100
    y = draw_option_row("Effekte:", sfx_val, y, 2, can_left_sfx, can_right_sfx)
    
    # Zurück-Button (Position anpassen)
    options_buttons[0].pos = (center_x, screen.get_height() - scale(100))
    
    mouse_pos = pygame.mouse.get_pos()
    for button in options_buttons:
        button.check_hover(mouse_pos)
        button.draw(screen, current_time)
    
    # Hinweise
    hints = [
        "↑ / ↓ : Option wählen  |  ← / → : Wert ändern",
        "F11: Vollbild umschalten"
    ]
    hint_y = screen.get_height() - scale(50)
    for hint in hints:
        hint_surf = font_small_hint.render(hint, True, GRAY)
        hint_rect = hint_surf.get_rect(center=(center_x, hint_y))
        screen.blit(hint_surf, hint_rect)
        hint_y += scale(20)

def draw_menu(current_time):
    """Zeichnet das atmosphärische Hauptmenü"""
    global menu_selected_index
    
    screen.fill(BLACK)
    
    # Atmosphärische Hintergrund-Schichten
    draw_fog(screen, current_time, 200)
    draw_particles(screen, current_time, 80)
    draw_vignette(screen, 160)
    
    # Skalierte Schriften
    font_menu_title = get_scaled_font(80)
    font_menu_hint = get_scaled_font(22)
    
    # Titel mit Glow - direkt auf Screen zeichnen statt extra full-screen Surface
    draw_cracked_text(screen, "DEAD WORLD", 
                     (screen.get_width() // 2, scale_y(130)), 
                     (BLOOD_RED[0], BLOOD_RED[1], BLOOD_RED[2]), 
                     current_time,
                     font_menu_title)
    
    # Dekorative Trennlinie unter dem Titel (gecacht)
    center_x = screen.get_width() // 2
    line_half = scale(120)
    line_y = scale_y(200)
    _draw_gradient_line(screen, center_x, line_y, line_half, DARK_RED)
    
    # Aktualisiere Button-Positionen basierend auf aktueller Auflösung
    menu_buttons[0].pos = (center_x, scale_y(320))
    menu_buttons[1].pos = (center_x, scale_y(420))
    menu_buttons[2].pos = (center_x, scale_y(520))
    
    mouse_pos = pygame.mouse.get_pos()
    
    # Prüfe ob Maus über einem Button ist
    mouse_over_any = False
    for i, button in enumerate(menu_buttons):
        if button.check_hover(mouse_pos):
            menu_selected_index = i
            mouse_over_any = True
    
    # Wenn keine Maus über Buttons, nutze keyboard selection
    if not mouse_over_any:
        for i, button in enumerate(menu_buttons):
            button.hovered = (i == menu_selected_index)
    
    for button in menu_buttons:
        button.draw(screen, current_time)
    
    # Hinweis für Tastatursteuerung (subtiler)
    hint_pulse = int(60 + 30 * math.sin(current_time * 0.002))
    hint_surf = font_menu_hint.render("↑↓: Navigieren  |  ENTER: Auswählen", True, (hint_pulse, hint_pulse, hint_pulse))
    hint_rect = hint_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() - scale(30)))
    screen.blit(hint_surf, hint_rect)

# Menu-Buttons (initiale Positionen, werden in draw_menu dynamisch aktualisiert)
menu_buttons = [
    MenuButton("NEUES SPIEL", (WIDTH // 2, 350), start_game),
    MenuButton("OPTIONEN", (WIDTH // 2, 450), show_options),
    MenuButton("BEENDEN", (WIDTH // 2, 550), quit_game)
]

options_buttons = [
    MenuButton("ZURÜCK", (WIDTH // 2, 550), back_to_menu)
]

def main():
    global current_state, input_text, backspace_held, last_backspace_time, history_index, scroll_offset, max_scroll, menu_selected_index, cursor_position, map_camera_x, map_camera_y, map_zoom, map_cursor_room, map_dragging, map_drag_last_pos, options_selected_index
    global delete_held, last_delete_time, left_held, last_left_time, right_held, last_right_time
    global enter_held, last_enter_time
    global node_dragging, node_drag_key, node_hovered_key
    global building_dragging, building_drag_key, building_drag_start, building_drag_offsets
    global selected_block_idx, block_resizing, block_resize_handle, block_moving, block_move_offset, block_naming, block_name_input, custom_blocks
    
    running = True
    start_time = pygame.time.get_ticks()
    
    # Musik wird erst beim Wechsel ins Menü gestartet (nicht im Intro)
    
    while running:
        current_time = pygame.time.get_ticks() - start_time
        current_ms = pygame.time.get_ticks()
        
        # Key-Repeat-Logik für Terminal-Eingabe
        if prolog_shown and not qte_active and current_state == GAME:
            # Backspace-Repeat
            if backspace_held:
                if current_ms - last_backspace_time > backspace_repeat_delay:
                    if cursor_position > 0:
                        input_text = input_text[:cursor_position-1] + input_text[cursor_position:]
                        cursor_position -= 1
                    last_backspace_time = current_ms
            
            # Delete-Repeat
            if delete_held:
                if current_ms - last_delete_time > key_repeat_delay:
                    if cursor_position < len(input_text):
                        input_text = input_text[:cursor_position] + input_text[cursor_position+1:]
                    last_delete_time = current_ms
            
            # Links-Repeat
            if left_held:
                if current_ms - last_left_time > key_repeat_delay:
                    if cursor_position > 0:
                        cursor_position -= 1
                    last_left_time = current_ms
            
            # Rechts-Repeat
            if right_held:
                if current_ms - last_right_time > key_repeat_delay:
                    if cursor_position < len(input_text):
                        cursor_position += 1
                    last_right_time = current_ms
        
        # Enter-Repeat (funktioniert sowohl im Prolog als auch im Spiel)
        if enter_held and current_state == GAME:
            if current_ms - last_enter_time > key_repeat_delay:
                if not prolog_shown:
                    process_command("")
                last_enter_time = current_ms
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Mausrad für Scrollen (GAME) / Zoom (MAP)
            if event.type == pygame.MOUSEWHEEL:
                if current_state == GAME and prolog_shown:
                    scroll_offset += event.y * 3  # Invertiert: nach oben scrollen = höherer offset
                    # Begrenze Scroll
                    scroll_offset = max(0, min(scroll_offset, max_scroll))
                elif current_state == MAP:
                    map_zoom = max(0.3, min(3.0, map_zoom + event.y * 0.12))
            
            if event.type == pygame.KEYDOWN:
                # F11 für Fullscreen
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                
                # ESC
                elif event.key == pygame.K_ESCAPE:
                    if current_state == MENU:
                        running = False
                    elif current_state == OPTIONS:
                        current_state = MENU
                        _start_menu_music()
                    elif current_state == MAP:
                        current_state = GAME
                        map_dragging = False
                    elif current_state == GAME:
                        current_state = MENU
                        _start_menu_music()
                    else:
                        current_state = MENU
                        _start_menu_music()
                        
                # Map-Steuerung (Graph View Panning)
                elif current_state == MAP:
                    if block_naming:
                        # Text input for block name
                        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE or event.key == pygame.K_F12:
                            if selected_block_idx is not None and selected_block_idx < len(custom_blocks):
                                custom_blocks[selected_block_idx]['name'] = block_name_input
                            block_naming = False
                        elif event.key == pygame.K_BACKSPACE:
                            block_name_input = block_name_input[:-1]
                        elif event.unicode.isprintable() and len(block_name_input) < 30:
                            block_name_input += event.unicode
                        continue  # Skip other MAP key handling while naming
                    
                    if event.key == pygame.K_UP:
                        map_camera_y -= 50 / map_zoom
                    elif event.key == pygame.K_DOWN:
                        map_camera_y += 50 / map_zoom
                    elif event.key == pygame.K_LEFT:
                        map_camera_x -= 50 / map_zoom
                    elif event.key == pygame.K_RIGHT:
                        map_camera_x += 50 / map_zoom
                    elif event.key in [pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS]:
                        map_zoom = min(3.0, map_zoom + 0.15)
                    elif event.key in [pygame.K_MINUS, pygame.K_KP_MINUS]:
                        map_zoom = max(0.3, map_zoom - 0.15)
                    elif event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                        current_state = GAME
                        map_dragging = False
                        node_dragging = False
                        node_drag_key = None
                        building_dragging = False
                        building_drag_key = None
                    elif event.key == pygame.K_r:
                        map_camera_x = 0
                        map_camera_y = 0
                        map_zoom = 1.0
                    elif event.key == pygame.K_s:
                        # Save custom map layout
                        save_map_layout()
                        draw_map._save_msg_time = pygame.time.get_ticks()
                    elif event.key == pygame.K_n:
                        # Create new custom block at viewport center
                        gcx = map_camera_x / 50
                        gcy = map_camera_y / 50
                        new_block = {
                            'name': f'Block {len(custom_blocks)+1}',
                            'gx': gcx - 2, 'gy': gcy - 2,
                            'gw': 4, 'gh': 4,
                            'color': [random.randint(40,120), random.randint(40,120), random.randint(40,120)]
                        }
                        custom_blocks.append(new_block)
                        selected_block_idx = len(custom_blocks) - 1
                    elif event.key == pygame.K_F12:
                        # Rename selected block
                        if selected_block_idx is not None and selected_block_idx < len(custom_blocks):
                            block_naming = True
                            block_name_input = custom_blocks[selected_block_idx]['name']
                    elif event.key == pygame.K_DELETE or event.key == pygame.K_x:
                        # Delete selected block
                        print(f"[MAP] Delete pressed! selected_block_idx={selected_block_idx}, blocks={len(custom_blocks)}")
                        if selected_block_idx is not None and selected_block_idx < len(custom_blocks):
                            custom_blocks.pop(selected_block_idx)
                            selected_block_idx = None
                            block_resizing = False
                            block_moving = False
                            print("[MAP] Block deleted!")
                        else:
                            print("[MAP] No block selected to delete")
                
                # Space im Intro
                elif event.key == pygame.K_SPACE and current_state == INTRO:
                    current_state = MENU
                    _start_menu_music()
                
                # Tastaturnavigation im Hauptmenü
                elif current_state == MENU:
                    if event.key == pygame.K_UP:
                        menu_selected_index = (menu_selected_index - 1) % len(menu_buttons)
                    elif event.key == pygame.K_DOWN:
                        menu_selected_index = (menu_selected_index + 1) % len(menu_buttons)
                    elif event.key == pygame.K_RETURN:
                        menu_buttons[menu_selected_index].action()
                
                # Pfeiltasten im Options-Menü
                elif current_state == OPTIONS:
                    if event.key == pygame.K_UP:
                        options_selected_index = (options_selected_index - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        options_selected_index = (options_selected_index + 1) % 3
                    elif event.key == pygame.K_LEFT:
                        if options_selected_index == 0:
                            change_resolution(-1)
                        elif options_selected_index == 1:
                            game_settings['music_volume'] = max(0.0, round(game_settings['music_volume'] - 0.05, 2))
                            pygame.mixer.music.set_volume(game_settings['music_volume'])
                        elif options_selected_index == 2:
                            game_settings['sfx_volume'] = max(0.0, round(game_settings['sfx_volume'] - 0.05, 2))
                    elif event.key == pygame.K_RIGHT:
                        if options_selected_index == 0:
                            change_resolution(1)
                        elif options_selected_index == 1:
                            game_settings['music_volume'] = min(1.0, round(game_settings['music_volume'] + 0.05, 2))
                            pygame.mixer.music.set_volume(game_settings['music_volume'])
                        elif options_selected_index == 2:
                            game_settings['sfx_volume'] = min(1.0, round(game_settings['sfx_volume'] + 0.05, 2))
                
                # Text-Eingabe im Spiel
                elif current_state == GAME:
                    if event.key == pygame.K_RETURN:
                        if not prolog_shown:
                            # Im Prolog: Enter zeigt mehr Text
                            process_command("")
                        elif input_text.strip().lower() in ["karte", "map"] and prolog_shown:
                            current_state = MAP
                            map_camera_x = 0
                            map_camera_y = 0
                            map_dragging = False
                            input_text = ""
                            cursor_position = 0
                        elif input_text.strip():
                            # Comma-Split: mehrere Befehle auf einer Zeile
                            raw_cmds = input_text.split(',')
                            for sub_cmd in raw_cmds:
                                sub_cmd = sub_cmd.strip()
                                if sub_cmd:
                                    add_to_history(f"> {sub_cmd}")
                                    process_command(sub_cmd)
                            input_text = ""
                            cursor_position = 0
                            history_index = -1
                        enter_held = True
                        last_enter_time = pygame.time.get_ticks() + key_initial_delay
                    
                    elif event.key == pygame.K_BACKSPACE and not qte_active:
                        if cursor_position > 0:
                            input_text = input_text[:cursor_position-1] + input_text[cursor_position:]
                            cursor_position -= 1
                        backspace_held = True
                        last_backspace_time = pygame.time.get_ticks() + backspace_initial_delay
                    
                    # Delete-Taste: Löscht Zeichen nach dem Cursor
                    elif event.key == pygame.K_DELETE and not qte_active:
                        if cursor_position < len(input_text):
                            input_text = input_text[:cursor_position] + input_text[cursor_position+1:]
                        delete_held = True
                        last_delete_time = pygame.time.get_ticks() + key_initial_delay
                    
                    # Links/Rechts-Pfeiltasten für Cursor-Navigation
                    elif event.key == pygame.K_LEFT and prolog_shown and not qte_active:
                        if cursor_position > 0:
                            cursor_position -= 1
                        left_held = True
                        last_left_time = pygame.time.get_ticks() + key_initial_delay
                    
                    elif event.key == pygame.K_RIGHT and prolog_shown and not qte_active:
                        if cursor_position < len(input_text):
                            cursor_position += 1
                        right_held = True
                        last_right_time = pygame.time.get_ticks() + key_initial_delay
                    
                    # Page Up / Page Down für Scrollen
                    elif event.key == pygame.K_PAGEUP and prolog_shown and not qte_active:
                        scroll_offset -= 10  # Invertiert
                        scroll_offset = max(0, scroll_offset)
                    
                    elif event.key == pygame.K_PAGEDOWN and prolog_shown and not qte_active:
                        scroll_offset += 10  # Invertiert
                        scroll_offset = min(scroll_offset, max_scroll)
                    
                    # Pos1 / Ende für schnelles Scrollen
                    elif event.key == pygame.K_HOME and prolog_shown and not qte_active:
                        scroll_offset = 0  # Invertiert: Anfang
                    
                    elif event.key == pygame.K_END and prolog_shown and not qte_active:
                        scroll_offset = max_scroll  # Invertiert: Ende
                    
                    # Pfeiltasten für Command History (nur wenn nicht gescrollt)
                    elif event.key == pygame.K_UP and prolog_shown and not qte_active:
                        if scroll_offset == 0:  # Nur bei nicht-gescrolltem Terminal
                            if command_history:
                                if history_index == -1:
                                    history_index = len(command_history) - 1
                                elif history_index > 0:
                                    history_index -= 1
                                
                                if 0 <= history_index < len(command_history):
                                    input_text = command_history[history_index]
                                    cursor_position = len(input_text)
                        else:
                            # Wenn gescrollt: Scroll hoch (invertiert: weniger offset)
                            scroll_offset -= 3
                            scroll_offset = max(0, scroll_offset)
                    
                    elif event.key == pygame.K_DOWN and prolog_shown and not qte_active:
                        if scroll_offset == 0:  # Nur bei nicht-gescrolltem Terminal
                            if command_history and history_index != -1:
                                history_index += 1
                                
                                if history_index >= len(command_history):
                                    history_index = -1
                                    input_text = ""
                                    cursor_position = 0
                                else:
                                    input_text = command_history[history_index]
                                    cursor_position = len(input_text)
                        else:
                            # Wenn gescrollt: Scroll runter (invertiert: mehr offset)
                            scroll_offset += 3
                            scroll_offset = min(scroll_offset, max_scroll)
                    
                    else:
                        # QTE Mode: Einzelne Tasten W, A, S, D, E
                        if qte_active and event.unicode.upper() in ['W', 'A', 'S', 'D', 'E']:
                            process_command(event.unicode.upper())
                            check_qte_result()
                        # Normaler Input
                        elif prolog_shown and not qte_active and len(input_text) < 60 and event.unicode.isprintable():
                            # Füge Zeichen an Cursor-Position ein
                            input_text = input_text[:cursor_position] + event.unicode + input_text[cursor_position:]
                            cursor_position += 1
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    backspace_held = False
                elif event.key == pygame.K_DELETE:
                    delete_held = False
                elif event.key == pygame.K_LEFT:
                    left_held = False
                elif event.key == pygame.K_RIGHT:
                    right_held = False
                elif event.key == pygame.K_RETURN:
                    enter_held = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if current_state == MAP:
                    UNIT = scale(50) * map_zoom
                    cx = screen.get_width() / 2 - (map_camera_x * map_zoom * 50)
                    cy = screen.get_height() / 2 - (map_camera_y * map_zoom * 50)
                    if event.button == 3:  # Right click = drag node, block, or building
                        hit = get_node_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
                        if hit:
                            node_dragging = True
                            node_drag_key = hit
                            selected_block_idx = None
                        else:
                            # Check custom blocks first
                            blk_idx, handle = get_block_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
                            if blk_idx is not None:
                                selected_block_idx = blk_idx
                                if handle and handle != 'move':  # Resize corner
                                    block_resizing = True
                                    block_resize_handle = handle
                                else:  # Move block (border/title bar)
                                    block_moving = True
                                    gx, gy = screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
                                    blk = custom_blocks[blk_idx]
                                    block_move_offset = (blk['gx'] - gx, blk['gy'] - gy)
                            else:
                                selected_block_idx = None
                    elif event.button == 1:  # Left click = select block or pan camera
                        blk_idx, _ = get_block_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
                        if blk_idx is not None:
                            selected_block_idx = blk_idx
                        else:
                            selected_block_idx = None
                        map_dragging = True
                        map_drag_last_pos = event.pos
                elif event.button == 1:
                    if current_state == MENU:
                        for button in menu_buttons:
                            button.click()
                    elif current_state == OPTIONS:
                        for button in options_buttons:
                            button.click()
                            
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    map_dragging = False
                elif event.button == 3:
                    node_dragging = False
                    node_drag_key = None
                    block_resizing = False
                    block_resize_handle = None
                    block_moving = False
                    
            if event.type == pygame.MOUSEMOTION:
                if current_state == MAP:
                    UNIT = scale(50) * map_zoom
                    cx = screen.get_width() / 2 - (map_camera_x * map_zoom * 50)
                    cy = screen.get_height() / 2 - (map_camera_y * map_zoom * 50)
                    if node_dragging and node_drag_key:
                        # Move the node to new graph position
                        gx, gy = screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
                        GRAPH_LAYOUT[node_drag_key] = (gx, gy)
                    elif block_moving and selected_block_idx is not None:
                        gx, gy = screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
                        custom_blocks[selected_block_idx]['gx'] = gx + block_move_offset[0]
                        custom_blocks[selected_block_idx]['gy'] = gy + block_move_offset[1]
                    elif block_resizing and selected_block_idx is not None:
                        gx, gy = screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
                        blk = custom_blocks[selected_block_idx]
                        if 'r' in block_resize_handle:  # right side
                            blk['gw'] = max(1, gx - blk['gx'])
                        if 'b' in block_resize_handle:  # bottom side
                            blk['gh'] = max(1, gy - blk['gy'])
                        if 'l' in block_resize_handle:  # left side
                            new_x = gx
                            blk['gw'] = max(1, (blk['gx'] + blk['gw']) - new_x)
                            blk['gx'] = new_x
                        if 't' in block_resize_handle:  # top side
                            new_y = gy
                            blk['gh'] = max(1, (blk['gy'] + blk['gh']) - new_y)
                            blk['gy'] = new_y
                    elif map_dragging:
                        dx = event.pos[0] - map_drag_last_pos[0]
                        dy = event.pos[1] - map_drag_last_pos[1]
                        drag_speed = 0.1
                        map_camera_x -= dx * drag_speed / map_zoom
                        map_camera_y -= dy * drag_speed / map_zoom
                        map_drag_last_pos = event.pos
                    else:
                        # Hover detection
                        node_hovered_key = get_node_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
        
        # State-basiertes Rendering
        if current_state == INTRO:
            intro_done = draw_intro(current_time)
            if intro_done:
                current_state = MENU
                start_time = pygame.time.get_ticks()
                _start_menu_music()
        
        elif current_state == MENU:
            draw_menu(current_time)
        
        elif current_state == OPTIONS:
            draw_options(current_time)
        
        elif current_state == GAME:
            update_typewriter()
            draw_game(current_time)
            
        elif current_state == MAP:
            draw_map(current_time)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
