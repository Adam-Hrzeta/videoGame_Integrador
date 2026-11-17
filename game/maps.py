import random

import pygame
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from .constants import MAPS_DIR, TILE_SIZE
from .entities import Door, Enemy, Pickup, Switch


class LevelMap:
    def __init__(self, number, difficulty=1.0):
        self.number = number
        self.rng = random.Random(901 + number)
        path = MAPS_DIR / ("nivel_%02d.tmx" % number)
        self.tmx = load_pygame(str(path), pixelalpha=True)
        self.width = self.tmx.width * self.tmx.tilewidth
        self.height = self.tmx.height * self.tmx.tileheight
        self.world = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.solids = []
        for layer in self.tmx.visible_layers:
            if isinstance(layer, TiledTileLayer):
                for x, y, gid in layer:
                    image = self.tmx.get_tile_image_by_gid(gid)
                    if image:
                        self.world.blit(image, (x * TILE_SIZE, y * TILE_SIZE))
                    props = self.tmx.get_tile_properties_by_gid(gid) or {}
                    if props.get("solid"):
                        self.solids.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        self.spawn = (TILE_SIZE * 3 + TILE_SIZE // 2, self.height // 2)
        self.door = None
        self.switches = []
        self.enemies = []
        self.pickups = []
        for obj in self.tmx.objects:
            rect = pygame.Rect(round(obj.x), round(obj.y), max(1, round(obj.width)), max(1, round(obj.height)))
            props = obj.properties
            if obj.type == "spawn":
                self.spawn = rect.center
            elif obj.type == "door":
                self.door = Door(rect, props.get("requires", "clear"))
            elif obj.type == "switch":
                self.switches.append(Switch(rect, props.get("label", "Mecanismo")))
            elif obj.type == "enemy":
                self.enemies.append(Enemy(rect.centerx, rect.centery, props.get("kind", "slime"),
                                          props.get("patrol", "pingpong"), difficulty))
            elif obj.type == "item":
                self.pickups.append(Pickup(rect, props.get("item", "ammo"), props.get("amount", 1)))

    def collides(self, rect):
        return any(rect.colliderect(wall) for wall in self.solids)

    def draw(self, surface, camera):
        area = pygame.Rect(round(camera.x), round(camera.y), surface.get_width(), surface.get_height())
        surface.blit(self.world, (0, 0), area)
