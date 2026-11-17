from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MAPS_DIR = ASSETS / "maps"
TILE_SIZE = 32
DEFAULT_SIZE = (960, 640)
MIN_SIZE = (800, 600)
FPS = 60

LEVELS = (
    ("El Bosque Velado", "Encuentra la llave y alcanza la puerta."),
    ("Las Catacumbas", "Sobrevive a los guardianes y recoge la llave."),
    ("La Forja Hundida", "Activa el interruptor para abrir el paso."),
    ("El Desierto de Ceniza", "Busca la llave entre las dunas."),
    ("El Corazón del Umbral", "Activa el sello y escapa."),
)

ENEMY_DATA = {
    "slime": {"name": "Baba", "color": (91, 205, 119), "hp": 2, "speed": 74, "damage": 1},
    "wraith": {"name": "Espectro", "color": (106, 192, 230), "hp": 2, "speed": 96, "damage": 1},
    "skeleton": {"name": "Esqueleto", "color": (230, 219, 180), "hp": 3, "speed": 70, "damage": 1},
    "brute": {"name": "Bruto", "color": (211, 105, 78), "hp": 5, "speed": 52, "damage": 2},
    "mage": {"name": "Hechicero", "color": (180, 119, 234), "hp": 3, "speed": 56, "damage": 1},
}

ITEM_DATA = {
    "medkit": {"name": "Botiquín", "color": (239, 93, 107), "stack": 5},
    "ammo": {"name": "Munición", "color": (239, 194, 80), "stack": 99},
    "key": {"name": "Llave", "color": (255, 219, 102), "stack": 9},
    "power": {"name": "Esencia", "color": (96, 214, 224), "stack": 5},
}
