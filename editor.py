import pygame
import sys
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_pos

from menu import Menu
import settings as s


class Editor:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.menu = Menu()

        self.origin = vector((s.WINDOW_WIDTH // 2, s.WINDOW_HEIGTH // 2))
        self.pan_mode = False
        self.pan_offset = vector()
        self.mode = 1

        self.guide_surf = pygame.Surface((s.WINDOW_WIDTH, s.WINDOW_WIDTH))
        self.guide_surf.set_colorkey("green")

        # canvas stuff:
        self.canvas_data = {}
        self.last_cell = None
        self.selection_type = "float"
        self.selection_id = "chair"

        # float stuff:
        self.canvas_floats = pygame.sprite.Group()
        self.float_drag_active = False

    def event_loop(self):
        for event in pygame.event.get():
            self.mode_switch(event)
            self.pan_movement(event)
            self.float_drag(event)
            self.canvas_add()

    def mode_switch(self, event):
        if event.type == pygame.QUIT:
            self.mode = 0
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.mode = 0

    def get_current_cell(self):
        temp_vect = (vector(mouse_pos()) - self.origin) // s.TILE_SIZE
        return (temp_vect.x, temp_vect.y)

    def pan_movement(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
            self.pan_mode = True
            self.pan_offset = vector(mouse_pos()) - self.origin
        if not mouse_buttons()[1]:
            self.pan_mode = False

        if self.pan_mode:
            self.origin = vector(mouse_pos()) - self.pan_offset

            for sprite in self.canvas_floats:
                sprite.pan_pos(self.origin)

    def canvas_add(self):
        if mouse_buttons()[0] and not self.float_drag_active:
            current_cell = self.get_current_cell()
            if self.selection_type == "tile":
                if current_cell != self.last_cell:
                    if current_cell in self.canvas_data:
                        self.canvas_data[current_cell].add_id(self.selection_id)
                    else:
                        self.canvas_data[current_cell] = CanvasTile(self.selection_id)

                    self.last_cell = current_cell
            else:
                CanvasFloat(
                    pos=mouse_pos(),
                    surf=pygame.surface.Surface((100, 100)),
                    float_id=self.selection_id,
                    origin=self.origin,
                    group=self.canvas_floats,
                )

    def float_drag(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            for sprite in self.canvas_floats:
                if sprite.rect.collidepoint(mouse_pos()):
                    self.float_drag_active = True
                    sprite.start_drag()

        if event.type == pygame.MOUSEBUTTONUP and self.float_drag_active:
            for sprite in self.canvas_floats:
                if sprite.selected:
                    sprite.end_drag(self.origin)
                    self.float_drag_active = False

    def draw_tile_guides(self):
        cols = s.WINDOW_WIDTH // s.TILE_SIZE
        rows = s.WINDOW_HEIGTH // s.TILE_SIZE

        origin_offset = vector(self.origin.x % s.TILE_SIZE, self.origin.y % s.TILE_SIZE)

        self.guide_surf.fill("green")

        for col in range(cols + 1):
            x = origin_offset.x + col * s.TILE_SIZE
            pygame.draw.line(self.guide_surf, "gray", (x, 0), (x, s.WINDOW_HEIGTH))

        for row in range(rows + 1):
            y = origin_offset.y + row * s.TILE_SIZE
            pygame.draw.line(self.guide_surf, "gray", (0, y), (s.WINDOW_WIDTH, y))

        self.display_surface.blit(self.guide_surf, (0, 0))

    def draw_level(self):
        for cell_pos, tile in self.canvas_data.items():
            pos = self.origin + vector(cell_pos) * s.TILE_SIZE

            if tile.wall:
                surf = pygame.surface.Surface((s.TILE_SIZE, s.TILE_SIZE))
                surf.fill("brown")
                rect = surf.get_rect(topleft=pos)
                self.display_surface.blit(surf, rect)
        self.canvas_floats.draw(self.display_surface)

    def run(self, dt):  # dt for future animations
        self.event_loop()
        self.canvas_floats.update()
        self.display_surface.fill("white")
        self.draw_tile_guides()
        self.draw_level()
        pygame.draw.circle(self.display_surface, "red", self.origin, 30)
        self.menu.display()
        return self.mode


class CanvasTile:
    def __init__(self, tile_id):
        self.wall = False
        self.coin = None

        self.add_id(tile_id)

    def add_id(self, tile_id):
        match tile_id:
            case "wall":
                self.wall = True
            case "coin":
                self.coin = tile_id


class CanvasFloat(pygame.sprite.Sprite):
    def __init__(self, pos, surf, float_id, origin, group):
        super().__init__(group)
        self.float_id = float_id

        self.image = surf
        self.image.fill("green")
        self.rect = surf.get_rect(center=pos)

        self.distance_to_origin = vector(self.rect.topleft) - origin
        self.selected = False
        self.mouse_offset = vector()

    def start_drag(self):
        self.selected = True
        self.mouse_offset = vector(mouse_pos()) - vector(self.rect.topleft)

    def drag(self):
        if self.selected:
            self.rect.topleft = mouse_pos() - self.mouse_offset

    def end_drag(self, origin):
        self.selected = False
        self.distance_to_origin = vector(self.rect.topleft) - origin

    def pan_pos(self, origin):
        self.rect.topleft = origin + self.distance_to_origin

    def update(self):
        self.drag()
