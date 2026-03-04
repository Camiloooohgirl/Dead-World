# ============================================================
# command_handlers.py — Extracted Command Handlers for Dead World
# ============================================================
# Each handler function returns True if it handled the command,
# False otherwise. The main process_command() uses these as a
# dispatcher chain.
#
# IMPORTANT: This module must NOT import from the main game file
# at module level. Instead, it receives references at init time.

import random
import datetime
import pygame
from config import *


# ========================
# MODULE STATE — set via init_handlers()
# ========================
_game = None  # Reference to main game module (set at runtime)


def init_handlers(game_module):
    """Call once at startup. Pass the main game module so handlers can
    access add_to_history, rooms, player_inventory, player_stats, etc."""
    global _game
    _game = game_module


# ========================
# HELPER — shorter alias
# ========================
def _h(text):
    """Shorthand for add_to_history."""
    _game.add_to_history(text)


# ========================
# HELP
# ========================
def handle_help(cmd):
    if cmd not in ('hilfe', 'help', '?'):
        return False

    _h("DEAD WORLD - BEFEHLE")
    _h("")
    _h("Bewegung:")
    _h("  n, norden - Gehe nach Norden")
    _h("  o, osten - Gehe nach Osten")
    _h("  s, süden - Gehe nach Süden")
    _h("  w, westen - Gehe nach Westen")
    _h("  r, runter - Gehe nach Unten")
    _h("  h, hoch - Gehe nach Oben")
    _h("  gehe [richtung] - Alternative Schreibweise")
    _h("  schaue, look - Raum beschreiben")
    _h("")
    _h("Gegenstände:")
    _h("  nimm [item] - Item aufheben")
    _h("  lese [item] - Item lesen (Zeitung, Notizen)")
    _h("  esse [item] - Essen/Trinken konsumieren")
    _h("  inventar, inv - Inventar anzeigen")
    _h("")
    _h("Kampf:")
    _h("  ausrüsten [waffe] - Waffe ausrüsten")
    _h("  schlag [ziel] - Nahkampf")
    _h("  stich auf [ziel] - Mit Messer angreifen")
    _h("  schieße auf [ziel] - Schusswaffe nutzen")
    _h("")
    _h("Terminal:")
    _h("  clear, cls - Terminal leeren")
    _h("  echo [text] - Text ausgeben")
    _h("  time - Aktuelle Zeit anzeigen")
    _h("  whoami - Charakter-Info")
    _h("  karte, map - Weltkarte anzeigen")
    _h("")
    _h("System:")
    _h("  save, speichern - Spiel speichern")
    _h("  restore, laden - Spiel laden")
    _h("  score, punkte - Punkte anzeigen")
    _h("  zeit - Spielzeit anzeigen")
    _h("  diagnose, d - Gesundheits- und Zustandsbericht")
    _h("  info - Spielinfo")
    _h("  q, quit - Beenden")
    _h("  verbose/brief/superbrief - Beschreibungsmodus")
    _h("  neu - Neustart nach Tod")
    _h("")
    _h("Behälter:")
    _h("  öffne/schließe [behälter]")
    _h("  lege [item] in [behälter]")
    _h("  nimm [item] aus [behälter]")
    _h("  schaue in [behälter]")
    _h("")
    return True


# ========================
# MOVEMENT
# ========================
# Direction alias map
_DIRECTION_MAP = {
    'n': 'norden', 'norden': 'norden', 'nord': 'norden',
    'o': 'osten', 'osten': 'osten', 'ost': 'osten',
    's': 'süden', 'süden': 'süden', 'süd': 'süden', 'sued': 'süden',
    'w': 'westen', 'westen': 'westen', 'west': 'westen',
    'so': 'südosten', 'südosten': 'südosten', 'suedosten': 'südosten',
    'süd-osten': 'südosten', 'sued-osten': 'südosten',
    'nw': 'nordwesten', 'nordwesten': 'nordwesten', 'nord-westen': 'nordwesten',
    'h': 'hoch', 'hoch': 'hoch', 'up': 'hoch',
    'r': 'runter', 'runter': 'runter', 'down': 'runter',
}


def handle_movement(cmd):
    if cmd.startswith('gehe '):
        direction = cmd[5:].strip()
        _game.move_direction(direction)
        return True

    direction = _DIRECTION_MAP.get(cmd)
    if direction:
        _game.move_direction(direction)
        return True

    return False


# ========================
# ITEM COMMANDS
# ========================
def handle_item_commands(cmd):
    """Handles: nimm, lese/lies, inventar/inv, esse/iss"""

    # --- NIMM (without 'aus') ---
    if cmd == 'nimm':
        room = _game.rooms[_game.current_room]
        available = room.get('items', [])
        if len(available) == 1:
            _game.process_command(f'nimm {available[0]}')
        elif len(available) > 1:
            _h("Was möchtest du nehmen?")
            for idx, it in enumerate(available, 1):
                _h(f"  {idx}. {_game.get_item_name(it)}")
            _game.pending_ambiguity = {'action': 'nimm', 'candidates': available[:], 'original_cmd': 'nimm'}
            _h("")
        else:
            _h("Hier gibt es nichts zum Nehmen.")
            _h("")
        return True

    if cmd.startswith('nimm ') and ' aus ' not in cmd:
        item = cmd[5:].strip()
        room = _game.rooms[_game.current_room]
        if item in room['items']:
            idef = _game.ITEM_DEFS.get(item)
            item_weight = idef.weight if idef else 1
            if _game.get_player_carry_weight() + item_weight > _game.player_stats['max_weight']:
                _h("Deine Last ist zu schwer. Du kannst nichts mehr tragen.")
                _h("")
            else:
                room['items'].remove(item)
                _game.player_inventory.append(item)
                _h(f"Du nimmst {_game.get_item_name(item)}.")
                _game.add_score('item_pickup')
                enc = _game.get_encumbrance_description()
                if enc:
                    _h(enc)
                _h("")
        else:
            _h(f"Hier gibt es kein '{item}'.")
            _h("")
        return True

    # --- LESE / LIES ---
    if cmd.startswith('lese ') or cmd.startswith('lies ') or cmd.startswith('lesen '):
        if cmd.startswith('lese '):
            item = cmd[5:].strip()
        elif cmd.startswith('lies '):
            item = cmd[5:].strip()
        elif cmd.startswith('lesen '):
            item = cmd[6:].strip()

        _game.read_item(item)
        if item == 'tagebuch':
            _h("Im Tagebuch hast du deine letzen 2 Jahre in diesem haus Dokumentiert.")
            _h("Jeder einzelne zombie oder Mensch der versuchte reinzukommen.")
        elif item == 'Stück Papier':
            _h("Ein stück Papier, es hat blut schmieren drauf, teile der Notiz dadurch unlesbar.")
            _h("Sie sind üb....... nirgends ist man sicher. Alles geshah nu........... em Präs......... abor.")
        return True

    # --- INVENTAR ---
    if cmd in ('inventar', 'inv', 'i'):
        _h("INVENTAR")
        _h("")
        if _game.player_inventory:
            item_names = [_game.get_item_name(it) for it in _game.player_inventory]
            _h(f"Items: {', '.join(item_names)}")
        else:
            _h("Items: Leer")
        if _game.player_stats['equipped_weapon']:
            weapon = weapons[_game.player_stats['equipped_weapon']]
            _h(f"Waffe: {weapon['name']}")
        else:
            _h("Waffe: Keine")
        fist_level = _game.player_stats['fist_level']
        if fist_level >= 5:
            _h("Fäuste: Meisterhaft")
        elif fist_level >= 3:
            _h("Fäuste: Erfahren")
        else:
            _h("Fäuste: Untrainiert")
        _h("")
        _h(_game.get_health_description())
        enc = _game.get_encumbrance_description()
        if enc:
            _h(enc)
        _h("")
        return True

    # --- ESSE / ISS ---
    if cmd.startswith('esse ') or cmd.startswith('iss '):
        if cmd.startswith('esse '):
            item = cmd[5:].strip()
        else:
            item = cmd[4:].strip()

        if item not in _game.player_inventory:
            _h(f"Du hast kein '{item}' im Inventar.")
            _h("")
        elif item not in food_items:
            _h(f"'{item}' kann man nicht essen.")
            _h("")
        else:
            food = food_items[item]
            old_hp = _game.player_stats['health']
            _game.player_stats['health'] = min(100, _game.player_stats['health'] + food['heal'])
            healed = _game.player_stats['health'] - old_hp
            _game.player_inventory.remove(item)
            _game.player_stats['hunger'] = max(0, _game.player_stats['hunger'] - 30)
            _game.player_stats['turns_since_last_meal'] = 0
            _game.player_stats['strength'] = min(100, _game.player_stats['strength'] + food['heal'] // 2)
            _h(food['message'])
            if healed > 0:
                if healed >= 30:
                    _h("Du fühlst dich deutlich besser.")
                elif healed >= 15:
                    _h("Etwas Kraft kehrt in deinen Körper zurück.")
                else:
                    _h("Du fühlst dich ein wenig gestärkt.")
            else:
                _h("Du bist bereits in guter Verfassung.")
            if _game.player_stats['hunger'] <= 0:
                _h("Dein Hunger ist gestillt.")
            _h("")
        return True

    return False


# ========================
# COMBAT COMMANDS
# ========================
def handle_combat_commands(cmd):
    """Handles: ausrüsten, schieße/schiesse, schlag/schlage, stich"""

    if cmd.startswith('ausrüsten '):
        weapon_key = cmd[10:].strip()
        _game.equip_weapon(weapon_key)
        return True

    if cmd.startswith('schieße auf ') or cmd.startswith('schiesse auf ') or \
       cmd.startswith('schieße ') or cmd.startswith('schiesse '):
        if 'auf ' in cmd:
            target = cmd.split('auf ', 1)[1].strip()
        else:
            target = cmd.split('schieße ', 1)[1].strip() if 'schieße ' in cmd else cmd.split('schiesse ', 1)[1].strip()

        room = _game.rooms[_game.current_room]
        if _game.current_room == 'start' and room.get('enemy') == 'zombie' and not _game.player_stats['equipped_weapon']:
            _h("Du hast keine Waffe!")
            _h("Du versuchst wild um dich zu schlagen...")
            _h("")
            if random.random() < 0.3:
                _h("Der Zombie ist schneller!")
                _h("Tentakel durchbohren deine Brust.")
                _h("Schwärze übernimmt deine Vision...")
                _h("")
                _h("=== DU BIST GESTORBEN ===")
                _h("")
                _reset_player()
                _game.rooms['start']['first_visit'] = True
                _game.rooms['start']['enemy'] = 'zombie'
                _game.rooms['start']['items'] = ['feuerlöscher', 'zeitung']
                _game.reset_transitions()
                _game.start_game()
            else:
                _h("Du stolperst zurück und weichst aus!")
                _h("Schnell, nimm eine Waffe!")
            _h("")
        else:
            _game.ranged_attack(target)
        return True

    if cmd.startswith('schlag ') or cmd.startswith('schlage '):
        if ' mit ' in cmd:
            parts = cmd.split(' ', 1)[1]
            target_and_weapon = parts.split(' mit ')
            if len(target_and_weapon) == 2:
                target = target_and_weapon[0].strip()
                weapon_name = target_and_weapon[1].strip()
                room = _game.rooms[_game.current_room]
                enemy_in_room = room.get('enemy', None)
                if not enemy_in_room:
                    _h("Es gibt hier nichts zum Angreifen!")
                    _h("")
                else:
                    enemy = enemies.get(enemy_in_room)
                    t = target.lower().strip()
                    enemy_words = [enemy_in_room] + enemy['name'].lower().replace('-', ' ').split()
                    if t == enemy_in_room or t in enemy_words:
                        _game.attack_with_weapon(target, weapon_name)
                    else:
                        _h(f"Hier ist kein '{target}'.")
                        if enemy:
                            _h(f"Hier ist: {enemy['name']}")
                        _h("")
            else:
                _h("Falsches Format. Nutze: schlag [ziel] mit [waffe]")
                _h("")
        else:
            target = cmd.split(' ', 1)[1].strip()
            room = _game.rooms[_game.current_room]
            enemy_in_room = room.get('enemy', None)
            if not enemy_in_room:
                _h("Es gibt hier nichts zum Angreifen!")
                _h("")
            else:
                enemy = enemies.get(enemy_in_room)
                t = target.lower().strip()
                enemy_words = [enemy_in_room] + enemy['name'].lower().replace('-', ' ').split()
                if t == enemy_in_room or t in enemy_words:
                    _game.unarmed_attack(target)
                else:
                    _h(f"Hier ist kein '{target}'.")
                    if enemy:
                        _h(f"Hier ist: {enemy['name']}")
                    _h("")
        return True

    if cmd.startswith('stich auf '):
        target = cmd[10:].strip()
        _game.melee_attack(target)
        return True

    return False


def _reset_player():
    """Reset player stats to defaults (used on death)."""
    _game.player_stats['health'] = 100
    _game.player_stats['strength'] = 100
    _game.player_stats['hunger'] = 0
    _game.player_stats['turns_since_last_meal'] = 0
    _game.player_stats['last_recovery_turn'] = 0
    _game.player_stats['equipped_weapon'] = None
    _game.player_stats['weapon_type'] = None
    _game.player_stats['in_combat'] = False
    _game.player_stats['fist_level'] = 1
    for enemy_key in enemies:
        enemies[enemy_key]['health'] = enemies[enemy_key]['max_health']


# ========================
# SYSTEM COMMANDS
# ========================
def handle_system_commands(cmd):
    """Handles: clear, echo, time, whoami, neu, verbose/brief/superbrief,
    info, quit, save, restore, score, zeit, diagnose"""

    if cmd in ('clear', 'cls'):
        _game.game_history.clear()
        _h("Terminal geleert.")
        _h("")
        return True

    if cmd.startswith('echo '):
        text = cmd[5:].strip()
        _h(text)
        _h("")
        return True

    if cmd == 'time':
        now = datetime.datetime.now()
        _h(f"Aktuelle Zeit: {now.strftime('%H:%M:%S')}")
        _h(f"Datum: {now.strftime('%d.%m.%Y')}")
        _h("")
        return True

    if cmd == 'whoami':
        _h("Name: Albert Wesker Cristal")
        _h("Status: Überlebender")
        _h("Standort: Bunker")
        _h("")
        return True

    if cmd == 'neu':
        _reset_player()
        for idef in _game.ITEM_DEFS.values():
            if idef.max_charge >= 0:
                idef.charge = idef.max_charge
        _game.rooms['start']['first_visit'] = True
        _game.rooms['start']['enemy'] = 'zombie'
        _game.rooms['start']['items'] = ['feuerlöscher', 'zeitung']
        _game.reset_transitions()
        _game.start_game()
        return True

    if cmd in ('verbose', 'ausführl', 'ausführli'):
        _game.view_mode = 'verbose'
        _h("Modus: VERBOSE – Volle Beschreibungen.")
        _h("")
        return True

    if cmd in ('brief', 'kurz'):
        _game.view_mode = 'brief'
        _h("Modus: BRIEF – Kurze Beschreibungen bei Wiederbesuch.")
        _h("")
        return True

    if cmd in ('superbrie', 'superkur', 'superkurz'):
        _game.view_mode = 'superbrief'
        _h("Modus: SUPERBRIEF – Nur Raumnamen.")
        _h("")
        return True

    if cmd == 'info':
        _h("═══════════════════════════════")
        _h("  DEAD WORLD v1.0")
        _h("  Ein Zork-inspiriertes")
        _h("  Survival Text-Adventure")
        _h("  mit Pygame Terminal-UI")
        _h("═══════════════════════════════")
        _h(f"  Züge: {_game.game_moves}")
        _h(f"  Punkte: {_game.game_score}")
        _h(f"  Spielzeit: {_game.format_elapsed_time()}")
        _h("")
        return True

    if cmd in ('q', 'quit', 'beenden'):
        _h("═══ SPIELENDE ═══")
        _h(f"Punkte: {_game.game_score}")
        _h(f"Züge: {_game.game_moves}")
        _h(f"Spielzeit: {_game.format_elapsed_time()}")
        _h("")
        _h("Willst du wirklich beenden? (Tippe 'neu' für Neustart)")
        _h("")
        return True

    if cmd in ('save', 'speicher', 'speichern'):
        _game.save_game()
        return True

    if cmd in ('restore', 'laden'):
        _game.restore_game()
        return True

    if cmd in ('score', 'punkte'):
        _h(f"Punkte: {_game.game_score}")
        _h(f"Züge: {_game.game_moves}")
        _h("")
        return True

    if cmd == 'zeit':
        _h(f"Spielzeit: {_game.format_elapsed_time()}")
        ticks_total = pygame.time.get_ticks() - _game.game_start_ticks
        _h(f"Pygame Ticks: {ticks_total}")
        _h("")
        return True

    if cmd in ('diagnose', 'd'):
        _h("═══ DIAGNOSE ═══")
        _h(_game.get_health_description())
        _h(_game.get_strength_description())
        hunger_desc = _game.get_hunger_description()
        if hunger_desc:
            _h(hunger_desc)
        if _game.player_stats['equipped_weapon']:
            w = weapons[_game.player_stats['equipped_weapon']]
            _h(f"Waffe: {w['name']}")
        else:
            _h("Waffe: Keine")
        _h(f"Kampfstatus: {'IM KAMPF' if _game.player_stats['in_combat'] else 'Sicher'}")
        enc = _game.get_encumbrance_description()
        if enc:
            _h(enc)
        for litem in _game.player_inventory:
            lidef = _game.ITEM_DEFS.get(litem)
            if lidef and lidef.max_charge >= 0:
                if lidef.charge <= 0:
                    _h(f"{lidef.name}: Erloschen")
                elif lidef.charge <= 20:
                    _h(f"{lidef.name}: Schwaches Licht")
                else:
                    _h(f"{lidef.name}: Leuchtet")
        _h("")
        return True

    return False


# ========================
# INTERACTION COMMANDS
# ========================
def handle_interaction_commands(cmd):
    """Handles: schieben, aufbrechen"""

    if cmd in ('schieben', 'schieb', 'regal schieben', 'schrank schieben', 'bücherregal schieben'):
        if _game.current_room == 'bibliothek_3':
            if not _game.bibliothek_4_schrank_geschoben:
                _game.bibliothek_4_schrank_geschoben = True
                _game.unlock_transition('bib_3_4')
                _h("Du stemmst dich gegen das schwere Bücherregal...")
                _h("Mit aller Kraft schiebst du es zur Seite!")
                _h("Der Weg nach NORDEN ist jetzt frei.")
                _h("")
            else:
                _h("Das Bücherregal wurde bereits zur Seite geschoben.")
                _h("")
        else:
            _h("Hier gibt es nichts zum Schieben.")
            _h("")
        return True

    if cmd in ('Brech auf', 'Zerhacke tür', 'schlage tür auf', 'tür aufbrechen', 'tür mit Axt aufschalgen'):
        if _game.current_room == 'haus1' and 'axt' in _game.player_inventory:
            if not _game.haus1_tür_auf:
                _game.haus1_tür_auf = True
                _game.unlock_transition('haus1_tuer')
                _h("Du nimmst die Axt in die Hände")
                _h("Mit wucht schlägst du mit der Axt auf die Tür ein")
                _h("Man kann nun ins Haus rein")
                _h("")
            else:
                _h("Die Tür ist bereits aufgebrochen")
                _h("")
        else:
            _h("Du hast nichts um die Tür zu öffnen.")
            _h("")
        return True

    return False


# ========================
# CONTAINER COMMANDS
# ========================
def handle_container_commands(cmd):
    """Handles: öffne, schließe, lege...in, nimm...aus, schaue in"""

    if cmd.startswith('öffne ') or cmd.startswith('oeffne '):
        target = cmd.split(' ', 1)[1].strip()[:9]
        _game.handle_container_open(target)
        return True

    if cmd.startswith('schließ') or cmd.startswith('schliess'):
        parts = cmd.split(' ', 1)
        if len(parts) > 1:
            target = parts[1].strip()[:9]
            _game.handle_container_close(target)
        else:
            _h("Was willst du schließen?")
            _h("")
        return True

    if ' in ' in cmd and cmd.startswith('lege '):
        rest = cmd[5:].strip()
        parts = rest.split(' in ', 1)
        if len(parts) == 2:
            _game.handle_put_in(parts[0].strip(), parts[1].strip())
        else:
            _h("Format: lege [item] in [behälter]")
            _h("")
        return True

    if ' aus ' in cmd and cmd.startswith('nimm '):
        rest = cmd[5:].strip()
        parts = rest.split(' aus ', 1)
        if len(parts) == 2:
            _game.handle_take_from(parts[0].strip(), parts[1].strip())
        else:
            _h("Format: nimm [item] aus [behälter]")
            _h("")
        return True

    if cmd.startswith('schaue in ') or cmd.startswith('schau in '):
        target = cmd.split(' in ', 1)[1].strip()
        _game.handle_look_in(target)
        return True

    return False


# ========================
# LOOK / MAP (inline, small)
# ========================
def handle_look_map(cmd):
    """Handles: schaue/look/l, karte/map"""

    if cmd in ('schaue', 'look', 'l'):
        _game.describe_room()
        return True

    if cmd in ('karte', 'map'):
        bldg_name, bldg_title, floor = _game.get_room_context(_game.current_room)
        room_name = _game.rooms.get(_game.current_room, {}).get('name', _game.current_room)
        _h(">>> STANDORT INFO <<<")
        _h(f"Gebäude: {bldg_title}")
        _h(f"Etage:   {floor.capitalize()}")
        _h(f"Raum:    {room_name}")
        _h("")
        _h("Gefundene Ausgänge:")
        transitions = _game.get_transitions_from(_game.current_room)
        if not transitions:
            _h("  (Keine sichtbaren Ausgänge)")
        else:
            for d, tgt, t in transitions:
                tgt_name = _game.rooms.get(tgt, {}).get('name', tgt)
                t_type = t.get('type', 'passage')
                lock_str = " [VERSCHLOSSEN]" if t.get('locked') else ""
                icon = "🚪" if t_type in ('door', 'entrance') else "🪜" if t_type == 'stairs' else "➡️"
                _h(f"  {d.capitalize():<12} {icon} {tgt_name} {lock_str}")
        _h("")
        return True

    return False


# ========================
# REACTIVE PARSER (unknown commands)
# ========================
def handle_unknown_command(cmd, words):
    """Last-resort handler: reactive parser for unknown/ambiguous commands."""
    verb = words[0] if words else ''
    obj = ' '.join(words[1:]) if len(words) > 1 else ''
    room = _game.rooms[_game.current_room]
    all_known_items = set(_game.ITEM_DEFS.keys())
    room_items = set(room.get('items', []))
    inv_items = set(_game.player_inventory)

    # 1) Verb braucht Objekt aber keins angegeben
    if verb in VERBS_NEED_OBJECT and not obj:
        infinitiv = VERBS_NEED_OBJECT[verb]
        _h(f"Was willst du {infinitiv}?")
        _game.pending_ambiguity = {'action': verb, 'candidates': list(room_items | inv_items), 'original_cmd': verb}
        _h("")
        return

    # 2) Logisch unmögliche Aktionen
    if verb in ('esse', 'iss') and obj:
        if obj in weapons:
            _h(random.choice(ILLOGICAL_RESPONSES['eat_weapon']))
            _h("")
            return
        if obj in all_known_items and obj not in food_items:
            _h(random.choice(ILLOGICAL_RESPONSES['eat_inedible']))
            _h("")
            return
    if verb in ('ausrüsten',) and obj:
        if obj in food_items:
            _h(random.choice(ILLOGICAL_RESPONSES['equip_food']))
            _h("")
            return
        if obj in all_known_items and obj not in weapons:
            _h(random.choice(ILLOGICAL_RESPONSES['equip_non_weapon']))
            _h("")
            return

    # 3) Objekt existiert im Spiel aber nicht hier
    if obj and obj in all_known_items:
        if obj not in room_items and obj not in inv_items:
            _h(f"Du siehst hier kein '{_game.get_item_name(obj)}'.")
            _h("")
            return

    # 4) Partielle Objekterkennung / Disambiguation
    if obj:
        available = list(room_items | inv_items)
        matches = [it for it in available if obj in it or it.startswith(obj)]
        if len(matches) == 1 and verb in VERBS_NEED_OBJECT:
            _game.process_command(f"{verb} {matches[0]}")
            return
        elif len(matches) > 1:
            _h("Was meinst du?")
            for idx, m in enumerate(matches, 1):
                _h(f"  {idx}. {_game.get_item_name(m)}")
            _game.pending_ambiguity = {'action': verb, 'candidates': matches, 'original_cmd': cmd}
            _h("")
            return

    # 5) Unbekanntes Verb
    if verb and verb[:9] not in KNOWN_VERBS:
        resp = random.choice(UNKNOWN_VERB_RESPONSES).format(verb=verb)
        _h(resp)
        _h("")
