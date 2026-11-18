from dataclasses import dataclass

import pygame

from .constants import ITEM_DATA, LEVELS
from .entities import Player
from .maps import LevelMap


@dataclass
class GameStats:
    level: int = 1
    score: int = 0
    deaths: int = 0
    enemies_defeated: int = 0
    enemies_remaining: int = 0
    elapsed: float = 0.0
    lives: int = 3


class Game:
    def __init__(self, audio, difficulty="Normal"):
        self.audio = audio
        self.difficulty_name = difficulty
        self.difficulty = {"Fácil": 0.75, "Normal": 1.0, "Difícil": 1.4}[difficulty]
        self.stats = GameStats()
        self.player = None
        self.level_map = None
        self.level = 1
        self.enemies = []
        self.projectiles = []
        self.drops = []
        self.door = None
        self.switches = []
        self.pickups = []
        self.spawn = (0, 0)
        self.notice_text = ""
        self.notice_timer = 0.0
        self.elapsed = 0.0
        self.ended = None
        self.load_level(1)

    def load_level(self, number):
        self.level = number
        self.stats.level = number
        self.level_map = LevelMap(number, self.difficulty)
        self.spawn = self.level_map.spawn
        if self.player is None:
            self.player = Player(*self.spawn)
            self.player.max_health = 6 if self.difficulty_name == "Fácil" else 5
            self.player.health = self.player.max_health
        else:
            self.player.pos.update(self.spawn)
            self.player.rect.center = self.spawn
            self.player.invulnerable = 1.0
        self.enemies = self.level_map.enemies
        self.stats.enemies_remaining = sum(enemy.alive for enemy in self.enemies)
        self.pickups = self.level_map.pickups
        self.door = self.level_map.door
        self.switches = self.level_map.switches
        self.projectiles.clear()
        self.drops.clear()
        self.audio.play_level(number)
        self.notice("Zona %d: %s" % (number, LEVELS[number - 1][0]), 3)

    def notice(self, text, duration=2.5):
        self.notice_text = text
        self.notice_timer = duration

    def interact(self):
        for switch in self.switches:
            if not switch.active and self.player.rect.inflate(46, 46).colliderect(switch.rect):
                switch.active = True
                self.audio.play("switch")
                self.notice("Mecanismo activado: %s" % switch.label, 2.5)
                return
        if not self.door or not self.player.rect.inflate(42, 42).colliderect(self.door.rect):
            self.notice("No hay nada con qué interactuar.", 1.4)
            return
        remaining = sum(enemy.alive for enemy in self.enemies)
        if remaining:
            self.notice("La puerta está sellada: quedan %d enemigos." % remaining, 2.3)
            return
        if self.door.requires == "key":
            if self.player.inventory["key"] <= 0:
                self.notice("La puerta necesita una llave.", 2)
                return
            self.player.inventory["key"] -= 1
        elif self.door.requires == "switch" and not all(s.active for s in self.switches):
            self.notice("Activa el mecanismo antes de salir.", 2)
            return
        self.audio.play("door")
        if self.level >= len(LEVELS):
            self.ended = True
            self.audio.play("victory")
        else:
            self.stats.score += 250
            self.load_level(self.level + 1)

    def door_ready(self):
        if not self.door or any(enemy.alive for enemy in self.enemies):
            return False
        if self.door.requires == "key":
            return self.player.inventory["key"] > 0
        if self.door.requires == "switch":
            return bool(self.switches) and all(switch.active for switch in self.switches)
        return True

    def collect(self):
        for pickup in self.pickups[:]:
            if self.player.rect.colliderect(pickup.rect):
                item = pickup.item
                if self.player.inventory[item] >= ITEM_DATA[item]["stack"]:
                    self.notice("Inventario lleno: deja espacio para %s." % ITEM_DATA[item]["name"], 1.5)
                    continue
                self.player.inventory[item] = min(ITEM_DATA[item]["stack"], self.player.inventory[item] + pickup.amount)
                self.pickups.remove(pickup)
                self.audio.play("pickup")
                self.notice("%s guardado en el inventario." % ITEM_DATA[item]["name"], 2)
                self.stats.score += 25
        for drop in self.drops[:]:
            if self.player.rect.colliderect(drop.rect):
                self.player.inventory[drop.item] = min(ITEM_DATA[drop.item]["stack"], self.player.inventory[drop.item] + drop.amount)
                self.drops.remove(drop)
                self.audio.play("pickup")
                self.notice("Recogiste: %s." % ITEM_DATA[drop.item]["name"], 1.5)

    def drop_selected(self):
        item = tuple(ITEM_DATA)[self.player.selected]
        if self.player.inventory[item] <= 0:
            self.notice("No hay objeto para descartar.", 1.6)
            return
        self.player.inventory[item] -= 1
        from .entities import Pickup
        rect = pygame.Rect(self.player.rect.centerx - 10, self.player.rect.centery - 10, 20, 20)
        self.pickups.append(Pickup(rect, item, 1))
        self.notice("%s descartado." % ITEM_DATA[item]["name"], 1.6)

    def finish(self, victory):
        self.ended = victory
        self.audio.play("victory" if victory else "gameover")

    def update(self, dt, keys, actions, control_scheme="WASD"):
        if self.ended is not None:
            return
        dt = min(dt, 0.05)
        self.elapsed += dt
        self.stats.elapsed = self.elapsed
        self.stats.lives = self.player.lives
        self.notice_timer = max(0.0, self.notice_timer - dt)
        self.player.anim_time += dt
        self.player.invulnerable = max(0.0, self.player.invulnerable - dt)
        self.player.attack_timer = max(0.0, self.player.attack_timer - dt)
        self.player.shoot_timer = max(0.0, self.player.shoot_timer - dt)
        self.player.attack_cooldown = max(0.0, self.player.attack_cooldown - dt)
        self.player.shoot_cooldown = max(0.0, self.player.shoot_cooldown - dt)
        self.player.jump_timer = max(0.0, self.player.jump_timer - dt)
        self.player.jump_cooldown = max(0.0, self.player.jump_cooldown - dt)
        self.player.power_timer = max(0.0, self.player.power_timer - dt)

        if control_scheme == "Flechas":
            move = pygame.Vector2(
                int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]),
                int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP]),
            )
        else:
            move = pygame.Vector2(
                int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
                int(keys[pygame.K_s]) - int(keys[pygame.K_w]),
            )
        if move.x:
            self.player.facing = 1 if move.x > 0 else -1
        self.player.move(move, dt, self)
        if actions.get("jump"):
            self.player.jump()
        if actions.get("attack"):
            self.player.attack(self)
        if actions.get("shoot"):
            self.player.shoot(self)
        if actions.get("interact"):
            self.interact()
        if actions.get("use"):
            self.player.use_item(self)
        if actions.get("drop"):
            self.drop_selected()
        if self.player.invulnerable <= 0:
            self.player.state = (
                "attack" if self.player.attack_timer else
                "shoot" if self.player.shoot_timer else
                "jump" if self.player.jump_timer else
                "walk" if move.length_squared() else
                "idle"
            )

        self.enemies = [enemy for enemy in self.enemies if enemy.update(dt, self)]
        self.stats.enemies_remaining = sum(enemy.alive for enemy in self.enemies)
        self.projectiles = [projectile for projectile in self.projectiles if projectile.update(dt, self)]
        self.collect()

    def draw(self, surface, camera):
        self.level_map.draw(surface, camera)
        self.door.draw(surface, camera, self.door_ready())
        for switch in self.switches:
            switch.draw(surface, camera)
        for pickup in self.pickups:
            nearby = self.player.pos.distance_to(pickup.rect.center) < 132
            pickup.draw(surface, camera, nearby)
        for drop in self.drops:
            nearby = self.player.pos.distance_to(drop.rect.center) < 132
            drop.draw(surface, camera, nearby)
        for projectile in self.projectiles:
            projectile.draw(surface, camera)
        for enemy in self.enemies:
            enemy.draw(surface, camera)
        self.player.draw(surface, camera)
