import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.constants import ENEMY_DATA, LEVELS
from game.gameplay import Game
from game.maps import LevelMap


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


if __name__ == "__main__":
    unittest.main()
