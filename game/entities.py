import math
from functools import lru_cache

import pygame

from .constants import ENEMY_DATA, ITEM_DATA, TILE_SIZE

ACTOR_SIZE = 48


@lru_cache(maxsize=256)
def actor_image(kind, state, frame, facing):
    image = pygame.Surface((ACTOR_SIZE, ACTOR_SIZE), pygame.SRCALPHA)
    bob = (0, -2, 0, 2)[frame % 4] if state in ("walk", "attack") else (0, 1, 0, -1)[frame % 4]
    cx = ACTOR_SIZE // 2 + (3 if state == "attack" else 0)
    pygame.draw.ellipse(image, (14, 18, 22, 100), (8, 36, 32, 8))
    if kind == "player":
        body = (62, 172, 153) if state != "hurt" else (255, 104, 100)
        pygame.draw.polygon(image, (50, 84, 99), [(cx - 12, 21 + bob), (cx + 11, 20 + bob), (cx + 16, 40), (cx - 17, 40)])
        pygame.draw.ellipse(image, body, (cx - 10, 11 + bob, 20, 20))
        pygame.draw.polygon(image, (30, 45, 59), [(cx - 11, 16 + bob), (cx, 3 + bob), (cx + 11, 16 + bob)])
        pygame.draw.circle(image, (244, 215, 164), (cx + (5 if facing > 0 else -5), 19 + bob), 2)
        if state in ("attack", "shoot"):
            pygame.draw.line(image, (224, 231, 220), (cx + facing * 10, 27 + bob), (cx + facing * 23, 18 + bob), 3)
            pygame.draw.circle(image, (120, 213, 230), (cx + facing * 23, 18 + bob), 3)
    else:
        color = ENEMY_DATA[kind]["color"]
        if state == "hurt":
            color = (255, 111, 105)
        elif state == "death":
            color = tuple(max(25, int(c * 0.55)) for c in color)
        if kind == "slime":
            pygame.draw.ellipse(image, color, (cx - 15, 17 + bob, 30, 22 - (frame % 2) * 2))
            pygame.draw.circle(image, (241, 247, 218), (cx + facing * 6, 25 + bob), 3)
            pygame.draw.circle(image, (34, 49, 45), (cx + facing * 7, 25 + bob), 1)
            pygame.draw.arc(image, (198, 246, 186), (cx - 7, 20 + bob, 13, 12), 0.2, 2.5, 2)
        elif kind == "wraith":
            pygame.draw.polygon(image, color, [(cx - 12, 38), (cx - 9, 15 + bob), (cx, 8 + bob), (cx + 11, 15 + bob), (cx + 13, 37), (cx + 6, 33), (cx, 38), (cx - 6, 33)])
            pygame.draw.ellipse(image, (224, 245, 255), (cx - 7, 19 + bob, 5, 3))
            pygame.draw.ellipse(image, (224, 245, 255), (cx + 3, 19 + bob, 5, 3))
        else:
            pygame.draw.rect(image, (59, 49, 52), (cx - 11, 26 + bob, 8, 13))
            pygame.draw.rect(image, (59, 49, 52), (cx + 3, 26 + bob, 8, 13))
            pygame.draw.rect(image, color, (cx - 13, 17 + bob, 26, 17), border_radius=5)
            pygame.draw.circle(image, color, (cx, 13 + bob), 10)
            pygame.draw.circle(image, (243, 211, 154), (cx + facing * 5, 14 + bob), 2)
            if kind == "skeleton":
                pygame.draw.polygon(image, (230, 219, 180), [(cx - 9, 6 + bob), (cx - 6, 1 + bob), (cx - 2, 8 + bob)])
                pygame.draw.line(image, (241, 236, 218), (cx - 7, 25 + bob), (cx + 8, 25 + bob), 2)
            elif kind == "brute":
                pygame.draw.circle(image, (98, 54, 51), (cx - 14, 24 + bob), 6)
                pygame.draw.circle(image, (98, 54, 51), (cx + 14, 24 + bob), 6)
                pygame.draw.rect(image, (239, 191, 118), (cx - 5, 22 + bob, 10, 3))
            elif kind == "mage":
                pygame.draw.polygon(image, (86, 54, 129), [(cx - 13, 14 + bob), (cx, 0 + bob), (cx + 13, 14 + bob)])
                pygame.draw.line(image, (232, 207, 135), (cx + 12, 23 + bob), (cx + 16, 38), 3)
                pygame.draw.circle(image, (112, 221, 255), (cx + 12, 20 + bob), 4)
        if state == "attack":
            pygame.draw.arc(image, (245, 204, 139), (cx + facing * 5 - 8, 12 + bob, 28, 27), 3.8 if facing > 0 else 0.7, 5.7 if facing > 0 else 2.4, 2)
    if facing < 0:
        image = pygame.transform.flip(image, True, False)
    return image


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
        frame = int(self.anim_time * 9) % 4
        image = actor_image("player", self.state, frame, self.facing).copy()
        dest = image.get_rect(center=(round(self.rect.centerx - camera.x), round(self.rect.centery - camera.y)))
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
        if self.health <= 0:
            self.alive = False
            self.state = "death"
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
        self.cooldown = max(0.0, self.cooldown - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        if not self.alive:
            self.death_timer -= dt
            return self.death_timer > 0
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
        return True

    def draw(self, surface, camera):
        image = actor_image(self.kind, self.state, int(self.anim_time * 8) % 4, self.facing).copy()
        if self.hit_flash:
            image.set_alpha(155)
        dest = image.get_rect(center=(round(self.rect.centerx - camera.x), round(self.rect.centery - camera.y)))
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

    def draw(self, surface, camera):
        self.phase += 0.05
        x, y = self.rect.centerx - camera.x, self.rect.centery - camera.y
        bob = round(math.sin(self.phase * 4) * 2)
        pygame.draw.circle(surface, ITEM_DATA[self.item]["color"], (round(x), round(y + bob)), 9)
        pygame.draw.circle(surface, (250, 245, 222), (round(x), round(y + bob)), 3)


class Pickup:
    def __init__(self, rect, item, amount=1):
        self.rect = pygame.Rect(rect)
        self.item = item if item in ITEM_DATA else "ammo"
        self.amount = int(amount)
        self.phase = 0.0

    def draw(self, surface, camera):
        self.phase += 0.05
        bob = round(math.sin(self.phase * 4) * 2)
        center = (round(self.rect.centerx - camera.x), round(self.rect.centery - camera.y + bob))
        pygame.draw.circle(surface, (20, 24, 30), (center[0], center[1] + 4), 10)
        pygame.draw.circle(surface, ITEM_DATA[self.item]["color"], center, 8)
        pygame.draw.circle(surface, (255, 247, 221), center, 3)


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
