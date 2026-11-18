import os
import unittest
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.constants import ENEMY_DATA, ITEM_DATA, LEVELS
from game.entities import ENEMY_FRAME_SIZE, PLAYER_FRAME_SIZE, Pickup, enemy_frames, player_frames
from game.gameplay import Game
from game.maps import LevelMap
from game.audio import AudioManager
from game.ui import draw_hud


class SilentAudio:
    def play(self, _name):
        pass

    def play_level(self, _number):
        pass


class GameRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((960, 640))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_tmx_maps_load_and_include_all_patrol_patterns(self):
        species = set()
        patrols = set()
        for number in range(1, len(LEVELS) + 1):
            level = LevelMap(number)
            self.assertGreater(level.width, 960)
            self.assertIsNotNone(level.door)
            self.assertGreaterEqual(len(level.enemies), 3)
            self.assertFalse(level.collides(pygame.Rect(level.spawn[0] - 8, level.spawn[1] - 8, 16, 16)))
            species.update(enemy.kind for enemy in level.enemies)
            patrols.update(enemy.patrol for enemy in level.enemies)
        self.assertEqual(species, set(ENEMY_DATA))
        self.assertEqual(patrols, {"pingpong", "waypoints", "fsm"})

    def test_campaign_maps_have_distinct_themes_and_layouts(self):
        themes = set()
        layouts = set()
        for number in range(1, len(LEVELS) + 1):
            level = LevelMap(number)
            themes.add(level.tmx.tilesets[0].name)
            layouts.add(frozenset((wall.x, wall.y) for wall in level.solids))
        self.assertEqual(len(themes), len(LEVELS))
        self.assertEqual(len(layouts), len(LEVELS))

    def test_every_map_has_a_walkable_route_from_spawn_to_door(self):
        for number in range(1, len(LEVELS) + 1):
            level = LevelMap(number)
            tile_width, tile_height = level.tmx.tilewidth, level.tmx.tileheight
            start = (level.spawn[0] // tile_width, level.spawn[1] // tile_height)
            target = (level.door.rect.centerx // tile_width, level.door.rect.centery // tile_height)
            queue = deque([start])
            reached = {start}
            while queue:
                x, y = queue.popleft()
                for next_cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    nx, ny = next_cell
                    if not (0 <= nx < level.tmx.width and 0 <= ny < level.tmx.height):
                        continue
                    if next_cell in reached:
                        continue
                    rect = pygame.Rect(
                        nx * tile_width + 4, ny * tile_height + 4,
                        tile_width - 8, tile_height - 8,
                    )
                    if not level.collides(rect):
                        reached.add(next_cell)
                        queue.append(next_cell)
            self.assertIn(target, reached, "El nivel %d no conecta el inicio con la puerta." % number)

    def test_player_uses_samurai_animations_for_all_states(self):
        self.assertEqual(len(player_frames("idle")), 6)
        self.assertEqual(len(player_frames("walk")), 8)
        self.assertEqual(len(player_frames("attack")), 4)
        self.assertEqual(len(player_frames("shoot")), 5)
        self.assertEqual(len(player_frames("jump")), 9)
        self.assertGreater(len(player_frames("hurt")), 1)
        self.assertGreater(len(player_frames("death")), 1)
        self.assertEqual(player_frames("walk")[0].get_size(), PLAYER_FRAME_SIZE)

    def test_each_enemy_type_uses_its_own_animated_sprite(self):
        idle_frames = []
        for kind in ENEMY_DATA:
            for state in ("idle", "walk", "attack", "hurt", "death"):
                frames = enemy_frames(kind, state)
                self.assertGreater(len(frames), 1, "%s has no %s animation" % (kind, state))
                self.assertEqual(frames[0].get_size(), ENEMY_FRAME_SIZE)
            idle_frames.append(pygame.image.tostring(enemy_frames(kind, "idle")[0], "RGBA"))
        self.assertEqual(len(set(idle_frames)), len(ENEMY_DATA))

    def test_jump_action_plays_the_jump_animation(self):
        game = Game(SilentAudio())
        game.update(1 / 60, pygame.key.get_pressed(), {"jump": True})
        self.assertEqual(game.player.state, "jump")
        self.assertGreater(game.player.jump_timer, 0)

    def test_hud_renders_health_and_resource_panel_at_minimum_resolution(self):
        game = Game(SilentAudio())
        surface = pygame.Surface((800, 600))
        draw_hud(surface, game)
        self.assertNotEqual(surface.get_at((30, 100)), (0, 0, 0, 255))

    def test_world_pickups_have_distinct_icons_and_nearby_labels(self):
        rendered_items = []
        for item in ITEM_DATA:
            surface = pygame.Surface((180, 120))
            pickup = Pickup(pygame.Rect(70, 60, 20, 20), item)
            pickup.draw(surface, pygame.Vector2(), show_label=True)
            rendered_items.append(pygame.image.tostring(surface, "RGB"))
        self.assertEqual(len(set(rendered_items)), len(ITEM_DATA))

    def test_key_door_requires_cleared_level_and_consumes_key(self):
        game = Game(SilentAudio())
        game.player.inventory["key"] = 1
        game.player.rect.center = game.door.rect.center
        game.player.pos.update(game.door.rect.center)
        game.interact()
        self.assertEqual(game.level, 1)
        self.assertEqual(game.player.inventory["key"], 1)

        for enemy in game.enemies:
            enemy.take_damage(100, game)
        game.interact()
        self.assertEqual(game.level, 2)
        self.assertEqual(game.player.inventory["key"], 0)

    def test_switch_level_requires_mechanism_and_enemy_clear(self):
        game = Game(SilentAudio())
        game.load_level(3)
        for enemy in game.enemies:
            enemy.take_damage(100, game)
        switch = game.switches[0]
        game.player.rect.center = switch.rect.center
        game.player.pos.update(switch.rect.center)
        game.interact()
        self.assertTrue(switch.active)
        game.player.rect.center = game.door.rect.center
        game.player.pos.update(game.door.rect.center)
        game.interact()
        self.assertEqual(game.level, 4)

    def test_death_updates_campaign_stats_and_removes_an_inventory_item(self):
        game = Game(SilentAudio())
        game.player.health = 1
        game.player.inventory["medkit"] = 1
        game.player.take_damage(1, game)
        self.assertEqual(game.player.lives, 2)
        self.assertEqual(game.stats.deaths, 1)
        self.assertEqual(game.player.health, game.player.max_health)
        self.assertEqual(game.player.inventory["medkit"], 0)

    def test_full_inventory_does_not_destroy_a_pickup(self):
        game = Game(SilentAudio())
        pickup = game.pickups[0]
        game.player.inventory[pickup.item] = 99
        pickup.rect.center = game.player.rect.center
        game.collect()
        self.assertIn(pickup, game.pickups)

    def test_original_audio_assets_exist_and_load(self):
        audio = AudioManager(0)
        self.assertTrue(audio.available)
        self.assertEqual(len(audio.music), 5)
        self.assertEqual(set(("shot", "swing", "hurt", "enemy_dead", "pickup",
                              "door", "switch", "victory", "gameover")),
                         set(audio.sounds))


if __name__ == "__main__":
    unittest.main()
