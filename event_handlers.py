# ============================================================
# event_handlers.py — Extracted Event Handlers for Dead World
# ============================================================
# Splits the dense main() event loop into focused handler functions.
# Each handler accesses game state via a module reference (_game).

import pygame
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
# KEYDOWN — PAUSE STATE
# ========================
def handle_keydown_pause(event):
    """Keydown events while in PAUSED state."""
    if event.key == pygame.K_UP:
        _game.pause_selected_index = (_game.pause_selected_index - 1) % len(_game.pause_buttons)
    elif event.key == pygame.K_DOWN:
        _game.pause_selected_index = (_game.pause_selected_index + 1) % len(_game.pause_buttons)
    elif event.key == pygame.K_RETURN:
        _game.pause_buttons[_game.pause_selected_index].action()


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


