"""Create editable Tiled TMX maps and their small procedural tileset."""

import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "assets" / "maps"
TILESET = ROOT / "assets" / "tileset.png"
TILE = 32
WIDTH, HEIGHT = 38, 26


def create_tileset():
    TILESET.parent.mkdir(parents=True, exist_ok=True)
    pygame.init()
    atlas = pygame.Surface((TILE * 5, TILE), pygame.SRCALPHA)
    colors = [(48, 92, 72), (46, 48, 62), (36, 74, 91), (150, 112, 67), (77, 67, 91)]
    for i, base in enumerate(colors):
        tile = pygame.Rect(i * TILE, 0, TILE, TILE)
        atlas.fill(base, tile)
        for y in range(2, TILE, 8):
            for x in range(i * TILE + 2, (i + 1) * TILE, 8):
                shade = 6 + ((x + y + i * 7) % 12)
                pygame.draw.rect(atlas, tuple(min(255, v + shade) for v in base), (x, y, 4, 4))
        if i == 1:
            pygame.draw.rect(atlas, (88, 75, 79), tile, 3)
            pygame.draw.line(atlas, (75, 63, 72), (tile.left + 5, 15), (tile.right - 4, 15), 2)
        elif i == 2:
            pygame.draw.arc(atlas, (69, 132, 145), tile.inflate(-5, -12), 0.2, 2.8, 2)
        elif i == 3:
            pygame.draw.line(atlas, (177, 139, 86), (tile.left + 4, 9), (tile.right - 4, 9), 2)
    pygame.image.save(atlas, TILESET)
    pygame.quit()


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
    grid = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
    # Border walls and level-specific internal obstacles.
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x == 0 or y == 0 or x == WIDTH - 1 or y == HEIGHT - 1:
                grid[y][x] = 1
    for row in range(3, HEIGHT - 3, 5):
        gap = rng.randint(4, WIDTH - 5)
        for x in range(3, WIDTH - 3):
            if abs(x - gap) > 1:
                grid[row][x] = 1
    for _ in range(index + 2):
        cx, cy = rng.randint(5, WIDTH - 6), rng.randint(4, HEIGHT - 5)
        for x in range(cx, min(cx + rng.randint(1, 3), WIDTH - 2)):
            grid[cy][x] = 2 if index % 2 else 1
    # Keep entrances and the central path open.
    for x in range(2, 7):
        for y in range(HEIGHT // 2 - 2, HEIGHT // 2 + 3):
            grid[y][x] = 0
    for x in range(WIDTH - 7, WIDTH - 2):
        for y in range(HEIGHT // 2 - 2, HEIGHT // 2 + 3):
            grid[y][x] = 0
    free_cells = [
        (x, y) for y in range(2, HEIGHT - 2) for x in range(7, WIDTH - 7)
        if grid[y][x] == 0 and abs(y - HEIGHT // 2) + abs(x - 3) > 5
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
    ts = ET.SubElement(root, "tileset", {
        "firstgid": "1", "name": "umbral_tiles", "tilewidth": str(TILE),
        "tileheight": str(TILE), "tilecount": "5", "columns": "5",
    })
    ET.SubElement(ts, "image", {"source": "../tileset.png", "width": "160", "height": "32"})
    for tile_id in (1, 2):
        tile = ET.SubElement(ts, "tile", {"id": str(tile_id)})
        props = ET.SubElement(tile, "properties")
        ET.SubElement(props, "property", {"name": "solid", "type": "bool", "value": "true"})
    layer = ET.SubElement(root, "layer", {
        "id": "1", "name": "Suelo", "width": str(WIDTH), "height": str(HEIGHT),
    })
    data = ET.SubElement(layer, "data", {"encoding": "csv"})
    data.text = "\n" + ",\n".join(",".join(str(tile + 1) for tile in row) for row in grid) + "\n"
    entities = ET.SubElement(root, "objectgroup", {"id": "2", "name": "Entidades"})
    object_id = 1
    tmx_object(entities, object_id, "spawn", 3 * TILE, HEIGHT // 2 * TILE, width=24, height=24)
    object_id += 1
    door_props = {"requires": "switch" if index in (2, 4) else "key" if index in (0, 1, 3) else "clear"}
    tmx_object(entities, object_id, "door", (WIDTH - 3) * TILE, HEIGHT // 2 * TILE, door_props, 28, 36)
    object_id += 1
    if door_props["requires"] == "key":
        x, y = take_cell()
        tmx_object(entities, object_id, "item", x * TILE, y * TILE, {"item": "key", "amount": 1}, 20, 20)
        object_id += 1
    if door_props["requires"] == "switch":
        x, y = take_cell()
        tmx_object(entities, object_id, "switch", x * TILE, y * TILE,
                   {"label": "Sello antiguo"}, 24, 24)
        object_id += 1
    # Five enemy species appear across the campaign, with at least five distinct
    # animated enemy sprites available in the game.
    kinds = ["slime", "wraith", "skeleton", "brute", "mage"]
    for n in range(3 + index):
        kind = kinds[(n + index) % len(kinds)]
        ex, ey = take_cell()
        patrol = ("pingpong", "waypoints", "fsm")[n % 3]
        tmx_object(entities, object_id, "enemy", ex * TILE, ey * TILE, {"kind": kind, "patrol": patrol})
        object_id += 1
    for n, item in enumerate(("medkit", "ammo", "power")):
        x, y = take_cell()
        tmx_object(entities, object_id, "item", x * TILE, y * TILE,
                   {"item": item, "amount": 2 if item == "ammo" else 1}, 20, 20)
        object_id += 1

    MAPS.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(MAPS / ("nivel_%02d.tmx" % (index + 1)), encoding="UTF-8", xml_declaration=True)


def main():
    create_tileset()
    for level in range(5):
        create_level(level)
    print("Tileset y 5 mapas TMX creados en assets/.")


if __name__ == "__main__":
    main()
