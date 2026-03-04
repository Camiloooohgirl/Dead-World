# ============================================================
# event_handlers.py — Extracted Event Handlers for Dead World
# ============================================================
# Splits the dense main() event loop into focused handler functions.
# Each handler accesses game state via a module reference (_game).

import pygame
import random
from config import *

_game = None


def init_event_handlers(game_module):
    """Call once at startup to provide reference to main game module."""
    global _game
    _game = game_module


# ========================
# KEY REPEAT LOGIC
# ========================
def handle_key_repeats(current_ms):
    """Process held-key repeats for terminal input. Called every frame."""
    if _game.prolog_shown and not _game.qte_active and _game.current_state == GAME:
        if _game.backspace_held:
            if current_ms - _game.last_backspace_time > backspace_repeat_delay:
                if _game.cursor_position > 0:
                    _game.input_text = _game.input_text[:_game.cursor_position-1] + _game.input_text[_game.cursor_position:]
                    _game.cursor_position -= 1
                _game.last_backspace_time = current_ms

        if _game.delete_held:
            if current_ms - _game.last_delete_time > key_repeat_delay:
                if _game.cursor_position < len(_game.input_text):
                    _game.input_text = _game.input_text[:_game.cursor_position] + _game.input_text[_game.cursor_position+1:]
                _game.last_delete_time = current_ms

        if _game.left_held:
            if current_ms - _game.last_left_time > key_repeat_delay:
                if _game.cursor_position > 0:
                    _game.cursor_position -= 1
                _game.last_left_time = current_ms

        if _game.right_held:
            if current_ms - _game.last_right_time > key_repeat_delay:
                if _game.cursor_position < len(_game.input_text):
                    _game.cursor_position += 1
                _game.last_right_time = current_ms

    # Enter repeat (works in both prolog and game)
    if _game.enter_held and _game.current_state == GAME:
        if current_ms - _game.last_enter_time > key_repeat_delay:
            if not _game.prolog_shown:
                _game.process_command("")
            _game.last_enter_time = current_ms


# ========================
# KEYUP
# ========================
def handle_keyup(event):
    """Release held-key flags."""
    if event.key == pygame.K_BACKSPACE:
        _game.backspace_held = False
    elif event.key == pygame.K_DELETE:
        _game.delete_held = False
    elif event.key == pygame.K_LEFT:
        _game.left_held = False
    elif event.key == pygame.K_RIGHT:
        _game.right_held = False
    elif event.key == pygame.K_RETURN:
        _game.enter_held = False


# ========================
# KEYDOWN — MAP STATE
# ========================
def handle_keydown_map(event):
    """Keydown events while in MAP state."""
    if _game.block_naming:
        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_F12):
            if _game.selected_block_idx is not None and _game.selected_block_idx < len(_game.custom_blocks):
                _game.custom_blocks[_game.selected_block_idx]['name'] = _game.block_name_input
            _game.block_naming = False
        elif event.key == pygame.K_BACKSPACE:
            _game.block_name_input = _game.block_name_input[:-1]
        elif event.unicode.isprintable() and len(_game.block_name_input) < 30:
            _game.block_name_input += event.unicode
        return True  # consumed, skip other MAP key handling

    if event.key == pygame.K_UP:
        _game.map_camera_y -= 50 / _game.map_zoom
    elif event.key == pygame.K_DOWN:
        _game.map_camera_y += 50 / _game.map_zoom
    elif event.key == pygame.K_LEFT:
        _game.map_camera_x -= 50 / _game.map_zoom
    elif event.key == pygame.K_RIGHT:
        _game.map_camera_x += 50 / _game.map_zoom
    elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
        _game.map_zoom = min(3.0, _game.map_zoom + 0.15)
    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
        _game.map_zoom = max(0.3, _game.map_zoom - 0.15)
    elif event.key in (pygame.K_m, pygame.K_ESCAPE):
        _game.current_state = GAME
        _game.map_dragging = False
        _game.node_dragging = False
        _game.node_drag_key = None
        _game.building_dragging = False
        _game.building_drag_key = None
    elif event.key == pygame.K_r:
        _game.map_camera_x = 0
        _game.map_camera_y = 0
        _game.map_zoom = 1.0
    elif event.key == pygame.K_s:
        _game.save_map_layout()
        _game.draw_map._save_msg_time = pygame.time.get_ticks()
    elif event.key == pygame.K_n:
        gcx = _game.map_camera_x / 50
        gcy = _game.map_camera_y / 50
        new_block = {
            'name': f'Block {len(_game.custom_blocks)+1}',
            'gx': gcx - 2, 'gy': gcy - 2,
            'gw': 4, 'gh': 4,
            'color': [random.randint(40, 120), random.randint(40, 120), random.randint(40, 120)]
        }
        _game.custom_blocks.append(new_block)
        _game.selected_block_idx = len(_game.custom_blocks) - 1
    elif event.key == pygame.K_F12:
        if _game.selected_block_idx is not None and _game.selected_block_idx < len(_game.custom_blocks):
            _game.block_naming = True
            _game.block_name_input = _game.custom_blocks[_game.selected_block_idx]['name']
    elif event.key in (pygame.K_DELETE, pygame.K_x):
        if _game.selected_block_idx is not None and _game.selected_block_idx < len(_game.custom_blocks):
            _game.custom_blocks.pop(_game.selected_block_idx)
            _game.selected_block_idx = None
            _game.block_resizing = False
            _game.block_moving = False

    return False


# ========================
# KEYDOWN — MENU STATE
# ========================
def handle_keydown_menu(event):
    """Keydown events while in MENU state."""
    if event.key == pygame.K_UP:
        _game.menu_selected_index = (_game.menu_selected_index - 1) % len(_game.menu_buttons)
    elif event.key == pygame.K_DOWN:
        _game.menu_selected_index = (_game.menu_selected_index + 1) % len(_game.menu_buttons)
    elif event.key == pygame.K_RETURN:
        _game.menu_buttons[_game.menu_selected_index].action()


# ========================
# KEYDOWN — OPTIONS STATE
# ========================
def handle_keydown_options(event):
    """Keydown events while in OPTIONS state."""
    if event.key == pygame.K_UP:
        _game.options_selected_index = (_game.options_selected_index - 1) % 3
    elif event.key == pygame.K_DOWN:
        _game.options_selected_index = (_game.options_selected_index + 1) % 3
    elif event.key == pygame.K_LEFT:
        if _game.options_selected_index == 0:
            _game.change_resolution(-1)
        elif _game.options_selected_index == 1:
            _game.game_settings['music_volume'] = max(0.0, round(_game.game_settings['music_volume'] - 0.05, 2))
            pygame.mixer.music.set_volume(_game.game_settings['music_volume'])
        elif _game.options_selected_index == 2:
            _game.game_settings['sfx_volume'] = max(0.0, round(_game.game_settings['sfx_volume'] - 0.05, 2))
    elif event.key == pygame.K_RIGHT:
        if _game.options_selected_index == 0:
            _game.change_resolution(1)
        elif _game.options_selected_index == 1:
            _game.game_settings['music_volume'] = min(1.0, round(_game.game_settings['music_volume'] + 0.05, 2))
            pygame.mixer.music.set_volume(_game.game_settings['music_volume'])
        elif _game.options_selected_index == 2:
            _game.game_settings['sfx_volume'] = min(1.0, round(_game.game_settings['sfx_volume'] + 0.05, 2))


# ========================
# KEYDOWN — GAME STATE
# ========================
def handle_keydown_game(event):
    """Keydown events while in GAME state."""
    if event.key == pygame.K_RETURN:
        if not _game.prolog_shown:
            _game.process_command("")
        elif _game.input_text.strip().lower() in ("karte", "map") and _game.prolog_shown:
            _game.current_state = MAP
            _game.map_camera_x = 0
            _game.map_camera_y = 0
            _game.map_dragging = False
            _game.input_text = ""
            _game.cursor_position = 0
        elif _game.input_text.strip():
            raw_cmds = _game.input_text.split(',')
            for sub_cmd in raw_cmds:
                sub_cmd = sub_cmd.strip()
                if sub_cmd:
                    _game.add_to_history(f"> {sub_cmd}")
                    _game.process_command(sub_cmd)
            _game.input_text = ""
            _game.cursor_position = 0
            _game.history_index = -1
        _game.enter_held = True
        _game.last_enter_time = pygame.time.get_ticks() + key_initial_delay

    elif event.key == pygame.K_BACKSPACE and not _game.qte_active:
        if _game.cursor_position > 0:
            _game.input_text = _game.input_text[:_game.cursor_position-1] + _game.input_text[_game.cursor_position:]
            _game.cursor_position -= 1
        _game.backspace_held = True
        _game.last_backspace_time = pygame.time.get_ticks() + backspace_initial_delay

    elif event.key == pygame.K_DELETE and not _game.qte_active:
        if _game.cursor_position < len(_game.input_text):
            _game.input_text = _game.input_text[:_game.cursor_position] + _game.input_text[_game.cursor_position+1:]
        _game.delete_held = True
        _game.last_delete_time = pygame.time.get_ticks() + key_initial_delay

    elif event.key == pygame.K_LEFT and _game.prolog_shown and not _game.qte_active:
        if _game.cursor_position > 0:
            _game.cursor_position -= 1
        _game.left_held = True
        _game.last_left_time = pygame.time.get_ticks() + key_initial_delay

    elif event.key == pygame.K_RIGHT and _game.prolog_shown and not _game.qte_active:
        if _game.cursor_position < len(_game.input_text):
            _game.cursor_position += 1
        _game.right_held = True
        _game.last_right_time = pygame.time.get_ticks() + key_initial_delay

    elif event.key == pygame.K_PAGEUP and _game.prolog_shown and not _game.qte_active:
        _game.scroll_offset -= 10
        _game.scroll_offset = max(0, _game.scroll_offset)

    elif event.key == pygame.K_PAGEDOWN and _game.prolog_shown and not _game.qte_active:
        _game.scroll_offset += 10
        _game.scroll_offset = min(_game.scroll_offset, _game.max_scroll)

    elif event.key == pygame.K_HOME and _game.prolog_shown and not _game.qte_active:
        _game.scroll_offset = 0

    elif event.key == pygame.K_END and _game.prolog_shown and not _game.qte_active:
        _game.scroll_offset = _game.max_scroll

    elif event.key == pygame.K_UP and _game.prolog_shown and not _game.qte_active:
        if _game.scroll_offset == 0:
            if _game.command_history:
                if _game.history_index == -1:
                    _game.history_index = len(_game.command_history) - 1
                elif _game.history_index > 0:
                    _game.history_index -= 1
                if 0 <= _game.history_index < len(_game.command_history):
                    _game.input_text = _game.command_history[_game.history_index]
                    _game.cursor_position = len(_game.input_text)
        else:
            _game.scroll_offset -= 3
            _game.scroll_offset = max(0, _game.scroll_offset)

    elif event.key == pygame.K_DOWN and _game.prolog_shown and not _game.qte_active:
        if _game.scroll_offset == 0:
            if _game.command_history and _game.history_index != -1:
                _game.history_index += 1
                if _game.history_index >= len(_game.command_history):
                    _game.history_index = -1
                    _game.input_text = ""
                    _game.cursor_position = 0
                else:
                    _game.input_text = _game.command_history[_game.history_index]
                    _game.cursor_position = len(_game.input_text)
        else:
            _game.scroll_offset += 3
            _game.scroll_offset = min(_game.scroll_offset, _game.max_scroll)

    else:
        # QTE Mode
        if _game.qte_active and event.unicode.upper() in ('W', 'A', 'S', 'D', 'E'):
            _game.process_command(event.unicode.upper())
            _game.check_qte_result()
        # Normal input
        elif _game.prolog_shown and not _game.qte_active and len(_game.input_text) < 60 and event.unicode.isprintable():
            _game.input_text = _game.input_text[:_game.cursor_position] + event.unicode + _game.input_text[_game.cursor_position:]
            _game.cursor_position += 1


# ========================
# MOUSE — MAP STATE
# ========================
def handle_mouse_map_down(event):
    """Mouse button down events in MAP state."""
    from render_utils import scale
    UNIT = scale(50) * _game.map_zoom
    cx = _game.screen.get_width() / 2 - (_game.map_camera_x * _game.map_zoom * 50)
    cy = _game.screen.get_height() / 2 - (_game.map_camera_y * _game.map_zoom * 50)

    if event.button == 3:  # Right click
        hit = _game.get_node_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
        if hit:
            _game.node_dragging = True
            _game.node_drag_key = hit
            _game.selected_block_idx = None
        else:
            blk_idx, handle = _game.get_block_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
            if blk_idx is not None:
                _game.selected_block_idx = blk_idx
                if handle and handle != 'move':
                    _game.block_resizing = True
                    _game.block_resize_handle = handle
                else:
                    _game.block_moving = True
                    gx, gy = _game.screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
                    blk = _game.custom_blocks[blk_idx]
                    _game.block_move_offset = (blk['gx'] - gx, blk['gy'] - gy)
            else:
                _game.selected_block_idx = None

    elif event.button == 1:  # Left click
        blk_idx, _ = _game.get_block_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
        if blk_idx is not None:
            _game.selected_block_idx = blk_idx
        else:
            _game.selected_block_idx = None
        _game.map_dragging = True
        _game.map_drag_last_pos = event.pos


def handle_mouse_map_motion(event):
    """Mouse motion events in MAP state."""
    from render_utils import scale
    UNIT = scale(50) * _game.map_zoom
    cx = _game.screen.get_width() / 2 - (_game.map_camera_x * _game.map_zoom * 50)
    cy = _game.screen.get_height() / 2 - (_game.map_camera_y * _game.map_zoom * 50)

    if _game.node_dragging and _game.node_drag_key:
        gx, gy = _game.screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
        _game.GRAPH_LAYOUT[_game.node_drag_key] = (gx, gy)
    elif _game.block_moving and _game.selected_block_idx is not None:
        gx, gy = _game.screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
        _game.custom_blocks[_game.selected_block_idx]['gx'] = gx + _game.block_move_offset[0]
        _game.custom_blocks[_game.selected_block_idx]['gy'] = gy + _game.block_move_offset[1]
    elif _game.block_resizing and _game.selected_block_idx is not None:
        gx, gy = _game.screen_to_graph(event.pos[0], event.pos[1], UNIT, cx, cy)
        blk = _game.custom_blocks[_game.selected_block_idx]
        if 'r' in _game.block_resize_handle:
            blk['gw'] = max(1, gx - blk['gx'])
        if 'b' in _game.block_resize_handle:
            blk['gh'] = max(1, gy - blk['gy'])
        if 'l' in _game.block_resize_handle:
            new_x = gx
            blk['gw'] = max(1, (blk['gx'] + blk['gw']) - new_x)
            blk['gx'] = new_x
        if 't' in _game.block_resize_handle:
            new_y = gy
            blk['gh'] = max(1, (blk['gy'] + blk['gh']) - new_y)
            blk['gy'] = new_y
    elif _game.map_dragging:
        dx = event.pos[0] - _game.map_drag_last_pos[0]
        dy = event.pos[1] - _game.map_drag_last_pos[1]
        drag_speed = 0.1
        _game.map_camera_x -= dx * drag_speed / _game.map_zoom
        _game.map_camera_y -= dy * drag_speed / _game.map_zoom
        _game.map_drag_last_pos = event.pos
    else:
        _game.node_hovered_key = _game.get_node_at_screen_pos(event.pos[0], event.pos[1], UNIT, cx, cy)
