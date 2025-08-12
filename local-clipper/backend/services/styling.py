"""
Palettes, safe-margins, overlays/icons, ASS style generation from preset.
"""
# Implement styling logic here

import os
import json

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
PRESETS_PATH = os.path.join(FRONTEND_DIR, 'presets.json')

SAFE_MARGINS = {
    "top": 80,
    "bottom": 80,
    "left": 40,
    "right": 40
}

OVERLAYS = {
    "star": "★",
    "fire": "🔥",
    "like": "👍"
}

PALETTES = {
    "clean": {"primary": "#fff", "outline": "#000"},
    "mrbeast": {"primary": "#00f0ff", "outline": "#ff00ff"},
    "karaoke": {"primary": "#fff700", "outline": "#000"},
    "bold-outline": {"primary": "#fff", "outline": "#000", "shadow": "#333"},
    "emoji-pop": {"primary": "#fff", "outline": "#000"},
    "minimal": {"primary": "#fff", "outline": "#222"},
    "high-contrast": {"primary": "#fff", "outline": "#000"},
    "shadowed": {"primary": "#fff", "outline": "#000", "shadow": "#000"}
}

def get_style_preset(preset_name: str) -> dict:
    if os.path.exists(PRESETS_PATH):
        with open(PRESETS_PATH, encoding='utf-8') as f:
            presets = json.load(f)
        return presets.get(preset_name, presets.get("clean", {}))
    return PALETTES.get(preset_name, PALETTES["clean"])

def generate_ass_style(preset_name: str) -> str:
    style = get_style_preset(preset_name)
    # Минимальный ASS стиль
    return f"Style: Default,Arial,48,{style.get('primary','#fff')},{style.get('outline','#000')},{style.get('shadow','#000')},0,0,1,3,1,2,10,10,10,1"
