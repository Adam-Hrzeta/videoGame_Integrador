import math
from functools import lru_cache
from pathlib import Path

import pygame

from .constants import ENEMY_DATA, ITEM_DATA, TILE_SIZE
from .item_icons import draw_item_icon, draw_item_label

PLAYER_FRAME_SIZE = (96, 96)
ENEMY_FRAME_SIZE = (72, 72)
SPRITE_ASSETS = Path(__file__).resolve().parents[1] / "assets" / "sprites"
PLAYER_ASSETS = SPRITE_ASSETS / "player" / "samurai"
PLAYER_ANIMATIONS = {
    "idle": "Idle",
    "walk": "Run",
    "attack": "Attack_1",
    "shoot": "Attack_2",
    "jump": "Jump",
    "hurt": "Hurt",
    "death": "Dead",
}
ENEMY_SPRITES = {
    "slime": "skeleton-archer",
    "wraith": "lightning-mage",
    "skeleton": "skeleton-warrior",
    "brute": "skeleton-spearman",
    "mage": "fire-wizard",
}
ENEMY_ANIMATIONS = {
    "idle": "Idle",
    "walk": "Run",
    "attack": "Attack_1",
    "shoot": "Attack_2",
    "hurt": "Hurt",
    "death": "Dead",
}


@lru_cache(maxsize=64)
def _sprite_frames(folder, name, frame_size, output_size):
    sheet = pygame.image.load(str(Path(folder) / (name + ".png"))).convert_alpha()
    frame_width, frame_height = frame_size
    if sheet.get_height() != frame_height or sheet.get_width() % frame_width:
        raise ValueError("La hoja de animación tiene dimensiones inesperadas: %s.png" % name)
    return tuple(
        pygame.transform.scale(
            sheet.subsurface((x, 0, frame_width, frame_height)),
            output_size,
        )
        for x in range(0, sheet.get_width(), frame_width)
    )


def player_frames(state):
    name = PLAYER_ANIMATIONS.get(state, PLAYER_ANIMATIONS["idle"])
    return _sprite_frames(str(PLAYER_ASSETS), name, (128, 128), PLAYER_FRAME_SIZE)


def enemy_frames(kind, state):
    folder = SPRITE_ASSETS / "enemies" / ENEMY_SPRITES[kind]
    name = ENEMY_ANIMATIONS.get(state, ENEMY_ANIMATIONS["idle"])
    if not (folder / (name + ".png")).is_file():
        name = "Walk" if name == "Run" else "Attack_1"
    return _sprite_frames(str(folder), name, (128, 128), ENEMY_FRAME_SIZE)


class Projectile:
    def __init__(self, x, y, direction, friendly, damage=1):
        self.pos = pygame.Vector2(x, y)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared():
            self.direction = self.direction.normalize()
        self.friendly = friendly
        self.damage = damage
        self.speed = 360 if friendly else 220
        self.rect = pygame.Rect(round(x - 5), round(y - 5), 10, 10)
        self.life = 2.4
        self.color = (110, 231, 245) if friendly else (224, 107, 196)

    def update(self, dt, game):
        self.life -= dt
        self.pos += self.direction * self.speed * dt
        self.rect.center = round(self.pos.x), round(self.pos.y)
        if self.life <= 0 or game.level_map.collides(self.rect):
            return False
        if self.friendly:
            for enemy in game.enemies:
                if enemy.alive and enemy.rect.colliderect(self.rect):
                    enemy.take_damage(self.damage, game)
                    return False
        elif not game.player.invulnerable and game.player.rect.colliderect(self.rect):
            game.player.take_damage(self.damage, game)
            return False
        return True

    def draw(self, surface, camera):
        pygame.draw.circle(surface, self.color, (round(self.rect.centerx - camera.x), round(self.rect.centery - camera.y)), 5)
        pygame.draw.circle(surface, (245, 244, 226), (round(self.rect.centerx - camera.x), round(self.rect.centery - camera.y)), 2)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(0, 0, 25, 30)
        self.rect.center = round(x), round(y)
        self.facing = 1
        self.state = "idle"
        self.anim_time = 0.0
        self.jump_timer = 0.0
        self.jump_cooldown = 0.0
        self.health = 5
        self.max_health = 5
        self.lives = 3
        self.invulnerable = 0.0
        self.attack_timer = 0.0
        self.attack_cooldown = 0.0
        self.shoot_timer = 0.0
        self.shoot_cooldown = 0.0
        self.power_timer = 0.0
        self.ammo = 8
        self.inventory = {name: 0 for name in ITEM_DATA}
        self.selected = 0
        self.speed = 190

    def move(self, vector, dt, game):
        if not vector.length_squared():
            return
        vector = vector.normalize() * self.speed * (1.3 if self.power_timer > 0 else 1.0) * dt
        self.pos.x += vector.x
        self.rect.centerx = round(self.pos.x)
        if game.level_map.collides(self.rect):
            self.pos.x -= vector.x
            self.rect.centerx = round(self.pos.x)
        self.pos.y += vector.y
        self.rect.centery = round(self.pos.y)
        if game.level_map.collides(self.rect):
            self.pos.y -= vector.y
            self.rect.centery = round(self.pos.y)

    def attack(self, game):
        if self.attack_cooldown > 0:
            return
        self.attack_cooldown = 0.42
        self.attack_timer = 0.22
        hit = self.rect.inflate(64, 54)
        if self.facing > 0:
            hit.left = self.rect.right - 1
        else:
            hit.right = self.rect.left + 1
        for enemy in game.enemies:
            if enemy.alive and hit.colliderect(enemy.rect):
                enemy.take_damage(2, game)
        game.audio.play("swing")

    def shoot(self, game):
        if self.shoot_cooldown > 0:
            return
        if self.ammo <= 0:
            game.notice("Sin munición. Busca cajas de suministros.", 2)
            return
        self.ammo -= 1
        self.shoot_cooldown = 0.3
        self.shoot_timer = 0.2
        self.state = "shoot"
        game.projectiles.append(Projectile(self.rect.centerx + self.facing * 14, self.rect.centery, (self.facing, 0), True, 2))
        game.audio.play("shot")

    def jump(self):
        if self.jump_cooldown > 0:
            return
        self.jump_timer = 0.45
        self.jump_cooldown = 0.7

    def take_damage(self, amount, game):
        if self.invulnerable > 0:
            return
        self.health -= amount
        self.invulnerable = 1.0
        self.state = "hurt"
        game.audio.play("hurt")
        if self.health <= 0:
            self.lives -= 1
            game.stats.deaths += 1
            game.stats.lives = self.lives
            self.ammo = max(0, self.ammo - 2)
            for item in ("power", "medkit", "ammo"):
                if self.inventory[item] > 0:
                    self.inventory[item] -= 1
                    break
            if self.lives <= 0:
                self.state = "death"
                game.finish(False)
            else:
                self.health = self.max_health
                self.pos.update(game.spawn)
                self.rect.center = game.spawn
                game.notice("Has reaparecido. Perdiste 2 municiones.", 3)

    def use_item(self, game):
        item = tuple(ITEM_DATA)[self.selected]
        if self.inventory[item] <= 0:
            game.notice("Ese espacio del inventario está vacío.", 2)
            return
        if item == "medkit":
            if self.health >= self.max_health:
                game.notice("Ya tienes toda la vida.", 2)
                return
            self.health = min(self.max_health, self.health + 3)
        elif item == "ammo":
            self.ammo += self.inventory[item] * 3
        elif item == "power":
            self.power_timer = 8.0
            self.invulnerable = max(self.invulnerable, 2.0)
        else:
            game.notice("La llave se usa al interactuar con una puerta.", 2)
            return
        self.inventory[item] = 0
        game.audio.play("pickup")
        game.notice("%s utilizado." % ITEM_DATA[item]["name"], 2)

    def draw(self, surface, camera):
        frames = player_frames(self.state)
        fps = {"idle": 6, "walk": 12, "attack": 16, "shoot": 16, "jump": 14}.get(self.state, 12)
        if self.state == "death":
            frame_index = len(frames) - 1
        else:
            frame_index = int(self.anim_time * fps) % len(frames)
        image = frames[frame_index].copy()
        if self.state == "hurt":
            image.fill((255, 128, 128, 255), special_flags=pygame.BLEND_RGBA_MULT)
        elif self.state == "death":
            image.fill((150, 150, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
        if self.facing < 0:
            image = pygame.transform.flip(image, True, False)
        jump_progress = 1 - self.jump_timer / 0.45 if self.state == "jump" else 0
        jump_offset = round(math.sin(jump_progress * math.pi) * 18)
        dest = image.get_rect(midbottom=(
            round(self.rect.centerx - camera.x),
            round(self.rect.bottom - camera.y - jump_offset),
        ))
        if self.invulnerable > 0 and int(self.anim_time * 18) % 2:
            image.set_alpha(110)
        surface.blit(image, dest)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind, patrol="pingpong", difficulty=1.0):
        super().__init__()
        self.kind = kind if kind in ENEMY_DATA else "slime"
        data = ENEMY_DATA[self.kind]
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(0, 0, 26 if self.kind != "brute" else 34, 28 if self.kind != "brute" else 36)
        self.rect.center = round(x), round(y)
        self.patrol = patrol
        self.speed = data["speed"] * (0.9 + difficulty * 0.1)
        self.health = max(1, round(data["hp"] * difficulty))
        self.max_health = self.health
        self.damage = data["damage"] if difficulty >= 1.5 else 1
        self.alive = True
        self.facing = -1
        self.state = "idle"
        self.anim_time = 0.0
        self.hit_flash = 0.0
        self.cooldown = 0.0
        self.state_time = 0.0
        self.patrol_direction = 1
        self.patrol_origin = pygame.Vector2(x, y)
        self.ai_state = "patrol"
        self.waypoint = 0
        self.death_timer = 0.0

    def take_damage(self, amount, game):
        if not self.alive:
            return
        self.health -= amount
        self.hit_flash = 0.15
        self.state = "hurt"
        self.state_time = 0.0
        if self.health <= 0:
            self.alive = False
            self.state = "death"
            self.state_time = 0.0
            self.death_timer = 0.45
            game.stats.score += 100
            game.stats.enemies_defeated += 1
            game.stats.enemies_remaining = sum(enemy.alive for enemy in game.enemies)
            game.audio.play("enemy_dead")
            game.notice("Enemigo derrotado: +100 puntos", 1.5)
            if game.level_map.rng.random() < 0.18:
                game.drops.append(Drop(self.rect.centerx, self.rect.centery, "ammo", 1))

    def update(self, dt, game):
        self.anim_time += dt
        self.state_time += dt
        self.cooldown = max(0.0, self.cooldown - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        if not self.alive:
            self.death_timer -= dt
            return self.death_timer > 0
        previous_state = self.state
        player = game.player
        delta = player.pos - self.pos
        distance = delta.length()
        if self.patrol == "fsm":
            if distance < 240:
                self.ai_state = "chase"
            elif self.health <= max(1, self.max_health // 3):
                self.ai_state = "retreat"
            else:
                self.ai_state = "patrol"
            if self.ai_state == "chase" and distance > 36:
                direction = delta.normalize()
            elif self.ai_state == "retreat" and distance < 200:
                direction = -delta.normalize() if distance else pygame.Vector2()
            else:
                direction = pygame.Vector2(self.patrol_direction, 0)
        elif self.patrol == "waypoints" and distance >= 32:
            points = (
                self.patrol_origin + pygame.Vector2(-68, -34),
                self.patrol_origin + pygame.Vector2(70, -30),
                self.patrol_origin + pygame.Vector2(62, 54),
                self.patrol_origin + pygame.Vector2(-66, 50),
            )
            target = points[self.waypoint % len(points)]
            if self.pos.distance_to(target) < 10:
                self.waypoint = (self.waypoint + 1) % len(points)
                target = points[self.waypoint]
            direction = (target - self.pos).normalize() if self.pos.distance_to(target) > 1 else pygame.Vector2()
            if distance < 125:
                direction = delta.normalize()
        elif distance < 175 and distance > 34:
            direction = delta.normalize()
        elif self.patrol == "pingpong":
            if abs(self.pos.x - self.patrol_origin.x) > 70:
                self.patrol_direction *= -1
            direction = pygame.Vector2(self.patrol_direction, 0)
        else:
            direction = pygame.Vector2()

        if self.kind == "mage" and distance < 250 and self.cooldown <= 0:
            self.cooldown = 1.5
            if distance:
                game.projectiles.append(Projectile(self.rect.centerx, self.rect.centery, delta, False, self.damage))
            self.state = "attack"
        elif distance < 34 and self.cooldown <= 0:
            self.cooldown = 0.8
            player.take_damage(self.damage, game)
            self.state = "attack"
            direction = pygame.Vector2()
        else:
            self.state = "walk" if direction.length_squared() else "idle"
        if direction.x:
            self.facing = 1 if direction.x > 0 else -1
        movement = direction * self.speed * dt
        self.pos += movement
        self.rect.center = round(self.pos.x), round(self.pos.y)
        if game.level_map.collides(self.rect):
            self.pos -= movement
            self.rect.center = round(self.pos.x), round(self.pos.y)
            self.patrol_direction *= -1
        if self.hit_flash > 0:
            self.state = "hurt"
        if self.state != previous_state:
            self.state_time = 0.0
        return True

    def draw(self, surface, camera):
        frames = enemy_frames(self.kind, self.state)
        fps = {"idle": 6, "walk": 12, "attack": 14, "hurt": 12, "death": 10}.get(self.state, 10)
        frame_index = min(int(self.state_time * fps), len(frames) - 1)
        image = frames[frame_index].copy()
        if self.facing < 0:
            image = pygame.transform.flip(image, True, False)
        if self.hit_flash:
            image.set_alpha(155)
        dest = image.get_rect(midbottom=(round(self.rect.centerx - camera.x), round(self.rect.bottom - camera.y)))
        surface.blit(image, dest)
        if self.alive and self.health < self.max_health:
            bar = pygame.Rect(dest.centerx - 15, dest.top + 2, 30, 4)
            pygame.draw.rect(surface, (45, 37, 45), bar)
            bar.width = round(30 * self.health / self.max_health)
            pygame.draw.rect(surface, (235, 83, 91), bar)


class Drop:
    def __init__(self, x, y, item, amount):
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
        self.item = item
        self.amount = amount
        self.phase = 0.0

    def draw(self, surface, camera, show_label=False):
        self.phase += 0.05
        x, y = self.rect.centerx - camera.x, self.rect.centery - camera.y
        bob = round(math.sin(self.phase * 4) * 2)
        center = (round(x), round(y + bob))
        pygame.draw.ellipse(surface, (14, 18, 24), (center[0] - 12, center[1] + 9, 24, 7))
        draw_item_icon(surface, self.item, center)
        if show_label:
            draw_item_label(surface, self.item, center)


class Pickup:
    def __init__(self, rect, item, amount=1):
        self.rect = pygame.Rect(rect)
        self.item = item if item in ITEM_DATA else "ammo"
        self.amount = int(amount)
        self.phase = 0.0

    def draw(self, surface, camera, show_label=False):
        self.phase += 0.05
        bob = round(math.sin(self.phase * 4) * 2)
        center = (round(self.rect.centerx - camera.x), round(self.rect.centery - camera.y + bob))
        pygame.draw.ellipse(surface, (14, 18, 24), (center[0] - 12, center[1] + 9, 24, 7))
        draw_item_icon(surface, self.item, center)
        if show_label:
            draw_item_label(surface, self.item, center)


class Switch:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.active = False

    def draw(self, surface, camera):
        rect = self.rect.move(-round(camera.x), -round(camera.y))
        color = (112, 230, 177) if self.active else (219, 161, 75)
        pygame.draw.rect(surface, (42, 37, 46), rect.inflate(6, 6), border_radius=5)
        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.circle(surface, (248, 236, 199), rect.center, 4)


class Door:
    def __init__(self, rect, requires):
        self.rect = pygame.Rect(rect)
        self.requires = requires

    def draw(self, surface, camera, unlocked=False):
        rect = self.rect.move(-round(camera.x), -round(camera.y))
        color = (81, 209, 157) if unlocked else (176, 120, 73)
        pygame.draw.rect(surface, (39, 36, 46), rect.inflate(8, 6), border_radius=5)
        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.circle(surface, (250, 222, 130), (rect.centerx + 5, rect.centery), 3)
