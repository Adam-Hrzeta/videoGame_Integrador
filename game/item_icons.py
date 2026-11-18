from functools import lru_cache

import pygame

from .constants import ITEM_DATA


@lru_cache(maxsize=1)
def item_label_font():
    return pygame.font.SysFont("segoeui", 12, bold=True)


def draw_item_icon(surface, name, center):
    x, y = center
    color = ITEM_DATA[name]["color"]
    pygame.draw.circle(surface, (13, 19, 28), center, 13)
    pygame.draw.circle(surface, (58, 70, 82), center, 13, 1)

    if name == "medkit":
        case = pygame.Rect(x - 8, y - 6, 16, 13)
        pygame.draw.rect(surface, (231, 236, 229), case, border_radius=3)
        pygame.draw.rect(surface, color, case, 1, border_radius=3)
        pygame.draw.rect(surface, color, (x - 2, y - 4, 4, 9), border_radius=1)
        pygame.draw.rect(surface, color, (x - 5, y - 1, 10, 4), border_radius=1)
    elif name == "ammo":
        pygame.draw.polygon(surface, color, (
            (x, y - 9), (x + 5, y - 3), (x + 4, y + 8),
            (x - 4, y + 8), (x - 5, y - 3),
        ))
        pygame.draw.line(surface, (255, 238, 188), (x, y - 5), (x, y + 5), 1)
    elif name == "key":
        pygame.draw.circle(surface, color, (x - 5, y - 2), 5, 2)
        pygame.draw.line(surface, color, (x - 1, y + 1), (x + 8, y + 1), 3)
        pygame.draw.line(surface, color, (x + 5, y + 1), (x + 5, y + 5), 2)
        pygame.draw.line(surface, color, (x + 8, y + 1), (x + 8, y + 4), 2)
    elif name == "power":
        pygame.draw.polygon(surface, color, (
            (x, y - 9), (x + 7, y - 2), (x + 5, y + 6),
            (x, y + 10), (x - 5, y + 6), (x - 7, y - 2),
        ))
        pygame.draw.line(surface, (226, 255, 255), (x, y - 5), (x - 2, y + 5), 2)
    else:
        pygame.draw.circle(surface, color, center, 6)


def draw_item_label(surface, name, center):
    text = item_label_font().render(ITEM_DATA[name]["name"], True, (242, 245, 239))
    rect = text.get_rect(center=(center[0], center[1] - 25)).inflate(12, 6)
    pygame.draw.rect(surface, (13, 19, 28), rect, border_radius=5)
    pygame.draw.rect(surface, ITEM_DATA[name]["color"], rect, 1, border_radius=5)
    surface.blit(text, text.get_rect(center=rect.center))
