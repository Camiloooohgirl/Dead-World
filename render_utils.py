# ============================================================
# render_utils.py — Scaling & Text Rendering Helpers for Dead World
# ============================================================
# Extracted from the main game file to reduce redundancy.
# Import with: from render_utils import *
#
# NOTE: This module needs a reference to the pygame screen surface.
# Call init_render(screen_surface) once after creating the display.

import pygame
import math
from config import REFERENCE_WIDTH, REFERENCE_HEIGHT, TERMINAL_FONT_NAME

# ========================
# MODULE STATE
# ========================
_screen = None           # Set via init_render()
_font_cache = {}
_last_scale_factor = None


def init_render(screen_surface):
    """Call once after pygame.display.set_mode() to provide the screen reference."""
    global _screen
    _screen = screen_surface


# ========================
# SCALING FUNCTIONS
# ========================

def get_scale_factor():
    """Berechnet einheitlichen Skalierungsfaktor basierend auf Fensterbreite"""
    sx = _screen.get_width() / REFERENCE_WIDTH
    sy = _screen.get_height() / REFERENCE_HEIGHT
    return min(sx, sy)


def scale(value):
    """Skaliert einen Wert proportional zur aktuellen Auflösung"""
    return int(value * get_scale_factor())


def scale_x(value):
    """Skaliert horizontal (für Positionen die sich mit Breite ändern)"""
    return int(value * _screen.get_width() / REFERENCE_WIDTH)


def scale_y(value):
    """Skaliert vertikal (für Positionen die sich mit Höhe ändern)"""
    return int(value * _screen.get_height() / REFERENCE_HEIGHT)


def scale_pos(x, y):
    """Skaliert eine Position und zentriert bei abweichendem Seitenverhältnis"""
    factor = get_scale_factor()
    offset_x = (_screen.get_width() - REFERENCE_WIDTH * factor) / 2
    offset_y = (_screen.get_height() - REFERENCE_HEIGHT * factor) / 2
    return (int(x * factor + offset_x), int(y * factor + offset_y))


def get_scaled_font(base_size):
    """Gibt skalierte Schrift zurück (gecacht für Performance)"""
    global _last_scale_factor

    current_factor = get_scale_factor()
    if _last_scale_factor != current_factor:
        _font_cache.clear()
        _last_scale_factor = current_factor

    scaled_size = max(12, scale(base_size))
    if scaled_size not in _font_cache:
        _font_cache[scaled_size] = pygame.font.SysFont(TERMINAL_FONT_NAME, scaled_size)
    return _font_cache[scaled_size]


def clear_font_cache():
    """Leert den Font-Cache bei manueller Auflösungsänderung"""
    global _last_scale_factor
    _font_cache.clear()
    _last_scale_factor = None


# ========================
# TEXT RENDERING HELPERS
# ========================

def draw_text(surface, text, pos, color, font, center=False):
    """Render text and blit in one call. If center=True, pos is the center point."""
    surf = font.render(text, True, color)
    if center:
        rect = surf.get_rect(center=pos)
        surface.blit(surf, rect)
    else:
        surface.blit(surf, pos)
    return surf


def draw_text_line(surface, text, x, y, color, font):
    """Simple left-aligned text rendering (used in game terminal)."""
    if text.strip():  # Skip empty lines to avoid rendering artifacts
        surf = font.render(text, True, color)
        surface.blit(surf, (x, y))
