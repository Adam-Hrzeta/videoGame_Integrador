"""Build five distinct Tiled maps and their artwork from the included source atlases."""

import math
import random
import xml.etree.ElementTree as ET
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "assets" / "maps"
TILESETS = ROOT / "assets" / "tilesets"
SOURCE = TILESETS / "source"
TILE = 32
WIDTH, HEIGHT = 38, 26

THEMES = {
    1: {"name": "bosque", "atlas": "forest", "base": 1, "wall": 62, "kind": "forest"},
    2: {"name": "desierto", "atlas": "desert", "base": 16, "wall": 10, "kind": "desert"},
    3: {"name": "catacumbas", "atlas": "dungeon", "base": 1, "wall": 49, "kind": "dungeon"},
    4: {"name": "pantano", "atlas": "swamp", "base": 1, "wall": 62, "kind": "swamp"},
    5: {"name": "umbral", "atlas": "umbral", "base": 1, "wall": 49, "kind": "final"},
}


def build_atlas(source_name, output_name, columns, rows, source_tile, spacing=0, tint=None):
    source = pygame.image.load(str(SOURCE / source_name)).convert_alpha()
    atlas = pygame.Surface((columns * TILE, rows * TILE), pygame.SRCALPHA)
    for row in range(rows):
        for column in range(columns):
            source_rect = pygame.Rect(
                column * (source_tile + spacing),
                row * (source_tile + spacing),
                source_tile,
                source_tile,
            )
            tile = source.subsurface(source_rect).copy()
            tile = pygame.transform.scale(tile, (TILE, TILE))
            if tint:
                tile.fill(tint, special_flags=pygame.BLEND_RGBA_MULT)
            atlas.blit(tile, (column * TILE, row * TILE))
    pygame.image.save(atlas, TILESETS / (output_name + ".png"))


def build_tilesets():
    TILESETS.mkdir(parents=True, exist_ok=True)
    build_atlas("overworld_tileset_grass.png", "forest", 12, 21, 16)
    build_atlas("tmw_desert_spacing.png", "desert", 8, 6, 33)
    build_atlas("kenney_tiny_dungeon.png", "dungeon", 12, 11, 16, spacing=1)
    build_atlas("overworld_tileset_grass.png", "swamp", 12, 21, 16, tint=(108, 157, 145, 255))
    build_atlas("kenney_tiny_dungeon.png", "umbral", 12, 11, 16, spacing=1,
                tint=(160, 112, 184, 255))

    definitions = (
        ("forest", 12, 21, 252, 61),
        ("desert", 8, 6, 48, 9),
        ("dungeon", 12, 11, 132, 48),
        ("swamp", 12, 21, 252, 61),
        ("umbral", 12, 11, 132, 48),
    )
    for name, columns, rows, count, solid_id in definitions:
        tileset = ET.Element("tileset", {
            "version": "1.10", "tiledversion": "1.10.2", "name": name,
            "tilewidth": str(TILE), "tileheight": str(TILE),
            "tilecount": str(count), "columns": str(columns),
        })
        ET.SubElement(tileset, "image", {
            "source": name + ".png", "width": str(columns * TILE),
            "height": str(rows * TILE),
        })
        tile = ET.SubElement(tileset, "tile", {"id": str(solid_id)})
        properties = ET.SubElement(tile, "properties")
        ET.SubElement(properties, "property", {
            "name": "solid", "type": "bool", "value": "true",
        })
        tree = ET.ElementTree(tileset)
        ET.indent(tree, space="  ")
        tree.write(TILESETS / (name + ".tsx"), encoding="UTF-8", xml_declaration=True)


def stamp_disk(grid, blocked, cx, cy, radius, tile_id):
    for y in range(max(1, cy - radius), min(HEIGHT - 1, cy + radius + 1)):
        for x in range(max(1, cx - radius), min(WIDTH - 1, cx + radius + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                grid[y][x] = tile_id
                blocked[y][x] = True


def create_layout(index, theme, rng):
    grid = [[theme["base"] for _ in range(WIDTH)] for _ in range(HEIGHT)]
    blocked = [[False for _ in range(WIDTH)] for _ in range(HEIGHT)]
    wall = theme["wall"]

    if theme["kind"] == "forest":
        for y in range(HEIGHT):
            for x in range(WIDTH):
                inside_island = ((x - 19) / 17) ** 2 + ((y - 13) / 11) ** 2 < 1
                if not inside_island:
                    grid[y][x] = wall
                    blocked[y][x] = True
        stamp_disk(grid, blocked, 12, 7, 2, wall)
        stamp_disk(grid, blocked, 26, 19, 3, wall)
        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):
                if not blocked[y][x] and rng.random() < 0.18:
                    grid[y][x] = rng.choice((2, 3, 4, 39, 40, 41))

    elif theme["kind"] == "desert":
        for x in range(WIDTH):
            grid[0][x] = grid[HEIGHT - 1][x] = wall
            blocked[0][x] = blocked[HEIGHT - 1][x] = True
        for y in range(HEIGHT):
            grid[y][0] = grid[y][WIDTH - 1] = wall
            blocked[y][0] = blocked[y][WIDTH - 1] = True
        for column, gap in ((9, 5), (16, 19), (24, 8), (31, 18)):
            for y in range(2, HEIGHT - 2):
                if abs(y - gap) > 2:
                    grid[y][column] = wall
                    blocked[y][column] = True
            for y in range(max(2, gap - 2), min(HEIGHT - 2, gap + 3)):
                grid[y][column] = 15
                blocked[y][column] = False
        for _ in range(16):
            x, y = rng.randrange(3, WIDTH - 3), rng.randrange(2, HEIGHT - 2)
            if abs(y - 13) > 4 and not blocked[y][x]:
                grid[y][x] = rng.choice((32, 34, 39, 40, 47))

    elif theme["kind"] == "dungeon":
        for x in range(WIDTH):
            grid[0][x] = grid[HEIGHT - 1][x] = wall
            blocked[0][x] = blocked[HEIGHT - 1][x] = True
        for y in range(HEIGHT):
            grid[y][0] = grid[y][WIDTH - 1] = wall
            blocked[y][0] = blocked[y][WIDTH - 1] = True
        for y, gap in ((6, 7), (12, 28), (19, 13)):
            for x in range(1, WIDTH - 1):
                if abs(x - gap) > 2:
                    grid[y][x] = wall
                    blocked[y][x] = True
        for x, gap in ((12, 10), (25, 16)):
            for y in range(1, HEIGHT - 1):
                if abs(y - gap) > 2:
                    grid[y][x] = wall
                    blocked[y][x] = True
        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):
                if not blocked[y][x] and rng.random() < 0.1:
                    grid[y][x] = rng.choice((2, 3, 4, 7, 8))
        for x in range(1, WIDTH - 1):
            for y in range(HEIGHT // 2 - 1, HEIGHT // 2 + 2):
                grid[y][x] = theme["base"]
                blocked[y][x] = False

    elif theme["kind"] == "swamp":
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if x in (0, WIDTH - 1) or y in (0, HEIGHT - 1):
                    grid[y][x] = wall
                    blocked[y][x] = True
        stamp_disk(grid, blocked, 9, 7, 3, wall)
        stamp_disk(grid, blocked, 20, 19, 4, wall)
        stamp_disk(grid, blocked, 29, 7, 3, wall)
        for x in range(5, WIDTH - 5):
            stream_y = 13 + round(3 * math.sin(x * 0.38))
            if abs(stream_y - 13) > 1:
                grid[stream_y][x] = wall
                blocked[stream_y][x] = True
        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):
                if not blocked[y][x] and rng.random() < 0.2:
                    grid[y][x] = rng.choice((2, 3, 4, 39, 40, 41))

    else:
        for x in range(WIDTH):
            grid[0][x] = grid[HEIGHT - 1][x] = wall
            blocked[0][x] = blocked[HEIGHT - 1][x] = True
        for y in range(HEIGHT):
            grid[y][0] = grid[y][WIDTH - 1] = wall
            blocked[y][0] = blocked[y][WIDTH - 1] = True
        cx, cy = WIDTH // 2, HEIGHT // 2
        for y in range(3, HEIGHT - 3):
            for x in range(3, WIDTH - 3):
                distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if 6.0 <= distance <= 8.0 and not (abs(x - cx) < 2 or abs(y - cy) < 2):
                    grid[y][x] = wall
                    blocked[y][x] = True
        for y in range(2, HEIGHT - 2):
            if y not in range(cy - 1, cy + 2):
                grid[y][cx] = wall
                blocked[y][cx] = True
        for x in range(2, WIDTH - 2):
            if (x not in range(cx - 1, cx + 2)
                    and x not in range(2, 6)
                    and x not in range(WIDTH - 6, WIDTH - 2)):
                grid[cy][x] = wall
                blocked[cy][x] = True
        for x in range(1, WIDTH - 1):
            for y in range(cy - 1, cy + 2):
                grid[y][x] = theme["base"]
                blocked[y][x] = False
        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):
                if not blocked[y][x] and rng.random() < 0.1:
                    grid[y][x] = rng.choice((2, 3, 4, 7, 8))

    return grid, blocked


def tmx_object(group, object_id, kind, x, y, props=None, width=28, height=28):
    obj = ET.SubElement(group, "object", {
        "id": str(object_id), "name": kind, "type": kind,
        "x": str(x), "y": str(y), "width": str(width), "height": str(height),
    })
    if props:
        properties = ET.SubElement(obj, "properties")
        for key, value in props.items():
            ET.SubElement(properties, "property", {"name": key, "value": str(value)})


def create_level(index):
    rng = random.Random(4200 + index)
    theme = THEMES[index]
    grid, blocked = create_layout(index, theme, rng)
    free_cells = [
        (x, y) for y in range(2, HEIGHT - 2) for x in range(5, WIDTH - 5)
        if not blocked[y][x] and abs(y - HEIGHT // 2) + abs(x - 3) > 6
    ]
    rng.shuffle(free_cells)
    occupied = set()

    def take_cell():
        while free_cells:
            cell = free_cells.pop()
            if cell not in occupied:
                occupied.add(cell)
                return cell
        raise RuntimeError("No quedan casillas libres para colocar entidades.")

    root = ET.Element("map", {
        "version": "1.10", "tiledversion": "1.10.2", "orientation": "orthogonal",
        "renderorder": "right-down", "width": str(WIDTH), "height": str(HEIGHT),
        "tilewidth": str(TILE), "tileheight": str(TILE), "infinite": "0",
        "nextlayerid": "3", "nextobjectid": "40",
    })
    ET.SubElement(root, "tileset", {
        "firstgid": "1", "source": "../tilesets/%s.tsx" % theme["atlas"],
    })
    for layer_id, name, data_grid, visible in (
        (1, "Suelo", grid, "1"),
        (2, "Colisiones", [[theme["wall"] if solid else 0 for solid in row] for row in blocked], "0"),
    ):
        layer = ET.SubElement(root, "layer", {
            "id": str(layer_id), "name": name, "width": str(WIDTH), "height": str(HEIGHT),
            "visible": visible,
        })
        data = ET.SubElement(layer, "data", {"encoding": "csv"})
        data.text = "\n" + ",\n".join(",".join(str(tile) for tile in row) for row in data_grid) + "\n"

    entities = ET.SubElement(root, "objectgroup", {"id": "3", "name": "Entidades"})
    tmx_object(entities, 1, "spawn", 3 * TILE, HEIGHT // 2 * TILE, width=24, height=24)
    door_props = {"requires": "switch" if index in (3, 5) else "key"}
    tmx_object(entities, 2, "door", (WIDTH - 3) * TILE, HEIGHT // 2 * TILE, door_props, 28, 36)
    object_id = 3
    if door_props["requires"] == "key":
        x, y = take_cell()
        tmx_object(entities, object_id, "item", x * TILE, y * TILE, {"item": "key", "amount": 1}, 20, 20)
        object_id += 1
    else:
        x, y = take_cell()
        tmx_object(entities, object_id, "switch", x * TILE, y * TILE,
                   {"label": "Sello antiguo"}, 24, 24)
        object_id += 1

    kinds = ["slime", "wraith", "skeleton", "brute", "mage"]
    patrols = ("pingpong", "waypoints", "fsm")
    for number in range(3 + index):
        kind = kinds[(number + index - 1) % len(kinds)]
        x, y = take_cell()
        tmx_object(entities, object_id, "enemy", x * TILE, y * TILE,
                   {"kind": kind, "patrol": patrols[number % len(patrols)]})
        object_id += 1
    for item in ("medkit", "ammo", "power"):
        x, y = take_cell()
        tmx_object(entities, object_id, "item", x * TILE, y * TILE,
                   {"item": item, "amount": 2 if item == "ammo" else 1}, 20, 20)
        object_id += 1

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(MAPS / ("nivel_%02d.tmx" % index), encoding="UTF-8", xml_declaration=True)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    build_tilesets()
    MAPS.mkdir(parents=True, exist_ok=True)
    for level in THEMES:
        create_level(level)
    pygame.quit()
    print("Cinco escenarios temáticos y sus tilesets Tiled creados en assets/.")


if __name__ == "__main__":
    main()
