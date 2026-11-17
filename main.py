import os
import sys

import pygame

from game.audio import AudioManager
from game.constants import DEFAULT_SIZE, FPS, LEVELS, MAPS_DIR, MIN_SIZE
from game.gameplay import Game
from game.ui import (
    ACCENT,
    MUTED,
    PANEL,
    TEXT,
    draw_hud,
    draw_inventory,
    draw_panel,
    draw_stats,
    draw_text,
    draw_tutorial,
)


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def follow(self, target, world_size, screen_size, dt):
        desired_x = target.rect.centerx - screen_size[0] / 2
        desired_y = target.rect.centery - screen_size[1] / 2
        desired_x = max(0, min(desired_x, world_size[0] - screen_size[0]))
        desired_y = max(0, min(desired_y, world_size[1] - screen_size[1]))
        blend = min(1.0, dt * 8)
        self.x += (desired_x - self.x) * blend
        self.y += (desired_y - self.y) * blend


def smoke_test():
    if not os.environ.get("SDL_VIDEODRIVER"):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode(DEFAULT_SIZE)
    if not (MAPS_DIR / "nivel_01.tmx").exists():
        from tools.build_maps import main as build_maps
        build_maps()
    audio = AudioManager(0)
    game = Game(audio)
    screen = pygame.Surface(DEFAULT_SIZE)
    camera = Camera()
    keys = pygame.key.get_pressed()
    for level in range(1, 6):
        game.load_level(level)
        camera.follow(game.player, (game.level_map.width, game.level_map.height), screen.get_size(), 1 / 60)
        game.update(1 / 60, keys, {})
        game.draw(screen, camera)
        assert game.level_map.tmx.width > screen.get_width() // 32
        assert game.door is not None
        assert len(game.enemies) >= 3
    print("SMOKE OK: 5 mapas TMX cargados y 1 ciclo de juego por nivel.")
    pygame.quit()


def set_screen(size):
    return pygame.display.set_mode(size, pygame.RESIZABLE)


def render_menu(screen, options, selected, title, subtitle=None):
    screen.fill((13, 18, 27))
    width, height = screen.get_size()
    for i in range(34):
        x = (i * 197 + 35) % width
        y = (i * 113 + 23) % height
        pygame.draw.circle(screen, (37, 49, 62), (x, y), 1 + (i % 2))
    draw_text(screen, "ECOS DEL", width // 2, max(75, height // 5), 27, (205, 217, 208), True, True)
    draw_text(screen, "UMBRAL", width // 2, max(127, height // 5 + 51), 54, ACCENT, True, True)
    if subtitle:
        draw_text(screen, subtitle, width // 2, max(169, height // 5 + 101), 16, MUTED, False, True)
    rects = []
    start_y = height // 2 + 23
    for index, option in enumerate(options):
        rect = pygame.Rect(width // 2 - 150, start_y + index * 53, 300, 43)
        pygame.draw.rect(screen, PANEL if index == selected else (17, 23, 33), rect, border_radius=9)
        pygame.draw.rect(screen, ACCENT if index == selected else (51, 65, 77), rect, 2, border_radius=9)
        draw_text(screen, option, rect.centerx, rect.centery, 19, TEXT if index == selected else MUTED, index == selected, True)
        rects.append(rect)
    draw_text(screen, "WASD mover   ·   Espacio atacar   ·   F disparar   ·   Esc pausa",
              width // 2, height - 31, 14, MUTED, False, True)
    return rects


def options_labels(options):
    return [
        "Volumen: %d%%" % round(options["volume"] * 100),
        "Resolución: %d × %d" % options["resolution"],
        "Controles: %s" % options["controls"],
        "Dificultad: %s" % options["difficulty"],
        "Volver",
    ]


def adjust_option(options, index, direction):
    if index == 0:
        options["volume"] = max(0.0, min(1.0, options["volume"] + direction * 0.1))
    elif index == 1:
        sizes = ((960, 640), (1280, 720))
        current = sizes.index(options["resolution"])
        options["resolution"] = sizes[(current + direction) % len(sizes)]
    elif index == 2:
        options["controls"] = "Flechas" if options["controls"] == "WASD" else "WASD"
    elif index == 3:
        levels = ("Fácil", "Normal", "Difícil")
        current = levels.index(options["difficulty"])
        options["difficulty"] = levels[(current + direction) % len(levels)]


def main():
    if "--smoke" in sys.argv:
        smoke_test()
        return
    pygame.init()
    pygame.display.set_caption("Ecos del Umbral")
    screen = set_screen(DEFAULT_SIZE)
    clock = pygame.time.Clock()
    audio = AudioManager(0.45)
    audio.set_volume(0.45)
    settings = {
        "volume": 0.45,
        "resolution": DEFAULT_SIZE,
        "controls": "WASD",
        "difficulty": "Normal",
    }
    mode = "menu"
    return_mode = "menu"
    menu_selection = 0
    option_selection = 0
    inventory_open = False
    camera = Camera()
    game = None
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        actions = {}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                size = (max(MIN_SIZE[0], event.w), max(MIN_SIZE[1], event.h))
                screen = set_screen(size)
            elif event.type == pygame.MOUSEWHEEL and mode == "playing" and game:
                game.player.selected = (game.player.selected - event.y) % 4
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mode == "menu":
                    rects = render_menu(screen, ("Jugar", "Configuración", "Salir"), menu_selection, "ECOS DEL UMBRAL")
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            menu_selection = i
                            if i == 0:
                                game = Game(audio, settings["difficulty"])
                                mode = "playing"
                            elif i == 1:
                                return_mode, mode = "menu", "settings"
                            else:
                                running = False
                elif mode == "settings":
                    lines = options_labels(settings)
                    for i, rect in enumerate(draw_panel(screen, "CONFIGURACIÓN", lines, option_selection, "← / → para cambiar")):
                        if rect.collidepoint(event.pos):
                            option_selection = i
                elif mode == "paused":
                    choices = ("Continuar", "Inventario", "Configuración", "Volver al menú")
                    for i, rect in enumerate(draw_panel(screen, "PAUSA", choices, menu_selection)):
                        if rect.collidepoint(event.pos):
                            menu_selection = i
            elif event.type == pygame.KEYDOWN:
                if mode == "menu":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        menu_selection = (menu_selection - 1) % 3
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        menu_selection = (menu_selection + 1) % 3
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if menu_selection == 0:
                            game = Game(audio, settings["difficulty"])
                            mode = "playing"
                        elif menu_selection == 1:
                            return_mode, mode, option_selection = "menu", "settings", 0
                        else:
                            running = False
                elif mode == "settings":
                    if event.key == pygame.K_ESCAPE:
                        mode = return_mode
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        option_selection = (option_selection - 1) % 5
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        option_selection = (option_selection + 1) % 5
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        adjust_option(settings, option_selection, -1 if event.key == pygame.K_LEFT else 1)
                        audio.set_volume(settings["volume"])
                        if option_selection == 1:
                            screen = set_screen(settings["resolution"])
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if option_selection == 4:
                            mode = return_mode
                        else:
                            adjust_option(settings, option_selection, 1)
                            audio.set_volume(settings["volume"])
                            if option_selection == 1:
                                screen = set_screen(settings["resolution"])
                elif mode == "playing" and game:
                    if inventory_open:
                        if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                            inventory_open = False
                        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                            game.player.selected = event.key - pygame.K_1
                        elif event.key == pygame.K_q:
                            game.player.use_item(game)
                        elif event.key == pygame.K_x:
                            game.drop_selected()
                    elif event.key == pygame.K_ESCAPE:
                        mode, menu_selection = "paused", 0
                    elif event.key == pygame.K_TAB:
                        inventory_open = True
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        game.player.selected = event.key - pygame.K_1
                    elif event.key == pygame.K_SPACE:
                        actions["attack"] = True
                    elif event.key == pygame.K_f:
                        actions["shoot"] = True
                    elif event.key == pygame.K_e:
                        actions["interact"] = True
                    elif event.key == pygame.K_q:
                        actions["use"] = True
                elif mode == "paused":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        menu_selection = (menu_selection - 1) % 4
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        menu_selection = (menu_selection + 1) % 4
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if menu_selection == 0:
                            mode = "playing"
                        elif menu_selection == 1:
                            mode, inventory_open = "playing", True
                        elif menu_selection == 2:
                            return_mode, mode, option_selection = "paused", "settings", 0
                        else:
                            mode = "menu"
                    elif event.key == pygame.K_ESCAPE:
                        mode = "playing"
                    elif event.key == pygame.K_i:
                        mode, inventory_open = "playing", True
                elif mode in ("victory", "gameover"):
                    if event.key == pygame.K_RETURN:
                        mode = "menu"
                    elif event.key == pygame.K_r:
                        game = Game(audio, settings["difficulty"])
                        mode = "playing"
                    elif event.key == pygame.K_ESCAPE:
                        running = False

        if not running:
            break
        if mode == "playing" and game:
            if not inventory_open:
                game.update(dt, pygame.key.get_pressed(), actions, settings["controls"])
            if game.ended is not None:
                mode = "victory" if game.ended else "gameover"
            camera.follow(game.player, (game.level_map.width, game.level_map.height), screen.get_size(), dt)
            game.draw(screen, camera)
            draw_hud(screen, game)
            draw_tutorial(screen, game)
            if inventory_open:
                draw_inventory(screen, game)
        elif mode == "menu":
            render_menu(screen, ("Jugar", "Configuración", "Salir"), menu_selection, "ECOS DEL UMBRAL",
                        "Aventura de supervivencia · Cinco zonas para escapar")
        elif mode == "settings":
            screen.fill((13, 18, 27))
            draw_panel(screen, "CONFIGURACIÓN", options_labels(settings), option_selection,
                       "← / → cambia el valor   ·   Enter confirma   ·   Esc vuelve")
        elif mode == "paused" and game:
            game.draw(screen, camera)
            draw_hud(screen, game)
            draw_panel(screen, "PAUSA", ("Continuar", "Inventario", "Configuración", "Volver al menú"),
                       menu_selection, "Tiempo %s   ·   Puntos %d   ·   Muertes %d" % (
                           "%02d:%02d" % (int(game.elapsed) // 60, int(game.elapsed) % 60),
                           game.stats.score, game.stats.deaths))
            if inventory_open:
                draw_inventory(screen, game)
        elif mode == "victory" and game:
            game.draw(screen, camera)
            draw_stats(screen, game, "¡UMBRAL SUPERADO!")
        elif mode == "gameover" and game:
            game.draw(screen, camera)
            draw_stats(screen, game, "FIN DE LA PARTIDA")
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
