import pygame

from .constants import ENEMY_DATA, ITEM_DATA, LEVELS
from .item_icons import draw_item_icon

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


def draw_text_right(surface, text, x, y, size=22, color=TEXT, bold=False):
    image = font(size, bold).render(str(text), True, color)
    rect = image.get_rect(topright=(x, y))
    surface.blit(image, rect)
    return rect


def draw_heart(surface, center, color):
    x, y = center
    pygame.draw.circle(surface, color, (x - 4, y - 2), 5)
    pygame.draw.circle(surface, color, (x + 4, y - 2), 5)
    pygame.draw.polygon(surface, color, ((x - 9, y), (x + 9, y), (x, y + 10)))


def draw_hud(surface, game):
    width = surface.get_width()
    pygame.draw.rect(surface, (13, 17, 26), (0, 0, width, 74))
    pygame.draw.line(surface, (65, 98, 104), (0, 73), (width, 73), 1)
    pygame.draw.line(surface, (114, 226, 190), (0, 73), (width, 73), 1)
    draw_text(surface, "SALUD", 18, 7, 12, MUTED, True)
    for i in range(game.player.max_health):
        color = (245, 100, 113) if i < game.player.health else (65, 73, 83)
        draw_heart(surface, (24 + i * 19, 33), color)
    draw_text(surface, "%d/%d" % (game.player.health, game.player.max_health),
              119, 26, 15, TEXT, True)
    health_bar = pygame.Rect(18, 51, 112, 7)
    pygame.draw.rect(surface, (45, 53, 65), health_bar, border_radius=4)
    health_ratio = max(0.0, min(1.0, game.player.health / game.player.max_health))
    fill_width = round(health_bar.width * health_ratio)
    if fill_width:
        pygame.draw.rect(surface, (226, 91, 105),
                         (health_bar.x, health_bar.y, fill_width, health_bar.height), border_radius=4)

    draw_text(surface, "VIDAS", 163, 13, 11, MUTED, True)
    draw_text(surface, str(game.player.lives), 163, 32, 19, TEXT, True)
    draw_text(surface, "PUNTAJE", 222, 13, 11, MUTED, True)
    draw_text(surface, "%06d" % game.stats.score, 222, 32, 17, (242, 216, 145), True)
    draw_text(surface, "ENEMIGOS", 347, 13, 11, MUTED, True)
    draw_text(surface, str(sum(e.alive for e in game.enemies)), 347, 32, 17, TEXT, True)
    draw_text(surface, "DISPAROS", 454, 13, 11, MUTED, True)
    draw_text(surface, str(game.player.ammo), 454, 32, 17, (240, 198, 104), True)
    draw_text_right(surface, "ZONA %d/5" % game.level, width - 18, 25, 16, ACCENT, True)
    if game.player.power_timer > 0:
        draw_text_right(surface, "ESENCIA ACTIVA %.0fs" % game.player.power_timer,
                        width - 18, 49, 11, (106, 225, 233), True)

    panel = pygame.Rect(14, 86, 218, 198)
    pygame.draw.rect(surface, (13, 19, 28), panel, border_radius=10)
    pygame.draw.rect(surface, (62, 79, 91), panel, 1, border_radius=10)
    draw_text(surface, "RECURSOS", panel.x + 12, panel.y + 8, 12, MUTED, True)
    pygame.draw.line(surface, (48, 61, 72), (panel.x + 10, panel.y + 29),
                     (panel.right - 10, panel.y + 29), 1)
    for index, name in enumerate(ITEM_DATA):
        row = pygame.Rect(panel.x + 8, panel.y + 35 + index * 38, panel.width - 16, 34)
        selected = index == game.player.selected
        pygame.draw.rect(surface, (29, 46, 49) if selected else (18, 25, 36),
                         row, border_radius=6)
        pygame.draw.rect(surface, ACCENT if selected else (40, 51, 63),
                         row, 1, border_radius=6)
        draw_text(surface, str(index + 1), row.x + 5, row.y + 10, 10, MUTED)
        draw_item_icon(surface, name, (row.x + 31, row.centery))
        draw_text(surface, ITEM_DATA[name]["name"], row.x + 51, row.y + 8, 13, TEXT, True)
        draw_text(surface, "x%d" % game.player.inventory[name],
                  row.right - 12, row.centery, 13, ITEM_DATA[name]["color"], True, True)
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
        draw_item_icon(surface, name, (rect.centerx, rect.y + 30))
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
        text = "WASD mover  •  Espacio atacar  •  J saltar  •  F disparar  •  E interactuar"
    else:
        text = "Q usa el objeto seleccionado  •  1–4 o rueda: cambiar objeto  •  Esc: pausa"
    rect = pygame.Rect(18, surface.get_height() - 84, min(surface.get_width() - 36, 640), 34)
    pygame.draw.rect(surface, (16, 23, 33), rect, border_radius=8)
    pygame.draw.rect(surface, (62, 86, 98), rect, 1, border_radius=8)
    draw_text(surface, text, rect.x + 12, rect.y + 7, 14, TEXT)


def format_time(seconds):
    return "%02d:%02d" % (int(seconds) // 60, int(seconds) % 60)
