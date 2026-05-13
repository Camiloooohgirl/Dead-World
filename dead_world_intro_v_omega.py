import pygame
import sys
import math
import random
import time
import datetime
import os
from config import *
from render_utils import *
import render_utils
import command_handlers
import event_handlers
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

# Gun Sounds - für Schusswaffen
GUN_SOUND_DIR = os.path.join(BASE_DIR, "Game_music", "Gun Sounds")
GUN_SOUNDS = []
for _gs_file in sorted(os.listdir(GUN_SOUND_DIR)):
    if _gs_file.endswith(('.mp3', '.wav', '.ogg')):
        try:
            GUN_SOUNDS.append(pygame.mixer.Sound(os.path.join(GUN_SOUND_DIR, _gs_file)))
        except Exception:
            pass

# Punch/Melee Sounds - für Nahkampf
PUNCH_SOUND_DIR = os.path.join(BASE_DIR, "Game_music", "Punch_Sounds")
PUNCH_SOUNDS = []
for _ps_file in sorted(os.listdir(PUNCH_SOUND_DIR)):
    if _ps_file.endswith(('.mp3', '.wav', '.ogg')):
        try:
            PUNCH_SOUNDS.append(pygame.mixer.Sound(os.path.join(PUNCH_SOUND_DIR, _ps_file)))
        except Exception:
            pass

_current_gun_sound = None
_current_punch_sound = None

def play_random_gun_sound():
    """Spielt einen zufälligen Schuss-Sound ab"""
    global _current_gun_sound
    if GUN_SOUNDS:
        sound = random.choice(GUN_SOUNDS)
        sound.set_volume(game_settings.get('sfx_volume', 0.7))
        sound.play()
        _current_gun_sound = sound

def play_random_punch_sound():
    """Spielt einen zufälligen Nahkampf-Sound ab"""
    global _current_punch_sound
    if PUNCH_SOUNDS:
        sound = random.choice(PUNCH_SOUNDS)
        sound.set_volume(game_settings.get('sfx_volume', 0.7))
        sound.play()
        _current_punch_sound = sound

def stop_combat_sounds():
    """Stoppt alle Kampf-Sounds"""
    global _current_gun_sound, _current_punch_sound
    if _current_gun_sound:
        _current_gun_sound.stop()
        _current_gun_sound = None
    if _current_punch_sound:
        _current_punch_sound.stop()
        _current_punch_sound = None

# Scaling-Funktionen und Font-Cache in render_utils.py
current_resolution_index = 3  # Standard: Hoch (1680x1050)

# Fenster erstellen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Dead World")
clock = pygame.time.Clock()
fullscreen = False
init_render(screen)  # Scaling-Funktionen an Screen binden

# Module initialisieren die Zugriff auf das Hauptmodul brauchen
import sys as _sys
command_handlers.init_handlers(_sys.modules[__name__])
event_handlers.init_event_handlers(_sys.modules[__name__])

# Fonts
font_large = pygame.font.Font(None, 120)
font_medium = pygame.font.Font(None, 80)
font_small = pygame.font.Font(None, 50)
font_terminal = pygame.font.Font(None, 30)
font_tiny = pygame.font.Font(None, 25)

# Game States (Definitionen in config.py)
current_state = INTRO

# Pause-Menü
pause_selected_index = 0
_options_return_state = MENU  # Wohin nach Verlassen der Optionen zurückgekehrt wird

visited_rooms = set()  # Besuchte Räume (zB. für Resets/Stats)

# Menü-Navigation
menu_selected_index = 0
options_selected_index = 0  # 0=Auflösung, 1=Musik, 2=Effekte

# Game Settings
game_settings = {
    'music_volume': 0.15,
    'sfx_volume': 0.15,
    'difficulty': 'Normal',
    'resolution': 3  # Index in RESOLUTION_PRESETS
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

# Backspace-Repeat (Delays in config.py)
backspace_held = False
backspace_timer = 0
last_backspace_time = 0

#Biblio
bibliothek_4_schrank_geschoben = False
#Haus1 Tür
haus1_tür_auf = True
#Haus1 Dachbodentür
haus1_dachbodentür_auf = False
#Haus1 boxes
haus1_dachboden_box_geschoben = False
#Haus1 Nachttisch
nachtschrank_auf = False
#Safe
safe_auf_haus1 = False
safe_durchsucht_haus1 = False
# Numpad: wartet der naechste Befehl auf den 6-stelligen Code? (Pygame-freundlich, kein input())
numpad_awaiting_code = False
#krankenhaus
krankenhaus_schrank_geschoben = False
numpad_nutzen = False

# Key-Repeat für Cursor-Tasten
delete_held = False
last_delete_time = 0
left_held = False
last_left_time = 0
right_held = False
last_right_time = 0
enter_held = False
last_enter_time = 0
# key_initial_delay und key_repeat_delay in config.py

# Scroll-System
scroll_offset = 0
max_scroll = 0

# Typewriter-Effekt System
typewriter_queue = []          # Warteschlange für Zeilen die noch getippt werden
typewriter_current_line = ""   # Die aktuelle Zeile die getippt wird
typewriter_reveal_index = 0    # Wie viele Zeichen sichtbar sind
typewriter_last_time = 0       # Letzter Zeitpunkt an dem ein Zeichen hinzugefügt wurde
# TYPEWRITER_SPEED in config.py
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

# Kampfsystem (ZOMBIE_RESPAWN_COOLDOWN in config.py)
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
scored_items = set()            # Items die bereits Punkte gegeben haben
scored_kills = set()            # Räume in denen der erste Kill bereits gezählt wurde
game_start_ticks = 0            # pygame.time.get_ticks() beim Spielstart
# SAVE_FILE importiert aus config.py

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
    'goldener_pfeil': Item('goldener_pfeil', 'Goldener Pfeil', 'Ein uralter, golden schimmernder Pfeil. Er strahlt eine unheimliche Energie aus.', weight=1),
    'gehstock': Item('gehstock', 'Gehstock', 'Ein robuster, hölzerner Gehstock mit gebogenem Griff.', weight=2),
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

# Score-Werte, Parser-System, Verb-Listen und Responses importiert aus config.py
def spawn_chance():
    if random.random() < 0.15:  # 15% statt 50% – weniger Zombie-Spam
        return True
    return False

# FIST_LEVEL_BONUSES, weapons, food_items, enemies importiert aus config.py

# QTE System
qte_active = False
qte_sequence = []
qte_input = ""
qte_start_time = 0
# qte_duration in config.py
qte_callback = None

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
    'westliche_haus_gabelung': {  # Sub-street near Spawn
        'name': 'Westliche Weggabelung',
        'description': 'Eine Weggabelung. Verrostete Straßenschilder zeigen in alle Richtungen. Im OSTEN die südliche Straße. Nach NORDEN die nordwestliche Weggabelung. Im SÜDEN das Krankenhaus.',
        # Removed westen → westlich_krankenhaus_erweiterung (deprecated). Western district
        # (Maze/Friedhof/etc.) is now reached via Puente Juanchito.
        'exits': {'osten': 'suedlich_haus', 'norden': 'nord_westliche_weggabelung', 'süden': 'krankenhaus_straße'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_straße': {#Krankenhaus
        'name': 'Krankenhaus Straße',
        'description': 'Du stehst auf der Straße vor dem Krankenhaus. Im NORDEN führt die Straße zur westlichen Weggabelung. Im WESTEN ist der Eingang zum Krankenhaus. Nach SÜDEN geht es zur Home Depot Weggabelung Nord Ost. Über einen Schleichweg im NORDWESTEN (an der Hospital-Westseite vorbei) erreicht man die Hacienda Straße.',
        'exits': {'norden': 'westliche_haus_gabelung', 'westen': 'krankenhaus_eingang', 'süden': 'home_depot_weggabelung_nord_ost', 'nordwesten': 'hacienda_straße'},
        'items': [],
        'in_development': False,
        'spawn_chance': True,
        'zombie_spawn': False
    },
    'krankenhaus_eingang': {#Krankenhaus
        'name': 'Krankenhaus Eingang',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'osten': 'krankenhaus_straße', 'Westen': 'krankenhaus_wartebereich'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_wartebereich': {#Krankenhaus
        'name': 'Krankenhaus - Wartebereich',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'osten': 'krankenhaus_eingang', 'Westen': 'krankenhaus_flur'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur': {#Krankenhaus
        'name': 'Krankenhaus - Flur',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'osten': 'krankenhaus_wartebereich','Süden':'krankenhaus_Rezeption' },
        'items': [],
        'in_development': False
    },
    'krankenhaus_Rezeption': {#Krankenhaus
        'name': 'Krankenhaus - Rezeption',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'osten': 'krankenhaus_wartebereich','westen': 'krankenhaus_flur_osten'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_osten': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Osten',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_flur_nord_ost','westen': 'krankenhaus_flur_süden','osten': 'krankenhaus_Rezeption'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_nord_ost': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Nord-Ost',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen': 'krankenhaus_flur_norden','Süden': 'krankenhaus_flur_osten'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_norden': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Norden',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen': 'krankenhaus_labor_rezeption','osten': 'krankenhaus_flur_nord_ost'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_labor_rezeption': {#Krankenhaus
        'name': 'Krankenhaus - Labor Rezeption',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen': 'krankenhaus_labor','osten': 'krankenhaus_flur_norden','Süden': 'krankenhaus_zwischen_flur'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_Labor': {#Krankenhaus
        'name': 'Krankenhaus - Labor',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'osten': 'krankenhaus_labor_rezeption','Süden':'krankenhaus_geheim_treppe'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_geheim_treppe': {#Krankenhaus
        'name': 'Krankenhaus - Labor Treppe',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_Labor','Runter':''},
        'items': [],
        'in_development': False
    },
    'gl_empfang': {#Geheimlabor
        'name': 'Geheimlabor - Empfang',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'hoch':'krankenhaus_geheim_treppe','Süden':'Lagerraum','Osten' : 'gl_sicherheits_flur'},
        'items': [],
        'in_development': False
    },
    'gl_lagerraum': {#Geheimlabor
        'name': 'Geheimlabor - Lagerraum',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden':'gl_empfang'},
        'items': ['ID Armband Lvl 1'],
        'in_development': False
    }, 
    'gl_sicherheits_flur': {#Geheimlabor
        'name': 'Geheimlabor - Sicherheits Flur',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen':'gl_empfang','Osten': 'gl_sicherheits_lvl1_flur'},
        'items': [],
        'in_development': False
    },
    'gl_sicherheits_lvl1_flur': {#Geheimlabor
        'name': 'Geheimlabor - Sicherheit lvl1 Flur',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden':'gl_Schlafsaal','Osten': 'gl_kafeteria','Süden': 'gl_sicherheits_lvl2_flur','westen':'gl_sicherheits_flur'},
        'items': [],
        'in_development': False
    },
    'gl_schlafsaal': {#Geheimlabor
        'name': 'Geheimlabor - Schlafsaal',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden':'gl_schlafzimmer1','Westen': ' gl_schlafzimmer2','Osten': 'gl_schlafzimmer3','Süden': 'gl_sicherheits_lvl1_flur'},
        'items': [],
        'in_development': False
    }, 
    'gl_schlafzimmer1': {#Geheimlabor
        'name': 'Geheimlabor - Schlafzimmer 1',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Süden': 'gl_schlafsaal'},
        'items': [],
        'in_development': False
    }, 
    'gl_schlafzimmer2': {#Geheimlabor
        'name': 'Geheimlabor - Schlafzimmer 2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'gl_schlafsaal'},
        'items': [],
        'in_development': False
    }, 
    'gl_schlafzimmer3': {#Geheimlabor
        'name': 'Geheimlabor - Schlafzimmer 3',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen': 'gl_schlafsaal'},
        'items': [],
        'zombie_spawn': True,
        'in_development': False
    },
    'gl_kafeteria': {#Geheimlabor
        'name': 'Geheimlabor - Kafeteria',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'gl_küche','Süden': 'gl_sicherheits_lvl1_flur'},
        'items': [],
        'in_development': False
    }, 
    'gl_küche': {#Geheimlabor
        'name': 'Geheimlabor - Schlafsaal',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'gl_kafeteria'},
        'items': [],
        'in_development': False
    }, 
    'gl_sicherheits_lvl2_flur': {#Geheimlabor
        'name': 'Geheimlabor - Sicherheit lvl2 Flur',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden':'gl_sicherheits_lvl1_flur','Osten': 'gl_presentationsraum','Westen':'gl_labor','Süden':'gl_bio_labor'},
        'items': [],
        'in_development': False
    },
    'gl_labor': {#Geheimlabor
        'name': 'Geheimlabor - Labor',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'gl_sicherheits_lvl2_flur','Süden':'gl_labor_flur','westen':'gl_testlb_flur'},
        'items': [],
        'in_development': False
    },
    'gl_labor_flur': {#Geheimlabor
        'name': 'Geheimlabor - Labor Flur',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'gl_Labor','Osten':'gl_drogen_test_labor'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_zwischen_flur': {#Krankenhaus
        'name': 'Krankenhaus - Zwischenflur',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_labor_rezeption','Süden': 'krankenhaus_preperations_raum'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_preperations_raum': {#Krankenhaus
        'name': 'Krankenhaus - Vorbereitungs Raum',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Süden': 'krankenhaus_OP_raum', 'osten': 'krankenhaus_flur_süd_westen'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_OP_raum': {#Krankenhaus
        'name': 'Krankenhaus - Operations Raum',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_preperations_raum'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_süd_westen': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Süd-Westen',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_flur_westen','Süden': 'krankenhaus_treppenhaus_flur', 'Westen': 'krankenhaus_preperations_raum'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_westen': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Westen',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_flur_nord-westen_1','Süden': 'krankenhaus_flur_süd_westen'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_nord_westen_1': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Nord-Westen',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_flur_nord-westen_2','Süden': 'krankenhaus_flur_westen'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_nord_westen_2': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Nord-Westen-2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Süden': 'krankenhaus_flur_nord_westen_1'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_treppenhaus_flur': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Treppenhaus',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Süden': 'krankenhaus_Treppe','Osten':'krankenhaus_kaputter_aufzug','Norden': 'krankenhaus_flur_süd_westen'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_Treppe': {#Krankenhaus
        'name': 'Krankenhaus - Treppe F1',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'hoch': 'krankenhaus_Treppe_F2','Norden': 'krankenhaus_treppenhaus_flur'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_Treppe_F2': {#Krankenhaus
        'name': 'Krankenhaus - Treppe F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'runter': 'krankenhaus_Treppe_F1','Norden': 'krankenhaus_treppenhaus_flur_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_treppenhaus_flur_f2': {#Krankenhaus
        'name': 'Krankenhaus - Treppehaus F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Süden': 'krankenhaus_Treppe_F2','Norden': 'krankenhaus_flur_westen_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_westen_f2': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Westen-F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_flur_norden_f2','Osten': 'krankenhaus_flur_mitte_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_norden_f2': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Norden-F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen': 'krankenhaus_aufnahmeraum','Norden': 'krankenhaus_mitarbeiter_flur','Süden': 'krankenhaus_flur_westen_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_aufnahmeraum': {#Krankenhaus
        'name': 'Krankenhaus - Aufnahme ',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'krankenhaus_flur_norden_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_mitte_f2': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Mitte',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'krankenhaus_schwesterstation','Süden': 'krankenhaus_flur_osten_f2','Westen': 'krankenhaus_flur_westen_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_mitarbeiter_flur': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Norden-F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_mitarbeiter_raum','Süden': 'krankenhaus_flur_norden_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_mitarbeiter_raum': {#Krankenhaus
        'name': 'Krankenhaus - Mitarbeiter Raum',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen': 'krankenhaus_schließfach_raum','Süden': 'krankenhaus_mitarbeiter_flur'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_schließfach_raum': {#Krankenhaus
        'name': 'Krankenhaus - Schließfach Raum',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'krankenhaus_mitarbeiter_raum'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_schwesterstation': {#Krankenhaus
        'name': 'Krankenhaus - Schwesternstation',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_krankenzimmer','Süden': 'krankenhaus_waschraum_flur'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_krankenzimmer': {#Krankenhaus
        'name': 'Krankenhaus - Krankenzimmer',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Süden': 'krankenhaus_schwesterstation'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_waschraum_flur': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Waschraum Osten',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen': 'krankenhaus_waschraum_flur_süden','Norden': 'krankenhaus_schwesterstation'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_waschraum_flur_süden': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Waschraum Süden',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'krankenhaus_waschraum_flur','Norden': 'krankenhaus_waschraum'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_waschraum': {#Krankenhaus
        'name': 'Krankenhaus - Waschraum',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Süden': 'krankenhaus_waschraum_flur_süden','Norden': 'krankenhaus_flur_osten_f2','Osten':'krankenhaus_behandlungs_raum'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_osten_f2': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Osten F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Norden': 'krankenhaus_flur_mitte_f2','Süden': 'krankenhaus_waschraum','Westen':'krankenhaus_flur_süden_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_süden_f2': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Süden F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'krankenhaus_flur_osten_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_flur_osten_f2': {#Krankenhaus
        'name': 'Krankenhaus - Flur: Osten F2',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Osten': 'krankenhaus_flur__f2','Süden': 'krankenhaus_waschraum','Westen':'krankenhaus_flur_süden_f2'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_behandlungs_raum': {#Krankenhaus
        'name': 'Krankenhaus - Behandlungsraum',
        'description': 'Kaputte Glastüren stehen offen. Aus dem Inneren des Krankenhauses hörst du Zombies schreien. Im OSTEN führt der Weg zurück auf die Straße.',
        'exits': {'Westen':'krankenhaus_waschraum'},
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
    'bibliothek_straße': {  # Sub-street near Library
        'name': 'Bibliothek Straße',
        'description': 'Eine ruhige Straße. Im NORDOSTEN siehst du den Eingang zur Bibliothek. Im OSTEN führt der Weg zurück zur nordwestlichen Weggabelung.',
        'exits': {'norden': 'bibliothek_eingang', 'osten': 'nord_westliche_weggabelung'},
        'items': [],
        'in_development': False,
        'spawn_chance': False,
        'zombie_spawn': False
    },
    'bibliothek_eingang': {  # Idea-Map: Library (R1C3)
        'name': 'Bibliothek Eingang',
        'description': 'Du stehst vor den Türen der Bibliothek. Leises Knarzen ist von drinnen zu hören.',
        'exits': {'norden': 'bibliothek_1.1', 'süden': 'krankenhaus_eingang'},
        'items': [],
        'in_development': False
    },
    'bibliothek_1.1': {#Bibliothek
        'name': 'Bibliothek 1',
        'description': '',
        'exits': {'südwesten': 'bibliothek_eingang', 'westen': 'bibliothek_1.2', 'osten': 'bibliothek_2'},
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
        'description': 'Ein staubiger Lesebereich. Im NORDEN versperrt ein schweres BÜCHERREGAL den Durchgang. Wenn du dich dagegenstemmst, könntest du es vielleicht zur Seite SCHIEBEN.',
        'exits': {'süden': 'bibliothek_2'},
        'items': [],
        'in_development': False
    },
    'bibliothek_4': {#Bibliothek
        'name': 'Bibliothek',
        'description': 'Hinter dem verschobenen Bücherregal öffnet sich ein weiterer Bereich der Bibliothek. Eine alte KISTE steht in der Ecke.',
        'exits': {'westen': 'bibliothek_5'},
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
        'exits': {'westen': 'norden_straße', 'süden': 'nord_östliche_weggabelung', 'norden': 'walmart_eingang', 'nordosten': 'noerdlich_walmart_straße' },
        'items': [],
        'in_development': False,
        'spawn_chance': True,
        'zombie_spawn': False
    },
    'walmart_eingang': {#Walmart
        'name': 'Walmart Eingang',
        'description': 'Die Schiebetüren aus glas sind kaputt, boden voller scherben, die kannst im Walmart zombies durch Regale sehen.',
        'exits': {'süden': 'parkplatz', 'norden': 'walmart_1'},
        'items': [],
        'in_development': False
    },
    'walmart_1': {#Walmart
        'name': 'Walmart',
        'description': 'Du stehst im walmart, die siehst viele umgefallene Regale, und viele Artikel liegen auf dem Boden. Links von dir bemerkst du einen durchgang.',
        'exits': {'süden': 'parkplatz', 'westen': 'walmart_2'},
        'items': [],
        'in_development': True
    },
    'walmart_2': {#Walmart
        'name': 'Walmart',
        'description': 'Du stehst in der unteren linken ecke des walmarts, weiterhin nur umgefallene Regale in sicht. Es sieht so aus als könntest du gerade aus weiter gehen.',
        'exits': {'norden': 'walmart_3','osten': 'walmart_3'},
        'items': [],
        'in_development': True
    },
    'walmart_3': {#Walmart
        'name': 'Walmart',
        'description': 'Weitere Regale am stehen, gerade aus wird dein weg von umgefallenen regalen blockiert, du siehst einen durchgang rechts von dir.',
        'exits': {'süden': 'walmart_2', 'osten': 'walmart_4'},
        'items': ['schokoriegel', 'energieriegel'],
        'in_development': True
    },
    'walmart_4': {#Walmart
        'name': 'Walmart',
        'description': 'Weiter drinne im Walmart siehst du weiter hin nur umgefallene Regale. Der weg führt weiter hin nach rechts.',
        'exits': {'osten': 'walmart_5', 'westen': 'walmart_3'},
        'items': [],
        'in_development': True
    },
    'walmart_5': {#Walmart
        'name': 'Walmart',
        'description': 'In der Mitte vom Walmart hast du eine halbwegs gute sicht durch den Laden, in der unteren rechten ecke des Ladens siehst du etwas liegen',
        'exits': {'norden': 'walmart_6', 'westen': 'walmart_4'},
        'items': [],
        'enemy': 'zombie',
        'in_development': True,
        'zombie_spawn': True
    },
    'walmart_6': {#Walmart
        'name': 'Walmart',
        'description': 'Der weg nach rechts ist nun abgeblockt von Regalen. Dafür ist gerade aus nun der weg frei.',
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
        'items': ['gehstock'],
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
        'exits': {'norden': 'oestlich_weggabelung', 'osten': 'park', 'süden': 'skyscraper_weggabelung', 'südosten': 'oestlich_park_erweiterung' },
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
    'haus1_Flur': {#Haus1
        'name': 'Haus 1 - Flur',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Norden': 'haus1_vordertür', 'Süden': 'haus1_wohnzimmer', 'Osten': 'haus1_Flur2'},
        'items': [],
        'in_development': True
    },
    'haus1_Flur2': {#Haus1
        'name': 'Haus 1 - Flur2',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Süden': 'haus1_dachbodentür', 'Osten': 'haus1_Flur3', 'Westen': 'haus1_schlafzimmer2'},
        'items': [],
        'in_development': True
    },
    'haus1_dachbodentür': {#Haus1
        'name': 'Haus 1 - Dachbodeneingang',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Norden': 'haus1_Flur', 'Hoch': 'haus1_dachboden'},
        'items': [],
        'in_development': True
    },
    'haus1_dachboden': {#Haus1
        'name': 'Haus 1 - Dachboden',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Runter': 'haus1_dachbodentür'},
        'items': [],
        'in_development': True
    },
    'haus1_wohnzimmer': {#Haus1
        'name': 'Haus 1 - Wohnzimmer',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Norden': 'haus1_Flur'},
        'items': [],
        'in_development': True
    },
    'haus1_schlafzimmer2': {#Haus1
        'name': 'Haus 1 - Schlafzimmer 2',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Osten': 'haus1_Flur2'},
        'items': [],
        'in_development': True
    },
    'haus1_schlafzimmer': {#Haus1
        'name': 'Haus 1 - Schlafzimmer',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Süden': 'haus1_Flur3'},
        'items': [],
        'in_development': True
    },
    'haus1_badezimmer': {#Haus1
        'name': 'Haus 1 - Badezimmer',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Westen': 'haus1_Flur3'},
        'items': [],
        'in_development': True
    },
    'haus1_küche': {#Haus1
        'name': 'Haus 1 - Küche',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Norden': 'haus1_Flur3'},
        'items': [],
        'in_development': True
    },
    'haus1_Flur3': {#Haus1
        'name': 'Haus 1 - Flur3',
        'description': 'Du stehst im Eingangsbereich von Haus 1. Es riecht muffig und der Boden knarzt unter deinen Füßen.',
        'exits': {'Norden': 'haus1_schlafzimmer', 'Westen': 'haus1_Flur2', 'Süden': 'haus1_küche', 'Osten': 'haus1_badezimmer'},
        'items': [],
        'in_development': True
    },
    'haus2': { #House 2
        'name': 'Haus 2',
        'description': 'Du stehst vor einem verlassenen Haus. Die Tür ist verriegelt, durch die zerbrochenen Fenster siehst du nur Dunkelheit. Im WESTEN führt die östliche Straße zurück zum Spawn-Bereich. Im OSTEN führt der Weg zum Wasserpark.',
        'exits': {'westen': '', 'osten': ''},
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
            'main': ['krankenhaus_straße', 'krankenhaus_eingang','krankenhaus_wartebereich'],
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

# ===== TRANSITIONS (abgeleitet aus exits) =====
# Für Bewegung gilt nur noch rooms[room]['exits'].
# Diese Liste existiert nur für die Karten-/Edge-Anzeige.
def _normalize_direction(value):
    if not isinstance(value, str):
        return ""
    return value.strip().lower()

def _resolve_room_key(value):
    """Resolve target room keys tolerant against small naming mismatches."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate in rooms:
        return candidate
    lowered = candidate.lower()
    for rk in rooms:
        if rk.lower() == lowered:
            return rk
    normalized = candidate.replace("-", "_")
    if normalized in rooms:
        return normalized
    normalized_lower = normalized.lower()
    for rk in rooms:
        if rk.lower() == normalized_lower:
            return rk
    return None

def sanitize_room_exits():
    """Normalisiert exits: Richtungen klein, Zielräume auf gültige Keys auflösen."""
    fixed = 0
    removed = 0
    for _room_key, _room_data in rooms.items():
        _raw_exits = _room_data.get('exits', {})
        if not isinstance(_raw_exits, dict):
            _room_data['exits'] = {}
            removed += 1
            continue

        _new_exits = {}
        for _dir, _target in _raw_exits.items():
            _norm_dir = _normalize_direction(_dir)
            _resolved_target = _resolve_room_key(_target)
            if not _norm_dir or not _resolved_target:
                removed += 1
                continue
            _new_exits[_norm_dir] = _resolved_target
            if _norm_dir != _dir or _resolved_target != _target:
                fixed += 1

        _room_data['exits'] = _new_exits

    if fixed or removed:
        print(f"[MAP] Exits bereinigt: {fixed} korrigiert, {removed} entfernt")

def rebuild_transitions_from_exits():
    transitions = []
    for _from_room, _room_data in rooms.items():
        for _dir_from, _to_room in _room_data.get('exits', {}).items():
            _resolved_to = _resolve_room_key(_to_room)
            if not _resolved_to:
                continue
            _dir_to = None
            for _rev_dir, _rev_dest in rooms[_resolved_to].get('exits', {}).items():
                if _resolve_room_key(_rev_dest) == _from_room:
                    _dir_to = _normalize_direction(_rev_dir)
                    break
            transitions.append({
                'id': f'edge_{_from_room}_{_normalize_direction(_dir_from)}',
                'type': 'passage',
                'from': _from_room,
                'to': _resolved_to,
                'dir_from': _normalize_direction(_dir_from),
                'dir_to': _dir_to,
                'locked': False,
                'trigger': None,
                'lock_msg': None,
            })
    return transitions

sanitize_room_exits()
TRANSITIONS = rebuild_transitions_from_exits()

def get_room_context(room_key):
    """Returns (building_key, building_name, floor_key) for a room"""
    ctx = _room_to_container.get(room_key)
    if ctx:
        bldg = BUILDING_HIERARCHY[ctx[0]]
        return (ctx[0], bldg['name'], ctx[1])
    return ('unbekannt', 'Unbekannt', 'unbekannt')

def get_transitions_from(room_key):
    """Returns list of (direction, target_room, transition) from this room."""
    result = []
    room = rooms.get(room_key, {})
    for d, target in room.get('exits', {}).items():
        resolved_target = _resolve_room_key(target)
        if resolved_target:
            result.append((_normalize_direction(d), resolved_target, {'locked': False}))
    return result

def try_transition(room_key, direction):
    """Attempt to move from room_key in direction. Returns (success, target, transition, message)."""
    wanted = _normalize_direction(direction)
    room = rooms.get(room_key, {})
    for d, target in room.get('exits', {}).items():
        resolved_target = _resolve_room_key(target)
        if _normalize_direction(d) == wanted and resolved_target:
            return (True, resolved_target, {'locked': False, 'trigger': None}, None)
    return (False, None, None, 'Du kannst nicht in diese Richtung gehen.')

def unlock_transition(transition_id):
    """Kompatibilitätsfunktion (Transition-Locks wurden entfernt)."""
    return None

def reset_transitions():
    """Kompatibilitätsfunktion (keine Transition-Locks mehr)."""
    global TRANSITIONS
    TRANSITIONS = rebuild_transitions_from_exits()


def apply_bibliothek_bookshelf_state():
    """Synchronisiert die Exits zwischen bibliothek_3 <-> bibliothek_4 mit
    dem Flag `bibliothek_4_schrank_geschoben`.

    Solange das Bücherregal nicht geschoben ist, fehlen die Norden/Süden-
    Übergänge. Nach dem Schieben werden sie hinzugefügt und die Karte
    (TRANSITIONS) neu aufgebaut.
    """
    global TRANSITIONS
    b3 = rooms.get('bibliothek_3')
    b4 = rooms.get('bibliothek_4')
    if not b3 or not b4:
        return
    if bibliothek_4_schrank_geschoben:
        b3.setdefault('exits', {})['norden'] = 'bibliothek_4'
        b4.setdefault('exits', {})['süden'] = 'bibliothek_3'
        b3['description'] = (
            'Ein staubiger Lesebereich. Das schwere Bücherregal steht jetzt '
            'zur Seite geschoben — der Weg nach NORDEN ist frei.'
        )
    else:
        b3.get('exits', {}).pop('norden', None)
        b4.get('exits', {}).pop('süden', None)
        b3['description'] = (
            'Ein staubiger Lesebereich. Im NORDEN versperrt ein schweres '
            'BÜCHERREGAL den Durchgang. Wenn du dich dagegenstemmst, '
            'könntest du es vielleicht zur Seite SCHIEBEN.'
        )
    TRANSITIONS[:] = rebuild_transitions_from_exits()


def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    init_render(screen)

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
        self.disabled = False
        self.rect = None
    
    def draw(self, surface, current_time):
        button_font = get_scaled_font(50)
        
        if self.disabled:
            color = GRAY
            shadow_color = (30, 25, 30)
        elif self.hovered:
            color = HOVER_RED
            shadow_color = DEEP_RED
        else:
            color = BLOOD_RED
            shadow_color = DEEP_RED
        
        # Schatten
        shadow = button_font.render(self.text, True, shadow_color)
        shadow_rect = shadow.get_rect(center=(self.pos[0] + scale(2), self.pos[1] + scale(2)))
        surface.blit(shadow, shadow_rect)
        
        # Haupt-Text
        text_surf = button_font.render(self.text, True, color)
        self.rect = text_surf.get_rect(center=self.pos)
        surface.blit(text_surf, self.rect)
        
        # Unterstreichungs-Animation bei Hover (nicht bei disabled)
        if self.hovered and not self.disabled:
            line_width = int(self.rect.width * (0.5 + 0.5 * math.sin(current_time * 0.005)))
            line_x = self.rect.centerx - line_width // 2
            line_y = self.rect.bottom + scale(4)
            pygame.draw.line(surface, HOVER_RED, (line_x, line_y), (line_x + line_width, line_y), max(1, scale(2)))
    
    def check_hover(self, mouse_pos):
        if self.disabled:
            self.hovered = False
            return False
        if self.rect:
            self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered
    
    def click(self):
        if self.hovered and self.action and not self.disabled:
            self.action()

def start_game():
    global current_state, game_history, current_room, player_inventory, prolog_shown, prolog_lines, prolog_line_index, menu_music_playing, visited_rooms, zombie_kill_times
    global game_score, game_moves, view_mode, visited_rooms_desc, game_start_ticks, pending_ambiguity
    global bibliothek_4_schrank_geschoben
    current_state = GAME
    game_history = []
    current_room = 'start'
    player_inventory = ['fäuste']
    prolog_shown = False
    prolog_line_index = 0
    visited_rooms = {'start'}  # Start-Raum als besucht markieren
    visited_rooms_desc = set()
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

    # Puzzle-Flags für neuen Spielstart zurücksetzen, damit z.B. das
    # Bücherregal in der Bibliothek den Durchgang wieder blockiert.
    bibliothek_4_schrank_geschoben = False
    apply_bibliothek_bookshelf_state()

    # Menü-Musik ausblenden
    pygame.mixer.music.fadeout(800)
    menu_music_playing = False
    
    # Prolog in Zeilen aufteilen
    prolog_lines = [line for line in PROLOG_TEXT.split('\n') if line.strip() or line == '']
    
    # Prolog-Text sofort anzeigen (process_command übernimmt die Logik)
    process_command("")

def load_game_from_menu():
    """Lädt einen gespeicherten Spielstand direkt aus dem Hauptmenü."""
    import json
    global current_state, current_room, player_inventory, game_score, game_moves, view_mode
    global visited_rooms, visited_rooms_desc, game_start_ticks, prolog_shown, prolog_lines, prolog_line_index
    global bibliothek_4_schrank_geschoben, haus1_tür_auf, menu_music_playing
    global haus1_dachbodentür_auf, haus1_dachboden_box_geschoben
    global nachtschrank_auf, safe_auf_haus1, safe_durchsucht_haus1
    global krankenhaus_schrank_geschoben, numpad_nutzen
    global scored_items, scored_kills, pending_ambiguity, game_history
    
    if not os.path.exists(SAVE_FILE):
        return  # Kein Spielstand vorhanden
    
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return  # Fehler beim Laden → nichts tun
    
    # Wechsle zum Spielzustand
    current_state = GAME
    prolog_shown = True  # Prolog überspringen, direkt ins Spiel
    prolog_lines = []
    prolog_line_index = 0
    pending_ambiguity = None
    game_history = []
    
    # Menü-Musik ausblenden
    pygame.mixer.music.fadeout(800)
    menu_music_playing = False
    
    # Spielstand laden (gleiche Logik wie restore_game)
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
    TRANSITIONS[:] = rebuild_transitions_from_exits()
    bibliothek_4_schrank_geschoben = data.get('bibliothek_4_schrank_geschoben', False)
    haus1_tür_auf = data.get('haus1_tür_auf', True)
    haus1_dachbodentür_auf = data.get('haus1_dachbodentür_auf', False)
    haus1_dachboden_box_geschoben = data.get('haus1_dachboden_box_geschoben', False)
    nachtschrank_auf = data.get('nachtschrank_auf', False)
    safe_auf_haus1 = data.get('safe_auf_haus1', False)
    safe_durchsucht_haus1 = data.get('safe_durchsucht_haus1', False)
    krankenhaus_schrank_geschoben = data.get('krankenhaus_schrank_geschoben', False)
    numpad_nutzen = data.get('numpad_nutzen', False)
    # Bibliotheks-Bücherregal-Übergang anhand des geladenen Flags rekonstruieren.
    apply_bibliothek_bookshelf_state()
    for ik, charge_val in data.get('item_charges', {}).items():
        if ik in ITEM_DEFS:
            ITEM_DEFS[ik].charge = charge_val
    elapsed = data.get('elapsed_ms', 0)
    game_start_ticks = pygame.time.get_ticks() - elapsed
    scored_items = set(data.get('scored_items', []))
    scored_kills = set(data.get('scored_kills', []))
    
    add_to_history("Spielstand geladen.")
    add_to_history("")
    describe_room()

def show_options():
    global current_state, _options_return_state
    _options_return_state = MENU
    current_state = OPTIONS

def back_to_menu():
    global current_state
    current_state = _options_return_state
    if current_state == MENU:
        _start_menu_music()

def resume_game():
    """Setzt das pausierte Spiel fort."""
    global current_state
    current_state = GAME

def pause_show_options():
    """Öffnet die Optionen aus dem Pause-Menü heraus."""
    global current_state, _options_return_state
    _options_return_state = PAUSED
    current_state = OPTIONS

def pause_to_main_menu():
    """Verlässt das laufende Spiel und kehrt zum Hauptmenü zurück."""
    global current_state
    current_state = MENU
    _start_menu_music()

def pause_save_game():
    """Speichert den Spielstand aus dem Pause-Menü heraus."""
    save_game()

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
    init_render(screen)

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
    """Bewege Spieler in eine Richtung (via rooms['exits'])."""
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
    
    # Timeskip-Trigger jetzt direkt über Raum/Route statt Transition-Objekt
    if rooms.get(current_room, {}).get('trigger_timeskip') and target == 'spawn':
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


# === CLASSIC MECHANICS: Helper-Funktionen ===

def add_score(action_key, amount=None, context=None):
    """Zork-style Punkte vergeben. context = item_key oder room_key für Dedup."""
    global game_score
    # Dedup: jedes Item gibt nur einmal Punkte
    if action_key == 'item_pickup' and context:
        if context in scored_items:
            return
        scored_items.add(context)
    # Dedup: erster Zombie-Kill pro Raum gibt Punkte, Respawns nicht
    if action_key == 'zombie_kill' and context:
        if context in scored_kills:
            return
        scored_kills.add(context)
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
        'elapsed_ms': pygame.time.get_ticks() - game_start_ticks,
        'bibliothek_4_schrank_geschoben': bibliothek_4_schrank_geschoben,
        'haus1_tür_auf': haus1_tür_auf,
        'haus1_dachbodentür_auf': haus1_dachbodentür_auf,
        'haus1_dachboden_box_geschoben': haus1_dachboden_box_geschoben,
        'nachtschrank_auf': nachtschrank_auf,
        'safe_auf_haus1': safe_auf_haus1,
        'safe_durchsucht_haus1': safe_durchsucht_haus1,
        'krankenhaus_schrank_geschoben': krankenhaus_schrank_geschoben,
        'numpad_nutzen': numpad_nutzen,
        'item_charges': {ik: idef.charge for ik, idef in ITEM_DEFS.items() if idef.max_charge >= 0},
        'scored_items': list(scored_items),
        'scored_kills': list(scored_kills),
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
    global haus1_dachbodentür_auf, haus1_dachboden_box_geschoben
    global nachtschrank_auf, safe_auf_haus1, safe_durchsucht_haus1
    global krankenhaus_schrank_geschoben, numpad_nutzen
    global scored_items, scored_kills
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
    TRANSITIONS[:] = rebuild_transitions_from_exits()
    bibliothek_4_schrank_geschoben = data.get('bibliothek_4_schrank_geschoben', False)
    haus1_tür_auf = data.get('haus1_tür_auf', True)
    haus1_dachbodentür_auf = data.get('haus1_dachbodentür_auf', False)
    haus1_dachboden_box_geschoben = data.get('haus1_dachboden_box_geschoben', False)
    nachtschrank_auf = data.get('nachtschrank_auf', False)
    safe_auf_haus1 = data.get('safe_auf_haus1', False)
    safe_durchsucht_haus1 = data.get('safe_durchsucht_haus1', False)
    krankenhaus_schrank_geschoben = data.get('krankenhaus_schrank_geschoben', False)
    numpad_nutzen = data.get('numpad_nutzen', False)
    # Bibliotheks-Bücherregal-Übergang anhand des geladenen Flags rekonstruieren.
    apply_bibliothek_bookshelf_state()
    for ik, charge_val in data.get('item_charges', {}).items():
        if ik in ITEM_DEFS:
            ITEM_DEFS[ik].charge = charge_val
    elapsed = data.get('elapsed_ms', 0)
    game_start_ticks = pygame.time.get_ticks() - elapsed
    scored_items = set(data.get('scored_items', []))
    scored_kills = set(data.get('scored_kills', []))
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
            add_score('item_pickup', context=item_key)
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
    add_score('item_pickup', context=item_key)
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
    """Verarbeitet Spielerbefehle — dispatcht an command_handlers.py"""
    global current_room, prolog_shown, prolog_line_index, qte_active, qte_input, command_history, history_index, current_state
    global pending_ambiguity, game_moves, view_mode, game_score
    
    # Füge Command zur History hinzu (außer im QTE oder Prolog)
    if prolog_shown and not qte_active and command.strip():
        command_history.append(command)
        if len(command_history) > 50:
            command_history.pop(0)
    
    history_index = -1
    
    # QTE-Modus
    if qte_active:
        qte_input += command.upper()
        return
    
    # Prolog-Modus
    if not prolog_shown:
        if prolog_line_index < len(prolog_lines):
            end_index = min(prolog_line_index + 3, len(prolog_lines))
            for i in range(prolog_line_index, end_index):
                add_to_history(prolog_lines[i])
            prolog_line_index = end_index
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

    # Zähle Züge
    if cmd and prolog_shown:
        game_moves += 1
        tick_msgs = tick_hidden_systems()
        for _tmsg in tick_msgs:
            add_to_history(_tmsg)

    # === DISPATCHER — delegiert an command_handlers.py ===
    if command_handlers.handle_help(cmd): return
    if command_handlers.handle_movement(cmd): return
    if command_handlers.handle_item_commands(cmd): return
    if command_handlers.handle_look_map(cmd): return
    if command_handlers.handle_combat_commands(cmd): return
    if command_handlers.handle_container_commands(cmd): return
    if command_handlers.handle_interaction_commands(cmd): return
    if command_handlers.handle_system_commands(cmd): return
    command_handlers.handle_unknown_command(cmd, words)

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
    play_random_gun_sound()
    
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
            add_score('zombie_kill', context=current_room)
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
    # Punch-Sound nur bei Nahkampf, Zombie-Sound bei Fernkampf-Gegenangriff
    if player_stats.get('weapon_type') == 'ranged':
        play_random_zombie_sound()
    else:
        play_random_punch_sound()
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
        TRANSITIONS[:] = rebuild_transitions_from_exits()
        
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
        play_random_punch_sound()
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
            add_score('zombie_kill', context=current_room)
            
            # Raumspezifische Belohnungen
            if current_room == 'start':
                rooms['start'].setdefault('exits', {})['norden'] = 'corridor'
                TRANSITIONS[:] = rebuild_transitions_from_exits()
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
        play_random_punch_sound()
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
            TRANSITIONS[:] = rebuild_transitions_from_exits()
            
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
    
    # --- Minimalist Top Bar ---
    w = screen.get_width()
    bar_height = scale(35)
    bar_pad = scale(10)
    pygame.draw.rect(screen, (0, 0, 0), (0, 0, w, bar_height))

    # Sans-serif font for the bar (cached to avoid per-frame allocation)
    _bar_font_size = scale(18)
    if not hasattr(draw_game, '_bar_font_cache') or draw_game._bar_font_cache[0] != _bar_font_size:
        try:
            draw_game._bar_font_cache = (_bar_font_size, pygame.font.SysFont("arial", _bar_font_size))
        except Exception:
            draw_game._bar_font_cache = (_bar_font_size, pygame.font.Font(None, _bar_font_size))
    bar_font = draw_game._bar_font_cache[1]
    bar_text_color = (255, 255, 255)

    # Left: current location name
    location_name = rooms.get(current_room, {}).get('name', current_room)
    loc_surf = bar_font.render(location_name, True, bar_text_color)
    loc_y = (bar_height - loc_surf.get_height()) // 2
    screen.blit(loc_surf, (bar_pad, loc_y))

    # Right: Score and Moves
    status_text = f"Score: {game_score}  |  Moves: {game_moves}"
    status_surf = bar_font.render(status_text, True, bar_text_color)
    status_y = (bar_height - status_surf.get_height()) // 2
    screen.blit(status_surf, (w - status_surf.get_width() - bar_pad, status_y))
    
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
    y_start = bar_height + scale(5) + qte_offset
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
    menu_buttons[0].pos = (center_x, scale_y(280))
    menu_buttons[1].pos = (center_x, scale_y(370))
    menu_buttons[2].pos = (center_x, scale_y(460))
    menu_buttons[3].pos = (center_x, scale_y(550))
    
    # "LADEN" Button deaktivieren wenn kein Spielstand vorhanden
    save_exists = os.path.exists(SAVE_FILE)
    menu_buttons[1].disabled = not save_exists
    
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
    MenuButton("NEUES SPIEL", (WIDTH // 2, 300), start_game),
    MenuButton("LADEN", (WIDTH // 2, 390), load_game_from_menu),
    MenuButton("OPTIONEN", (WIDTH // 2, 480), show_options),
    MenuButton("BEENDEN", (WIDTH // 2, 570), quit_game)
]

options_buttons = [
    MenuButton("ZURÜCK", (WIDTH // 2, 550), back_to_menu)
]

# Pause-Menü Buttons (Positionen werden in draw_pause_menu dynamisch aktualisiert)
pause_buttons = [
    MenuButton("FORTSETZEN", (WIDTH // 2, 310), resume_game),
    MenuButton("SPIEL SPEICHERN", (WIDTH // 2, 390), pause_save_game),
    MenuButton("OPTIONEN", (WIDTH // 2, 470), pause_show_options),
    MenuButton("HAUPTMENÜ", (WIDTH // 2, 550), pause_to_main_menu),
    MenuButton("BEENDEN", (WIDTH // 2, 630), quit_game),
]


def draw_pause_menu(current_time):
    """Zeichnet das Pause-Menü mit verdunkeltem Spiel-Hintergrund."""
    global pause_selected_index

    # Spiel als eingefrorenen Hintergrund rendern
    draw_game(current_time)

    # Verdunkelndes Overlay
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Titel
    font_title = get_scaled_font(80)
    title_surf = font_title.render("PAUSIERT", True, BLOOD_RED)
    title_rect = title_surf.get_rect(center=(screen.get_width() // 2, scale_y(150)))
    screen.blit(title_surf, title_rect)

    # Trennlinie
    center_x = screen.get_width() // 2
    line_half = scale(120)
    line_y = scale_y(220)
    _draw_gradient_line(screen, center_x, line_y, line_half, DARK_RED)

    # Button-Positionen für aktuelle Auflösung neu setzen
    pause_buttons[0].pos = (center_x, scale_y(310))
    pause_buttons[1].pos = (center_x, scale_y(390))
    pause_buttons[2].pos = (center_x, scale_y(470))
    pause_buttons[3].pos = (center_x, scale_y(550))
    pause_buttons[4].pos = (center_x, scale_y(630))

    mouse_pos = pygame.mouse.get_pos()
    mouse_over_any = False
    for i, button in enumerate(pause_buttons):
        if button.check_hover(mouse_pos):
            pause_selected_index = i
            mouse_over_any = True

    if not mouse_over_any:
        for i, button in enumerate(pause_buttons):
            button.hovered = (i == pause_selected_index)

    for button in pause_buttons:
        button.draw(screen, current_time)

    # Hinweis-Zeile
    font_hint = get_scaled_font(22)
    hint_pulse = int(60 + 30 * math.sin(current_time * 0.002))
    hint_surf = font_hint.render(
        "ESC: Fortsetzen   |   ↑↓: Navigieren   |   ENTER: Auswählen",
        True, (hint_pulse, hint_pulse, hint_pulse)
    )
    hint_rect = hint_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() - scale(30)))
    screen.blit(hint_surf, hint_rect)


def main():
    global current_state, input_text, scroll_offset, max_scroll, menu_selected_index, cursor_position
    global options_selected_index

    running = True
    start_time = pygame.time.get_ticks()
    
    while running:
        current_time = pygame.time.get_ticks() - start_time
        current_ms = pygame.time.get_ticks()
        
        # Key-Repeat-Logik
        event_handlers.handle_key_repeats(current_ms)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Mausrad: Scrollen (GAME)
            elif event.type == pygame.MOUSEWHEEL:
                if current_state == GAME and prolog_shown:
                    scroll_offset += event.y * 3
                    scroll_offset = max(0, min(scroll_offset, max_scroll))
            
            elif event.type == pygame.KEYDOWN:
                # F11 Fullscreen (global)
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                
                # ESC (global)
                elif event.key == pygame.K_ESCAPE:
                    if current_state == MENU:
                        running = False
                    elif current_state == OPTIONS:
                        current_state = _options_return_state
                        if current_state == MENU:
                            _start_menu_music()
                    elif current_state == GAME:
                        current_state = PAUSED
                    elif current_state == PAUSED:
                        current_state = GAME
                    else:
                        current_state = MENU
                        _start_menu_music()
                
                # State-spezifische Keydown-Handler
                elif event.key == pygame.K_SPACE and current_state == INTRO:
                    current_state = MENU
                    _start_menu_music()
                elif current_state == MENU:
                    event_handlers.handle_keydown_menu(event)
                elif current_state == OPTIONS:
                    event_handlers.handle_keydown_options(event)
                elif current_state == PAUSED:
                    event_handlers.handle_keydown_pause(event)
                elif current_state == GAME:
                    event_handlers.handle_keydown_game(event)
            
            elif event.type == pygame.KEYUP:
                event_handlers.handle_keyup(event)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if current_state == MENU:
                        for button in menu_buttons:
                            button.click()
                    elif current_state == OPTIONS:
                        for button in options_buttons:
                            button.click()
                    elif current_state == PAUSED:
                        for button in pause_buttons:
                            button.click()
        
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
        elif current_state == PAUSED:
            draw_pause_menu(current_time)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
