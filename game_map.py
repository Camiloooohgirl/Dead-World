# ============================================================================
# game_map.py — Dead World 2D Spatial Map
# ============================================================================
# Auto-generates (x, y) grid coordinates for every room using BFS traversal.
# Import GAME_MAP from this module to get a dict keyed by (x,y) tuples.
# ============================================================================

from collections import deque

# ---------------------------------------------------------------------------
# Direction → (dx, dy) offsets
# Convention: North = -Y (up on screen), South = +Y, East = +X, West = -X
# ---------------------------------------------------------------------------
DIRECTION_DELTAS = {
    'norden':     ( 0, -1),
    'süden':      ( 0,  1),
    'osten':      ( 1,  0),
    'westen':     (-1,  0),
    'nordosten':  ( 1, -1),
    'nordwesten': (-1, -1),
    'südosten':   ( 1,  1),
    'südwesten':  (-1,  1),
    'hoch':       ( 0, -1),   # stairs up   = visual north
    'runter':     ( 0,  1),   # stairs down = visual south
}

# ---------------------------------------------------------------------------
# Biome / terrain classification per room key
# ---------------------------------------------------------------------------
BIOME_MAP = {
    # --- Bunker ---
    'start':        'bunker',
    'corridor':     'bunker',
    'laboratory':   'bunker',
    'storage':      'bunker',
    'tunnel':       'tunnel',
    # --- Versteck (Safehouse) ---
    'spawn':           'safehouse',
    'schlafzimmer':    'indoor',
    'flur':            'indoor',
    'badezimmer':      'indoor',
    'eingangsbereich': 'indoor',
    'wohnzimmer':      'indoor',
    'wohnbereich':     'indoor',
    'schlafzimmer2':   'indoor',
    'kueche':          'indoor',
    'vordertuer':      'indoor',
    'treppen':         'indoor',
    'keller':          'underground',
    'lagerraum':       'underground',
    # --- Stadt (Streets) ---
    'suedlich_haus':               'street',
    'westlich_haus_gabelung':      'street',
    'oestlich_weggabelung':        'street',
    'nord_westliche_weggabelung':  'street',
    'nord_östliche_weggabelung':   'street',
    'östliche_straße':             'street',
    'norden_straße':               'street',
    'park_straße':                 'street',
    'skyscraper_weggabelung':      'street',
    'weggabelung_skyscraper2':     'street',
    'noerdlich_haus':              'street',
    # --- Krankenhaus ---
    'krankenhaus_straße':  'street',
    'krankenhaus_eingang': 'hospital',
    # --- Bibliothek ---
    'bibliothek_straße':   'street',
    'bibliothek_eingang':  'library',
    'bibliothek_1.1':      'library',
    'bibliothek_1.2':      'library',
    'bibliothek_2':        'library',
    'bibliothek_3':        'library',
    'bibliothek_4':        'library',
    'bibliothek_5':        'library',
    'bibliothek_6':        'library',
    'bibliothek_7':        'library',
    'bibliothek_8':        'library',
    # --- Walmart ---
    'parkplatz':       'parking',
    'walmart_eingang': 'store',
    'walmart_1':       'store',
    'walmart_2':       'store',
    'walmart_3':       'store',
    'walmart_4':       'store',
    'walmart_5':       'store',
    'walmart_6':       'store',
    'walmart_7':       'store',
    'walmart_8':       'store',
    'walmart_9':       'store',
    'walmart_10':      'store',
    'walmart_11':      'store',
    'walmart_12.1':    'store',
    'walmart_12.2':    'store',
    'walmart_13':      'store',
    'walmart_14':      'store',
    # --- Haus 1 ---
    'haus1':           'house',
    # --- Haus 3 ---
    'haus_3_eingang':      'house',
    'haus_3_v':            'house',
    'haus_3_wohnbereich':  'house',
    'wohnzimmer_h3':       'house',
    'küche_h3':            'house',
    'bathroom_3':          'house',
    'bedroom_3':           'house',
}

# Placeholder rooms that are referenced in exits but not yet defined
UNIMPLEMENTED_ROOMS = {
    'haus2', 'park', 'haus1_vordertür', 'bedroom_2',
    'straße_pizzeria', 'home_depot_straße_ost',
}


# ---------------------------------------------------------------------------
# Bidirectional adjacency builder
# ---------------------------------------------------------------------------

_OPPOSITE = {
    'norden': 'süden', 'süden': 'norden',
    'osten': 'westen', 'westen': 'osten',
    'nordosten': 'südwesten', 'südwesten': 'nordosten',
    'nordwesten': 'südosten', 'südosten': 'nordwesten',
    'hoch': 'runter', 'runter': 'hoch',
}

def _build_adjacency(rooms):
    """
    Build a bidirectional adjacency dict from the rooms graph.
    adj[room_a] = set of (direction_from_a, room_b)

    Rooms with empty exits (e.g. 'start', 'spawn') gain reverse edges
    from their neighbors, so they are still reachable by BFS.
    """
    adj = {rk: set() for rk in rooms}

    for rk, room in rooms.items():
        for direction, target in room.get('exits', {}).items():
            adj[rk].add((direction, target))
            # Reverse edge for rooms that exist
            rev_dir = _OPPOSITE.get(direction)
            if rev_dir and target in rooms:
                adj.setdefault(target, set()).add((rev_dir, rk))

    return adj


# ---------------------------------------------------------------------------
# BFS Coordinate Solver
# ---------------------------------------------------------------------------

def build_game_map(rooms, seed_room='vordertuer', seed_coord=(0, 0),
                   bunker_seed_room='corridor', bunker_seed_coord=(0, 10)):
    """
    Walk the rooms graph via BFS on a bidirectional adjacency graph,
    assigning (x, y) coordinates based on directional exits.

    Returns: (game_map, coord_of)
      - game_map: { (x,y): { room data dict } }
      - coord_of: { room_key: (x,y) }

    Three BFS passes:
      1. Main world seeded at vordertuer (0, 0)
      2. Bunker seeded at corridor (0, 10) — disconnected underground
      3. Orphan sweep for anything still unmapped
    """
    adj = _build_adjacency(rooms)
    coord_of = {}     # room_key → (x, y)
    occupied = {}     # (x, y) → room_key

    def _nearest_free(target_x, target_y):
        """Spiral outward from (target_x, target_y) to find a free cell."""
        if (target_x, target_y) not in occupied:
            return (target_x, target_y)
        for radius in range(1, 50):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:
                        candidate = (target_x + dx, target_y + dy)
                        if candidate not in occupied:
                            return candidate
        return (target_x + 50, target_y)  # fallback

    def _bfs(start_key, start_xy):
        if start_key not in rooms:
            return
        if start_key in coord_of:
            return  # already placed by a previous pass
        sx, sy = start_xy
        actual = _nearest_free(sx, sy)
        coord_of[start_key] = actual
        occupied[actual] = start_key

        queue = deque([start_key])
        visited = {start_key}

        while queue:
            current = queue.popleft()
            cx, cy = coord_of[current]

            for direction, target_key in adj.get(current, set()):
                if target_key in visited:
                    continue
                if target_key not in rooms and target_key not in UNIMPLEMENTED_ROOMS:
                    continue

                delta = DIRECTION_DELTAS.get(direction, (0, 0))
                tx, ty = cx + delta[0], cy + delta[1]
                actual = _nearest_free(tx, ty)

                visited.add(target_key)
                coord_of[target_key] = actual
                occupied[actual] = target_key

                if target_key in rooms:
                    queue.append(target_key)

    # --- Pass 1: Main world (everything reachable from vordertuer) ---
    _bfs(seed_room, seed_coord)

    # --- Pass 2: Bunker (disconnected underground) ---
    _bfs(bunker_seed_room, bunker_seed_coord)

    # --- Pass 3: catch any orphan rooms not reached by either BFS ---
    orphan_y = max(y for (_, y) in occupied) + 2 if occupied else 20
    orphan_x = 0
    for rk in rooms:
        if rk not in coord_of:
            actual = _nearest_free(orphan_x, orphan_y)
            coord_of[rk] = actual
            occupied[actual] = rk
            orphan_x += 2

    # -----------------------------------------------------------------
    # Build the final GAME_MAP dict keyed by (x, y)
    # -----------------------------------------------------------------
    game_map = {}
    for room_key, (gx, gy) in coord_of.items():
        if room_key in rooms:
            room_data = rooms[room_key]
            biome = BIOME_MAP.get(room_key, 'unknown')
            # Compute adjacency list with coordinates
            connections = {}
            for direction, target_key in room_data.get('exits', {}).items():
                if target_key in coord_of:
                    connections[direction] = {
                        'target': target_key,
                        'coord': coord_of[target_key],
                    }
                else:
                    connections[direction] = {
                        'target': target_key,
                        'coord': None,  # unimplemented target
                    }

            game_map[(gx, gy)] = {
                'key':          room_key,
                'name':         room_data.get('name', room_key),
                'description':  room_data.get('description', ''),
                'biome':        biome,
                'items':        room_data.get('items', []),
                'exits':        room_data.get('exits', {}),
                'connections':  connections,
                'enemy':        room_data.get('enemy'),
                'is_safehouse': room_data.get('is_safehouse', False),
                'in_development': room_data.get('in_development', False),
                'zombie_spawn': room_data.get('zombie_spawn', False),
                'spawn_chance': room_data.get('spawn_chance', False),
                'status':       'active',
            }
        elif room_key in UNIMPLEMENTED_ROOMS:
            game_map[(gx, gy)] = {
                'key':          room_key,
                'name':         room_key.replace('_', ' ').title(),
                'description':  '',
                'biome':        'unknown',
                'items':        [],
                'exits':        {},
                'connections':  {},
                'enemy':        None,
                'is_safehouse': False,
                'in_development': True,
                'zombie_spawn': False,
                'spawn_chance': False,
                'status':       'unimplemented',
            }

    return game_map, coord_of


# ---------------------------------------------------------------------------
# Reverse lookup helper:  room_key → (x, y)
# ---------------------------------------------------------------------------
_coord_lookup = {}  # populated after build

def get_room_coord(room_key):
    """Return (x, y) for a room key, or None if not mapped."""
    return _coord_lookup.get(room_key)


# ---------------------------------------------------------------------------
# Build the map at import time using the rooms dict from the main game module
# ---------------------------------------------------------------------------
# We import rooms lazily to avoid circular imports.
# If this module is imported before the main game, GAME_MAP will be empty
# and must be rebuilt with rebuild_game_map().

GAME_MAP = {}

def rebuild_game_map(rooms_dict):
    """
    (Re)build GAME_MAP from a rooms dictionary.
    Call this after the rooms dict is available.
    Returns the GAME_MAP for convenience.
    """
    global GAME_MAP, _coord_lookup
    GAME_MAP, _coord_lookup = build_game_map(rooms_dict)
    return GAME_MAP


# ---------------------------------------------------------------------------
# Biome color palette for Pygame rendering
# ---------------------------------------------------------------------------
BIOME_COLORS = {
    'bunker':       (80,  80,  90),    # dark steel gray
    'tunnel':       (60,  55,  50),    # earthy brown
    'safehouse':    (40, 120,  60),    # safe green
    'indoor':       (100, 90,  80),    # warm beige
    'underground':  (50,  45,  55),    # deep purple-gray
    'street':       (70,  75,  85),    # asphalt blue-gray
    'hospital':     (180, 50,  50),    # medical red
    'library':      (110, 85,  60),    # old book brown
    'parking':      (90,  90,  90),    # concrete gray
    'store':        (50,  90, 150),    # walmart blue
    'house':        (130, 100, 70),    # wooden brown
    'unknown':      (55,  55,  55),    # dim gray placeholder
}

# Icon glyphs (Unicode) for map node rendering
BIOME_ICONS = {
    'bunker':       '⚙',
    'tunnel':       '🕳',
    'safehouse':    '🏠',
    'indoor':       '🚪',
    'underground':  '⬇',
    'street':       '🛣',
    'hospital':     '🏥',
    'library':      '📚',
    'parking':      '🅿',
    'store':        '🛒',
    'house':        '🏡',
    'unknown':      '❓',
}


# ---------------------------------------------------------------------------
# Standalone: print info when run directly
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("\n=== game_map.py standalone mode ===")
    print("To generate the map, call from your game:")
    print("  from game_map import rebuild_game_map, GAME_MAP")
    print("  rebuild_game_map(rooms)")
    print(f"  # GAME_MAP will contain {{(x,y): room_data}} entries")
    print(f"\nDefined {len(BIOME_MAP)} biome classifications")
    print(f"Defined {len(UNIMPLEMENTED_ROOMS)} placeholder rooms")
    print(f"Defined {len(BIOME_COLORS)} biome colors for rendering")
    print(f"Defined {len(DIRECTION_DELTAS)} direction deltas")
