import pygame
import sys
import math
import random
import time
import datetime

# Pygame initialisieren
pygame.init()

# Konstanten
WIDTH, HEIGHT = 1200, 700
FPS = 60

# Resolution Presets (Name, Breite, Höhe)
RESOLUTION_PRESETS = [
    ('Sehr Niedrig', 800, 450),
    ('Niedrig', 1024, 576),
    ('Mittel', 1280, 720),
    ('Hoch', 1600, 900),
    ('Sehr Hoch', 1920, 1080)
]
current_resolution_index = 2  # Standard: Mittel (1280x720)
#jannik
# Farben
BLACK = (0, 0, 0)
BLOOD_RED = (139, 0, 0)
DARK_RED = (100, 0, 0)
GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)
DARK_GRAY = (30, 30, 30)
HOVER_RED = (180, 0, 0)
GREEN = (0, 255, 0)
TERMINAL_GREEN = (0, 200, 0)
TERMINAL_BG = (10, 10, 10)

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
current_state = INTRO

# Menü-Navigation
menu_selected_index = 0

# Game Settings
game_settings = {
    'music_volume': 0.5,
    'sfx_volume': 0.7,
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

#
bibliothek_4_schrank_geschoben = False


# Key-Repeat für Cursor-Tasten
delete_held = False
last_delete_time = 0
left_held = False
last_left_time = 0
right_held = False
last_right_time = 0
key_initial_delay = 250  # ms
key_repeat_delay = 35    # ms

# Scroll-System
scroll_offset = 0
max_scroll = 0

# Kampfsystem

player_stats = {   
    'health': 100,
    'equipped_weapon': None,
    'weapon_type': None,  # 'ranged', 'melee', None
    'in_combat': False,
    'fist_level': 1       # Fäuste Level (1-5), Level-Up durch Black Flash
}
#
def spawn_chance():
    if random.random() < 0.5:
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
    'baseball_schläger': {'name': 'Baseball Schläger', 'type': 'melee', 'damage': [25, 35], 'crit_chance': 0.25},
    'axt': {'name': 'Axt', 'type': 'melee', 'damage': [35, 50], 'crit_chance': 0.3},
    'machete': {'name': 'Machete', 'type': 'melee', 'damage': [30, 45], 'crit_chance': 0.35},
}

# Gegner-Datenbank
enemies = {
    'zombie': {'name': 'Toxoplasma-Zombie', 'health': 100, 'max_health': 100, 'damage': [10, 20], 'distance': 'nah'},
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
        'items': [],
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
        'description': 'Im lagerraum dirnnen stehen 3 Schwerlastregale mit weiterem dosen essen und wasser, ein bett steht in der rechten ecke. Im norden gehts in den keller',
        'exits': {'norden': 'keller'},
        'items': [],
        'in_development': False
    },
    'suedlich_haus': {#Stadt
        'name': 'Südliche Straße',
        'description': 'Du stehst mitten in der Straße, komplett leergeräumt, nur Kaputte Autos so wie getrocknetes Blut. Im WESTEN geht es weiter. Im SÜDEN steht Haus 1. Im OSTEN geht es weiter. NORDEN führt zurück zu deinem Versteck.',
        'exits': {'norden': 'vordertuer', 'westen': 'westlich_haus_gabelung', 'süden': 'haus1', 'osten': 'oestlich_weggabelung'},
        'items': [],
        'in_development': False,
        'spawn_chance': True
    },
    'westlich_haus_gabelung': {#Stadt
        'name': 'Westliche weggabelung',
        'description': 'Du stehst an einer Weggabelung, richtung Süden gehts zum Krankenhaus und nach Norden sieht man nur noch ne weitere weggabelung.',
        'exits': {'osten': 'suedlich_haus', 'norden': 'nord_westliche_weggabelung', 'süden': 'krankenhaus_straße'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_straße': {#Krankenhaus
        'name': 'Krankenhaus Straße',
        'description': 'Du stehst in mitten der straße, westlich von dir steht das Krankenhauses.',
        'exits': {'norden': 'westlich_haus_gabelung', 'westen': 'krankenhaus_eingang'},
        'items': [],
        'in_development': False
    },
    'krankenhaus_eingang': {#Krankenhaus
        'name': 'Krankenhaus Eingang',
        'description': 'Vor dir sind kaputte glastüren, von inneren des Krankenhauses hörst du Zombies schreien. Richtung westen gelangst du zurück auf die Straße',
        'exits': {'osten': 'krankenhaus_straße'},
        'items': [],
        'in_development': False
    },
    'östliche_straße': {#stadt
        'name': 'Östliche Straße',
        'description': 'Du stehst auf der Straße, weitere kaputte Autos und blut sind auf der Straße sehbar. Im Osten liegt ein Haus, ',
        'exits': {'norden': 'nord_westliche_weggabelung', 'osten': 'haus2', 'süden': 'oestlich_weggabelung'},
        'items': [],
        'in_development': False
    },
    'nord_westliche_weggabelung': {#Stadt Norden
        'name': 'Nord Westliche weggabelung',
        'description': 'Du befindest dich an einer weggabelung, im westen liegt die Bibliothek Straße, richtung osten befinden sich weitere häuser',
        'exits': {'osten': 'östliche_straße', 'westen': 'bibliothek_straße'},
        'items': [],
        'in_development': False
    },
    'bibliothek_straße': {#Bibliothek
        'name': 'Bibliothek Straße',
        'description': 'Du stehst auf der Straße, weitere kaputte Autos und blut sind auf der Straße sehbar. Im Osten liegt ein Haus, ',
        'exits': {'norden': 'bibliothek_eingang', 'osten': 'nord_westliche_weggabelung'},
        'items': [],
        'in_development': False
    },
    'bibliothek_eingang': {#Bibliothek
        'name': 'Bibliothek Eingang',
        'description': 'Du stehst vor den Türen der Bibliothek, knarzen ist von drausen zuhören. Im Osten liegt ein Haus, ',
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
        'items': [],
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
        'name': 'Nord Östliche weggabelung',
        'description': 'Im mitten von der weggabelung siehst du den Parkplatz von Walmart und ein weiteres Haus im Norden',
        'exits': {'norden': 'norden_straße', 'westen': 'nord-westliche weggabelung', 'süden': 'östliche_straße', 'osten': 'parkplatz'},
        'items': [],
        'in_development': False
    },
    'parkplatz': {#Walmart
        'name': 'Parkplatz',
        'description': 'Du stehst auf dem Parkplatz von Walmart, es stehen viele kaputte autos, manche davon auch umgekippt. Richtung westen  und im süden gehst zur weggabelung zurück',
        'exits': {'westen': 'norden_straße', 'süden': 'nord_östliche_weggabelung', 'norden': 'walmart_eingang'},
        'items': [],
        'in_development': False
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
        'items': [],
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
        'description': 'Im westen von dir ist ein Haus, die Türen stehen offen, im osten liegt der Parkplatz von Walmart. Im Süden gehsts zurück zur weggabelung.',
        'exits': {'westen': 'haus_3_eingang', 'süden': 'nord_östliche_weggabelung', 'osten': 'parkplatz'},
        'items': [],
        'in_development': True
    },
    'haus_3': {#Haus3
        'name': 'haus_3',
        'description': 'Im westen von dir ist ein Haus, die Türen stehen offen, im osten liegt der Parkplatz von Walmart. Im Süden gehsts zurück zur weggabelung.',
        'exits': {'westen': 'haus_3_eingang', 'süden': 'nord_östliche_weggabelung', 'osten': 'parkplatz'},
        'items': [],
        'in_development': True
    },
    'oestlich_weggabelung': {#Stadt
        'name': 'Östliche weggabelung',
        'description': 'Du stehst auf der Straße, weitere kaputte Autos und blut sind auf der Straße sehbar. Im Osten liegt ein Park, ',
        'exits': {'norden': 'nord_östliche_weggabelung',
        'osten': 'park', 'süden': 'skyscraper_weggabelung'},
        'items': [],
        'in_development': True
    },
    'park_straße': {#Stadt
        'name': 'Park Straße',
        'description': 'Du stehst auf der Straße, weitere kaputte Autos und blut sind auf der Straße sehbar. Im Osten liegt ein Park, ',
        'exits': {'norden': 'oestlich weggabelung', 'osten': 'park', 'süden': 'skyscraper_weggabelung'},
        'items': [],
        'in_development': True
    },
    'skyscraper_weggabelung': {#Stadt
        'name': 'Skyscraper Weggabelung',
        'description': 'Du stehst an einer weggabelung, nach norden siehst du die Parkstraße, nach Süden siehst ein Hochhaus. Nach WESTEN ist Straße Pizzeria.',
        'exits': {'norden': 'park_straße', 'osten': 'straße_pizzeria', 'süden': 'weggabelung_skyscraper2'},
        'items': [],
        'in_development': True
    },
    'weggabelung_skyscraper2': {#Stadt
        'name': 'Weggabelung Skyscraper 2',
        'description': 'Du stehst an einer weggabelung, nach norden siehst du die Skyscraperweggabelung. Nach westen ist Home Depot Straße Ost',
        'exits': {'norden': 'skyscraper_weggabelung','osten': 'home_depot_straße_ost'},
        'items': [],
        'in_development': True
    },
    'noerdlich_haus': {#Stadt
        'name': 'Nördlich vom Versteck',
        'description': 'Du stehst nördlich von deinem Versteck. Der Garten ist überwuchert. Nach SÜDEN kannst du zur Westseite, nach OSTEN zur Ostseite.',
        'exits': {'süden': 'westlich_haus_gabelung', 'osten': 'oestlich_weggabelung'},
        'items': [],
        'in_development': True
    },
    'haus1': {#Haus1
        'name': 'Haus 1',
        'description': 'Du stehst vor der Haustür vom Haus doch sie lässt sich nicht öffnen.',
        'exits': {'norden': 'suedlich_haus'},
        'items': [],
        'in_development': True
    },     
}

def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

def draw_cracked_text(surface, text, pos, color, time, font=None):
    """Zeichnet Text mit Rissen und Verzerrung"""
    # Standard-Font mit Skalierung wenn keiner angegeben
    if font is None:
        font = get_scaled_font(120)
    
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=pos)
    
    # Skaliertes Schütteln
    shake_x = math.sin(time * 0.05) * scale(3)
    shake_y = math.cos(time * 0.07) * scale(2)
    
    # Skalierter Schatten
    shadow_range = max(3, scale(5))
    for i in range(shadow_range, 0, -1):
        shadow = font.render(text, True, DARK_RED)
        shadow_offset = scale(2)
        shadow_rect = shadow.get_rect(center=(pos[0] + i*shadow_offset + shake_x, pos[1] + i*shadow_offset + shake_y))
        surface.blit(shadow, shadow_rect)
    
    final_rect = text_rect.move(shake_x, shake_y)
    surface.blit(text_surface, final_rect)

def draw_particles(surface, time, alpha):
    """Zeichnet fallende Partikel (Asche/Staub)"""
    for i in range(50):
        x = (i * 137 + time * 2) % surface.get_width()
        y = (i * 79 + time * 3) % surface.get_height()
        size = (i % 3) + 1
        particle_alpha = min(255, alpha)
        color = (*LIGHT_GRAY, particle_alpha)
        
        particle_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        particle_surface.fill(color)
        surface.blit(particle_surface, (x, y))

def draw_cracks(surface, alpha):
    """Zeichnet Risse im Hintergrund"""
    crack_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    
    for i in range(8):
        start_x = i * 150 + 50
        points = [(start_x, 0)]
        
        y = 0
        while y < surface.get_height():
            offset = math.sin(y * 0.02 + i) * 20
            points.append((start_x + offset, y))
            y += 50
        
        if len(points) > 1:
            pygame.draw.lines(crack_surface, (*GRAY, alpha), False, points, 2)
    
    surface.blit(crack_surface, (0, 0))

def draw_intro(current_time):
    """Zeichnet das Intro"""
    FADE_IN_DURATION = 2000
    HOLD_DURATION = 3000
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
    
    crack_alpha = min(alpha, 100)
    draw_cracks(screen, crack_alpha)
    
    draw_particles(screen, current_time, alpha // 2)
    
    # Skalierte Titel-Schrift
    intro_font = get_scaled_font(120)
    
    text_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    draw_cracked_text(text_surface, "DEAD WORLD", 
                     (screen.get_width() // 2, screen.get_height() // 2), 
                     (BLOOD_RED[0], BLOOD_RED[1], BLOOD_RED[2]), 
                     current_time,
                     intro_font)
    
    text_surface.set_alpha(alpha)
    screen.blit(text_surface, (0, 0))
    
    return False

class MenuButton:
    def __init__(self, text, pos, action):
        self.text = text
        self.pos = pos
        self.action = action
        self.hovered = False
        self.rect = None
    
    def draw(self, surface, current_time):
        color = HOVER_RED if self.hovered else BLOOD_RED
        
        # Skalierte Schrift für Buttons
        button_font = get_scaled_font(50)
        
        text_surf = button_font.render(self.text, True, color)
        self.rect = text_surf.get_rect(center=self.pos)
        
        # Skalierter Schatten
        shadow_offset = max(1, scale(3))
        for i in range(shadow_offset, 0, -1):
            shadow = button_font.render(self.text, True, DARK_RED)
            shadow_rect = shadow.get_rect(center=(self.pos[0] + i, self.pos[1] + i))
            surface.blit(shadow, shadow_rect)
        
        if self.hovered:
            shake = math.sin(current_time * 0.01) * scale(2)
            final_rect = self.rect.move(shake, 0)
        else:
            final_rect = self.rect
        
        surface.blit(text_surf, final_rect)
        
        if self.hovered:
            border_rect = self.rect.inflate(scale(20), scale(10))
            pygame.draw.rect(surface, BLOOD_RED, border_rect, 2)
    
    def check_hover(self, mouse_pos):
        if self.rect:
            self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered
    
    def click(self):
        if self.hovered and self.action:
            self.action()

def start_game():
    global current_state, game_history, current_room, player_inventory, prolog_shown, prolog_lines, prolog_line_index
    current_state = GAME
    game_history = []
    current_room = 'start'
    player_inventory = ['fäuste']
    prolog_shown = False
    prolog_line_index = 0
    
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
    """Fügt Text zur Spielhistorie hinzu mit automatischem Word-Wrapping"""
    global scroll_offset
    
    max_chars = get_max_chars()
    
    #
    
    # Leere Zeilen direkt hinzufügen
    if not text or text.strip() == "":
        game_history.append(text)
    else:
        # Text mit Word-Wrapping aufteilen
        wrapped_lines = wrap_text(text, max_chars)
        for line in wrapped_lines:
            game_history.append(line)
    
    # Automatisch nach unten scrollen bei neuen Nachrichten
    scroll_offset = 0

def move_direction(direction):
    """Bewege Spieler in eine Richtung"""
    global current_room
    
    room = rooms[current_room]
    if room.get('spawn_chance') and spawn_chance():
        print("Ein Zombie taucht auf!")
    
    if direction in room['exits']:
        next_room = room['exits'][direction]
        
        # Spezialfall: Bücherregal blockiert bibliothek_4
        if current_room == 'bibliothek_3' and next_room == 'bibliothek_4' and not bibliothek_4_schrank_geschoben:
            add_to_history("Ein großes Bücherregal versperrt den Weg nach NORDEN.")
            add_to_history("Vielleicht kannst du es zur Seite schieben?")
            add_to_history("")
            return
        
        #
        
                
        # Spezialfall: Zeitsprung wenn man zum Spawn geht
        if next_room == 'spawn' and current_room == 'tunnel':
            trigger_two_year_timeskip()
            return
        
        current_room = next_room
        add_to_history(f"Du gehst nach {direction.upper()}...")
        add_to_history("")
        describe_room()
    else:
        add_to_history("Du kannst nicht in diese Richtung gehen.")
        add_to_history("")

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
    
    add_to_history("")
    describe_room()

def describe_room():
    """Beschreibt den aktuellen Raum"""
    room = rooms[current_room]
    
    # Erste Begegnung mit Zombie im Startroom
    if current_room == 'start' and room.get('first_visit'):
        add_to_history("")
        add_to_history("Der Zombie taumelt auf dich zu!")
        add_to_history("Tentakel zucken aus seinem Mund.")
        add_to_history("")
        room['first_visit'] = False
        return
    
    add_to_history(f"> {room['name']}")
    add_to_history(room['description'])
    if room['items']:
        add_to_history(f"Du siehst: {', '.join(room['items'])}")
    
    if current_room == 'wohnbereich' and room.get('zombie_spawn'):
        # Neuer Zombie im Wohnbereich - Health zurücksetzen
        enemies['zombie']['health'] = enemies['zombie']['max_health']
        add_to_history("")
        add_to_history("Der Zombie taumelt auf dich zu!")
        add_to_history("Tentakel zucken aus seinem Mund.")
        add_to_history("")
        room['zombie_spawn'] = False
        return
    
    if current_room == 'walmart_5' and room.get('zombie_spawn'):
        # Neuer Zombie im Wohnbereich - Health zurücksetzen
        enemies['zombie']['health'] = enemies['zombie']['max_health']
        add_to_history("")
        add_to_history("Der Zombie taumelt auf dich zu!")
        add_to_history("Tentakel zucken aus seinem Mund.")
        add_to_history("")
        room['zombie_spawn'] = False
        return

    if current_room == 'walmart_9' and room.get('zombie_spawn'):
        # Neuer Zombie im Wohnbereich - Health zurücksetzen
        enemies['zombie']['health'] = enemies['zombie']['max_health']
        add_to_history("")
        add_to_history("Der Zombie taumelt auf dich zu!")
        add_to_history("Tentakel zucken aus seinem Mund.")
        add_to_history("")
        room['zombie_spawn'] = False
        return
    # Gegner im Raum?
    if room.get('enemy'):
        enemy_key = room['enemy']
        enemy = enemies.get(enemy_key)
        if enemy and enemy['health'] > 0:
            add_to_history(f">>> {enemy['name']} ist hier! <<<")
            add_to_history(f"HP: {enemy['health']}/{enemy['max_health']}")
            player_stats['in_combat'] = True
    
    add_to_history("")



def process_command(command):
    """Verarbeitet Spielerbefehle"""
    global current_room, prolog_shown, prolog_line_index, qte_active, qte_input, command_history, history_index
    
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
        add_to_history("  status - Charakter-Status anzeigen")
        add_to_history("  echo [text] - Text ausgeben")
        add_to_history("  time - Aktuelle Zeit anzeigen")
        add_to_history("  whoami - Charakter-Info")
        add_to_history("")
        add_to_history("System:")
        add_to_history("  neu - Neustart nach Tod")
        add_to_history("")
    
    elif cmd.startswith('gehe '):
        direction = cmd[5:].strip()
        room = rooms[current_room]
        if direction in room['exits']:
            current_room = room['exits'][direction]
            add_to_history(f"Du gehst nach {direction.upper()}...")
            add_to_history("")
            describe_room()
        else:
            add_to_history("Du kannst nicht in diese Richtung gehen.")
            add_to_history("")
    
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
    
    elif cmd.startswith('nimm '):
        item = cmd[5:].strip()
        room = rooms[current_room]
        if item in room['items']:
            room['items'].remove(item)
            player_inventory.append(item)
            add_to_history(f"Du nimmst {item}.")
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
            add_to_history(f"Items: {', '.join(player_inventory)}")
        else:
            add_to_history("Items: Leer")
        
        if player_stats['equipped_weapon']:
            weapon = weapons[player_stats['equipped_weapon']]
            add_to_history(f"Waffe: {weapon['name']} ({weapon['type']})")
            
            if weapon['type'] == 'ranged':
                add_to_history(f"Munition: {weapon.get('ammo', 0)}")
            else:
                min_dmg, max_dmg = weapon['damage']
                add_to_history(f"Schaden: {min_dmg}-{max_dmg}")
        else:
            add_to_history("Waffe: Keine")
        
        # Fäuste Level anzeigen
        fist_level = player_stats['fist_level']
        fist_bonus = FIST_LEVEL_BONUSES[fist_level]
        min_dmg, max_dmg = fist_bonus['damage']
        black_flash_percent = round(weapons['fäuste'].get('black_flash', 0) * 100, 1)
            
        add_to_history("")
        add_to_history(f"=== FÄUSTE (Level {fist_level}/5) ===")
        add_to_history(f"Schaden: {min_dmg}-{max_dmg}")
        add_to_history(f"Black Flash: {black_flash_percent}%")
            
        if fist_level < 5:
            add_to_history("(Level-Up durch Black Flash!)")
        else:
            add_to_history(">>> MAX LEVEL! <<<")
            
        add_to_history("")
            
        # Health Bar
        hp_percent = player_stats['health'] / 100.0
        bar_length = 20
        filled = int(hp_percent * bar_length)
        hp_bar = '█' * filled + '░' * (bar_length - filled)
            
        add_to_history(f"HP: [{hp_bar}] {player_stats['health']}/100")
        add_to_history("")
        
    elif cmd in ['schaue', 'look', 'l']:
        describe_room()
    
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
                add_to_history("Tippe 'neu' um neu zu starten")
                player_stats['health'] = 0
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
                attack_with_weapon(target, weapon_name)
            else:
                add_to_history("Falsches Format. Nutze: schlag [ziel] mit [waffe]")
                add_to_history("")
        else:
            target = cmd.split(' ', 1)[1].strip()
            unarmed_attack(target)
    
    elif cmd == 'clear' or cmd == 'cls':
        game_history.clear()
        add_to_history("Terminal geleert.")
        add_to_history("")
    
    elif cmd == 'status' or cmd == 'stats':
        add_to_history("CHARAKTER STATUS")
        add_to_history("")
        add_to_history("Name: Albert Wesker Cristal")
        add_to_history(f"HP: {player_stats['health']}")
        add_to_history(f"Raum: {rooms[current_room]['name']}")
        
        if player_stats['in_combat']:
            add_to_history("Status: IM KAMPF")
        else:
            add_to_history("Status: Sicher")
        add_to_history("")
    
    elif cmd.startswith('stich auf '):
        target = cmd[10:].strip()
        melee_attack(target)
    
    # Terminal-Befehle
    elif cmd == 'neu':
        # Neues Spiel starten - setzt alles zurück
        # Reset Player Stats
        player_stats['health'] = 100
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
    
    elif cmd in ['schieben', 'schieb', 'regal schieben', 'schrank schieben', 'bücherregal schieben']:
        global bibliothek_4_schrank_geschoben
        if current_room == 'bibliothek_3':
            if not bibliothek_4_schrank_geschoben:
                bibliothek_4_schrank_geschoben = True
                add_to_history("Du stemmst dich gegen das schwere Bücherregal...")
                add_to_history("Mit aller Kraft schiebst du es zur Seite!")
                add_to_history("Der Weg nach NORDEN ist jetzt frei.")
                add_to_history("")
            else:
                add_to_history("Das Bücherregal wurde bereits zur Seite geschoben.")
                add_to_history("")
        else:
            add_to_history("Hier gibt es nichts zum Schieben.")
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
        add_to_history(f"TREFFER! {damage} Schaden!")
        add_to_history(f"{enemy['name']} HP: {enemy['health']}/{enemy['max_health']}")
        
        if enemy['health'] <= 0:
            add_to_history(f"Der {enemy['name']} bricht zusammen!")
            room['enemy'] = None
            player_stats['in_combat'] = False
        else:
            # Gegner-Gegenangriff
            enemy_counterattack(enemy)
    else:
        add_to_history("VERFEHLT! Der Schuss geht daneben.")
        # Gegner-Gegenangriff
        enemy_counterattack(enemy)
    
    add_to_history(f"Munition: {weapon['ammo']}")
    add_to_history("")

def enemy_counterattack(enemy):
    """Gegner greift zurück an"""
    min_dmg, max_dmg = enemy['damage']
    damage = random.randint(min_dmg, max_dmg)
    
    player_stats['health'] -= damage
    add_to_history(f"{enemy['name']} greift an! -{damage} HP")
    add_to_history(f"Deine HP: {player_stats['health']}/100")
    
    if player_stats['health'] <= 0:
        add_to_history("")
        add_to_history("=== DU BIST GESTORBEN ===")
        add_to_history("Tippe 'neu' um neu zu starten")

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
    new_bonus = FIST_LEVEL_BONUSES[new_level]
    min_dmg, max_dmg = new_bonus['damage']
    
    add_to_history("")
    add_to_history("=================================")
    add_to_history(f">>> FÄUSTE LEVEL UP! Level {new_level} <<<")
    add_to_history(f"Neuer Schaden: {min_dmg}-{max_dmg}")
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
        add_to_history(f"Treffer! {damage} Schaden!")
        add_to_history(f"{enemy['name']} HP: {enemy['health']}/{enemy['max_health']}")
        
        # Level-Up bei Black Flash (statt XP-System)
        if is_fists and got_black_flash:
            level_up_fists()
        
        if enemy['health'] <= 0:
            add_to_history("")
            add_to_history("Der Zombie zuckt ein letztes Mal.")
            add_to_history("Schwarze Flüssigkeit sickert aus dem zerschmetterten Schädel.")
            add_to_history("")
            add_to_history("=== SIEG ===")
            add_to_history("")
            
            # Gegner besiegt - entferne aus Raum
            room['enemy'] = None
            player_stats['in_combat'] = False
            
            # Raumspezifische Belohnungen
            if current_room == 'start':
                room['exits']['norden'] = 'corridor'
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
            add_to_history(f"{enemy['name']} krallt sich in deine Schulter! -{damage} HP")
            add_to_history(f"Deine HP: {player_stats['health']}/100")
            
            if player_stats['health'] <= 0:
                add_to_history("")
                add_to_history("=== DU BIST GESTORBEN ===")
                add_to_history("Tippe 'neu' um neu zu starten")
    else:
        add_to_history("Du verfehlst!")
        min_dmg, max_dmg = enemy['damage']
        damage = random.randint(min_dmg, max_dmg)
        player_stats['health'] -= damage
        add_to_history(f"Der Zombie beißt zu! -{damage} HP")
        add_to_history(f"Deine HP: {player_stats['health']}/100")
        
        if player_stats['health'] <= 0:
            add_to_history("")
            add_to_history("=== DU BIST GESTORBEN ===")
            add_to_history("Tippe 'neu' um neu zu starten")
    
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
        add_to_history(f"Getroffen! -{damage} HP")
        add_to_history(f"Deine HP: {player_stats['health']}/100")
        
        if player_stats['health'] <= 0:
            add_to_history("")
            add_to_history("=== DU BIST GESTORBEN ===")
            add_to_history("Tippe 'neu' um neu zu starten")
    
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
    """Zeichnet das Text-Adventure Terminal"""
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
        header_color = (255, 0, 0)  # Rot für QTE
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
    
    # Separator
    pygame.draw.line(screen, TERMINAL_GREEN, (padding, separator_y), (screen.get_width() - padding, separator_y), 2)
    
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
        pygame.draw.line(screen, TERMINAL_GREEN, (padding, input_y - scale(10)), (screen.get_width() - padding, input_y - scale(10)), 2)
        
        # Text vor und nach dem Cursor
        text_before_cursor = input_text[:cursor_position]
        text_after_cursor = input_text[cursor_position:]
        
        # Blinkender Cursor
        if (current_time // 500) % 2 == 0:
            cursor_char = "|"
        else:
            cursor_char = " "
        
        prompt = f"> {text_before_cursor}{cursor_char}{text_after_cursor}"
        
        input_surf = font_text.render(prompt, True, TERMINAL_GREEN)
        screen.blit(input_surf, (text_padding, input_y))
        
        # History-Hinweis anzeigen wenn History vorhanden
        if command_history and history_index != -1:
            hint_text = f"[History: {history_index + 1}/{len(command_history)}]"
            hint_surf = font_hint.render(hint_text, True, GRAY)
            screen.blit(hint_surf, (screen.get_width() - scale(200), input_y + scale(35)))
    
    elif not prolog_shown and not qte_active:
        # Prolog-Hinweis
        hint_y = screen.get_height() - scale(40)
        hint_surf = font_text.render("[Drücke ENTER um fortzufahren]", True, TERMINAL_GREEN)
        hint_rect = hint_surf.get_rect(center=(screen.get_width() // 2, hint_y))
        screen.blit(hint_surf, hint_rect)


def draw_options(current_time):
    """Zeichnet das Options-Menü"""
    screen.fill(BLACK)
    draw_cracks(screen, 50)
    draw_particles(screen, current_time, 100)
    
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
    
    # === AUFLÖSUNG ===
    res_label = font_option.render("Auflösung:", True, LIGHT_GRAY)
    res_label_rect = res_label.get_rect(center=(center_x, y))
    screen.blit(res_label, res_label_rect)
    
    y += spacing
    
    # Pfeile und aktuelle Auflösung
    arrow_color = TERMINAL_GREEN if not fullscreen else GRAY
    res_name = get_current_resolution_name()
    arrow_offset = scale(220)
    
    # Linker Pfeil
    left_arrow = font_option.render("<", True, arrow_color if current_resolution_index > 0 else GRAY)
    left_rect = left_arrow.get_rect(center=(center_x - arrow_offset, y))
    screen.blit(left_arrow, left_rect)
    
    # Auflösungstext
    res_text = font_option.render(res_name, True, TERMINAL_GREEN)
    res_rect = res_text.get_rect(center=(center_x, y))
    screen.blit(res_text, res_rect)
    
    # Rechter Pfeil
    right_arrow = font_option.render(">", True, arrow_color if current_resolution_index < len(RESOLUTION_PRESETS) - 1 else GRAY)
    right_rect = right_arrow.get_rect(center=(center_x + arrow_offset, y))
    screen.blit(right_arrow, right_rect)
    
    # Fullscreen-Warnung
    if fullscreen:
        warn_text = font_small_hint.render("(Deaktiviere Fullscreen mit F11 um Auflösung zu ändern)", True, HOVER_RED)
        warn_rect = warn_text.get_rect(center=(center_x, y + scale(35)))
        screen.blit(warn_text, warn_rect)
    
    # === MUSIK ===
    y += scale(80)
    music_text = f"Musik: {int(game_settings['music_volume'] * 100)}%"
    music_surf = font_option.render(music_text, True, LIGHT_GRAY)
    music_rect = music_surf.get_rect(center=(center_x, y))
    screen.blit(music_surf, music_rect)
    
    # === SFX ===
    y += scale(60)
    sfx_text = f"Effekte: {int(game_settings['sfx_volume'] * 100)}%"
    sfx_surf = font_option.render(sfx_text, True, LIGHT_GRAY)
    sfx_rect = sfx_surf.get_rect(center=(center_x, y))
    screen.blit(sfx_surf, sfx_rect)
    
    # === SCHWIERIGKEIT ===
    y += scale(60)
    diff_text = f"Schwierigkeit: {game_settings['difficulty']}"
    diff_surf = font_option.render(diff_text, True, LIGHT_GRAY)
    diff_rect = diff_surf.get_rect(center=(center_x, y))
    screen.blit(diff_surf, diff_rect)
    
    # Zurück-Button (Position anpassen)
    options_buttons[0].pos = (center_x, screen.get_height() - scale(100))
    
    mouse_pos = pygame.mouse.get_pos()
    for button in options_buttons:
        button.check_hover(mouse_pos)
        button.draw(screen, current_time)
    
    # Hinweise
    hints = [
        "← / → : Auflösung ändern",
        "F11: Vollbild umschalten"
    ]
    hint_y = screen.get_height() - scale(50)
    for hint in hints:
        hint_surf = font_small_hint.render(hint, True, GRAY)
        hint_rect = hint_surf.get_rect(center=(center_x, hint_y))
        screen.blit(hint_surf, hint_rect)
        hint_y += scale(20)

def draw_menu(current_time):
    """Zeichnet das Hauptmenü"""
    global menu_selected_index
    
    screen.fill(BLACK)
    
    draw_cracks(screen, 50)
    draw_particles(screen, current_time, 100)
    
    # Skalierte Schriften
    font_menu_title = get_scaled_font(80)
    font_menu_hint = get_scaled_font(25)
    
    title_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    draw_cracked_text(title_surface, "DEAD WORLD", 
                     (screen.get_width() // 2, scale_y(150)), 
                     (BLOOD_RED[0], BLOOD_RED[1], BLOOD_RED[2]), 
                     current_time,
                     font_menu_title)
    screen.blit(title_surface, (0, 0))
    
    # Aktualisiere Button-Positionen basierend auf aktueller Auflösung
    center_x = screen.get_width() // 2
    menu_buttons[0].pos = (center_x, scale_y(350))
    menu_buttons[1].pos = (center_x, scale_y(450))
    menu_buttons[2].pos = (center_x, scale_y(550))
    
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
    
    # Hinweis für Tastatursteuerung
    hint_surf = font_menu_hint.render("↑↓: Navigieren  |  ENTER: Auswählen", True, GRAY)
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
    global current_state, input_text, backspace_held, last_backspace_time, history_index, scroll_offset, max_scroll, menu_selected_index, cursor_position
    global delete_held, last_delete_time, left_held, last_left_time, right_held, last_right_time
    
    running = True
    start_time = pygame.time.get_ticks()
    
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
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Mausrad für Scrollen
            if event.type == pygame.MOUSEWHEEL and current_state == GAME and prolog_shown:
                scroll_offset += event.y * 3  # Invertiert: nach oben scrollen = höherer offset
                # Begrenze Scroll
                scroll_offset = max(0, min(scroll_offset, max_scroll))
            
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
                    elif current_state == GAME:
                        current_state = MENU
                    else:
                        current_state = MENU
                
                # Space im Intro
                elif event.key == pygame.K_SPACE and current_state == INTRO:
                    current_state = MENU
                
                # Tastaturnavigation im Hauptmenü
                elif current_state == MENU:
                    if event.key == pygame.K_UP:
                        menu_selected_index = (menu_selected_index - 1) % len(menu_buttons)
                    elif event.key == pygame.K_DOWN:
                        menu_selected_index = (menu_selected_index + 1) % len(menu_buttons)
                    elif event.key == pygame.K_RETURN:
                        menu_buttons[menu_selected_index].action()
                
                # Pfeiltasten im Options-Menü für Auflösung
                elif current_state == OPTIONS:
                    if event.key == pygame.K_LEFT:
                        change_resolution(-1)
                    elif event.key == pygame.K_RIGHT:
                        change_resolution(1)
                
                # Text-Eingabe im Spiel
                elif current_state == GAME:
                    if event.key == pygame.K_RETURN:
                        if not prolog_shown:
                            # Im Prolog: Enter zeigt mehr Text
                            process_command("")
                        elif input_text.strip():
                            # Im Spiel: verarbeite Befehl
                            add_to_history(f"> {input_text}")
                            process_command(input_text)
                            input_text = ""
                            cursor_position = 0
                            history_index = -1
                    
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
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if current_state == MENU:
                        for button in menu_buttons:
                            button.click()
                    elif current_state == OPTIONS:
                        for button in options_buttons:
                            button.click()
        
        # State-basiertes Rendering
        if current_state == INTRO:
            intro_done = draw_intro(current_time)
            if intro_done:
                current_state = MENU
                start_time = pygame.time.get_ticks()
        
        elif current_state == MENU:
            draw_menu(current_time)
        
        elif current_state == OPTIONS:
            draw_options(current_time)
        
        elif current_state == GAME:
            draw_game(current_time)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
