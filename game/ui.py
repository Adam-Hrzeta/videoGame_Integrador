import pygame

from .constants import ENEMY_DATA, ITEM_DATA, LEVELS

BG = (14, 18, 27)
PANEL = (22, 29, 42)
TEXT = (235, 239, 230)
MUTED = (167, 179, 183)
ACCENT = (114, 226, 190)


def font(size, bold=False):
    return pygame.font.SysFont("segoeui", size, bold=bold)


def draw_text(surface, text, x, y, size=22, color=TEXT, bold=False, center=False):
    image = font(size, bold).render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(image, rect)
    return rect


def draw_hud(surface, game):
    width = surface.get_width()
    pygame.draw.rect(surface, (13, 17, 26, 235), (0, 0, width, 78))
    draw_text(surface, "VIDA", 18, 9, 14, MUTED, True)
    for i in range(game.player.max_health):
        color = (237, 98, 111) if i < game.player.health else (76, 80, 90)
        pygame.draw.rect(surface, color, (18 + i * 19, 34, 14, 12), border_radius=4)
    draw_text(surface, "Vidas %d" % game.player.lives, 155, 29, 17)
    draw_text(surface, "Puntos %06d" % game.stats.score, 245, 29, 17, (242, 216, 145))
    draw_text(surface, "Enemigos %d" % sum(e.alive for e in game.enemies), 400, 29, 17)
    draw_text(surface, "Zona %d/5" % game.level, width - 122, 29, 17, ACCENT, True)
    labels = tuple(ITEM_DATA)
    x0 = max(18, width - 4 * 72 - 24)
    for index, name in enumerate(labels):
        rect = pygame.Rect(x0 + index * 72, 86, 62, 54)
        pygame.draw.rect(surface, (19, 24, 35), rect, border_radius=7)
        pygame.draw.rect(surface, ACCENT if index == game.player.selected else (65, 75, 88), rect, 2, border_radius=7)
        pygame.draw.circle(surface, ITEM_DATA[name]["color"], (rect.centerx, rect.y + 17), 6)
        draw_text(surface, "%d" % game.player.inventory[name], rect.centerx, rect.y + 39, 15, TEXT, True, True)
        draw_text(surface, str(index + 1), rect.x + 5, rect.y + 2, 11, MUTED)
    draw_text(surface, "Munición %d" % game.player.ammo, 18, 60, 15, (240, 198, 104))
    if game.player.power_timer > 0:
        draw_text(surface, "Esencia %.0fs" % game.player.power_timer, 150, 60, 15, (106, 225, 233))
    if game.notice_timer > 0:
        notice = font(17, True).render(game.notice_text, True, TEXT)
        rect = notice.get_rect(center=(width // 2, surface.get_height() - 34))
        pygame.draw.rect(surface, (14, 19, 28), rect.inflate(28, 16), border_radius=9)
        surface.blit(notice, rect)


def draw_inventory(surface, game):
    width, height = surface.get_size()
    shade = pygame.Surface((width, height), pygame.SRCALPHA)
    shade.fill((5, 8, 14, 180))
    surface.blit(shade, (0, 0))
    draw_text(surface, "INVENTARIO", width // 2, height // 2 - 118, 30, ACCENT, True, True)
    for index, name in enumerate(ITEM_DATA):
        rect = pygame.Rect(width // 2 - 218 + index * 110, height // 2 - 52, 98, 105)
        pygame.draw.rect(surface, PANEL, rect, border_radius=10)
        pygame.draw.rect(surface, ACCENT if index == game.player.selected else (76, 87, 100), rect, 2, border_radius=10)
        pygame.draw.circle(surface, ITEM_DATA[name]["color"], (rect.centerx, rect.y + 30), 12)
        draw_text(surface, ITEM_DATA[name]["name"], rect.centerx, rect.y + 57, 14, TEXT, True, True)
        draw_text(surface, "x%d" % game.player.inventory[name], rect.centerx, rect.y + 82, 16, MUTED, False, True)
    draw_text(surface, "1–4 seleccionar  •  Q usar  •  X descartar  •  Tab cerrar", width // 2, height // 2 + 95, 16, MUTED, False, True)


def draw_panel(surface, title, lines, selected=0, subtitle=None):
    width, height = surface.get_size()
    shade = pygame.Surface((width, height), pygame.SRCALPHA)
    shade.fill((5, 8, 14, 205))
    surface.blit(shade, (0, 0))
    panel = pygame.Rect(width // 2 - 240, height // 2 - 190, 480, 380)
    pygame.draw.rect(surface, PANEL, panel, border_radius=18)
    pygame.draw.rect(surface, (68, 87, 100), panel, 2, border_radius=18)
    draw_text(surface, title, width // 2, panel.y + 46, 32, ACCENT, True, True)
    if subtitle:
        draw_text(surface, subtitle, width // 2, panel.y + 91, 16, MUTED, False, True)
    start_y = panel.y + (124 if subtitle else 116)
    option_rects = []
    for index, line in enumerate(lines):
        color = ACCENT if index == selected else TEXT
        prefix = "›  " if index == selected else "   "
        draw_text(surface, prefix + line, panel.x + 62, start_y + index * 39, 19, color, index == selected)
        option_rects.append(pygame.Rect(panel.x + 38, start_y + index * 39 - 5, panel.width - 76, 33))
    return option_rects


def draw_stats(surface, game, title):
    width, height = surface.get_size()
    shade = pygame.Surface((width, height), pygame.SRCALPHA)
    shade.fill((5, 8, 14, 215))
    surface.blit(shade, (0, 0))
    draw_text(surface, title, width // 2, height // 2 - 135, 38, ACCENT, True, True)
    draw_text(surface, "Puntaje: %d" % game.stats.score, width // 2, height // 2 - 60, 22, TEXT, False, True)
    draw_text(surface, "Enemigos derrotados: %d" % game.stats.enemies_defeated, width // 2, height // 2 - 23, 19, TEXT, False, True)
    draw_text(surface, "Muertes: %d   •   Tiempo: %02d:%02d" % (
        game.stats.deaths, int(game.elapsed) // 60, int(game.elapsed) % 60), width // 2, height // 2 + 14, 19, TEXT, False, True)
    draw_text(surface, "Vidas: %d   •   Enemigos restantes: %d" % (
        game.stats.lives, game.stats.enemies_remaining), width // 2, height // 2 + 49, 18, TEXT, False, True)
    draw_text(surface, "Zona alcanzada: %d/5" % game.stats.level, width // 2, height // 2 + 82, 18, TEXT, False, True)
    draw_text(surface, "Enter: menú principal    •    R: jugar de nuevo    •    Escape: salir", width // 2, height // 2 + 125, 15, MUTED, False, True)


def draw_tutorial(surface, game):
    if game.level > 2 or game.elapsed > 38:
        return
    if game.level == 1:
        text = "WASD mover  •  Espacio atacar  •  F disparar  •  E interactuar"
    else:
        text = "Q usa el objeto seleccionado  •  1–4 o rueda: cambiar objeto  •  Esc: pausa"
    rect = pygame.Rect(18, surface.get_height() - 84, min(surface.get_width() - 36, 640), 34)
    pygame.draw.rect(surface, (16, 23, 33), rect, border_radius=8)
    pygame.draw.rect(surface, (62, 86, 98), rect, 1, border_radius=8)
    draw_text(surface, text, rect.x + 12, rect.y + 7, 14, TEXT)


def format_time(seconds):
    return "%02d:%02d" % (int(seconds) // 60, int(seconds) % 60)
