import pygame
from pygame.math import Vector2 as vector

import settings as s
from support import signum


class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, group):
        super().__init__(group)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)


class Animated(Generic):
    def __init__(self, pos, frames, group):
        self.frames = frames
        self.frame_index = 0
        super().__init__(pos, self.frames[self.frame_index], group)

    def animate(self, dt):
        self.frame_index += s.ANIMATION_SPEED * dt
        self.frame_index = (
            0 if self.frame_index >= len(self.frames) else self.frame_index
        )
        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


class Coin(Animated):
    def __init__(self, pos, frames, group):
        super().__init__(pos, frames, group)
        self.rect = self.image.get_rect(center=pos)


class Player(Generic):
    def __init__(self, pos, group, collision_sprites):
        super().__init__(pos, pygame.Surface((90, 127)), group)
        self.image.fill("green")

        self.speed = vector()
        self.touch_ground = True

        self.hitbox = self.rect.inflate(-50, -15)
        self.shift = vector(self.hitbox.topleft)
        self.collision_sprites = collision_sprites

    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_d]:
            self.speed.x = 1
        elif keys[pygame.K_a]:
            self.speed.x = -1
        else:
            self.speed.x = 0

        if keys[pygame.K_w] and self.touch_ground:
            self.speed.y = -2

    def move(self, dt):
        self.shift.x += self.speed.x * s.PLAYER_SPEED * dt
        self.hitbox.x = round(self.shift.x)
        self.rect.centerx = self.hitbox.centerx
        self.collistion_check("X")

        self.gravity_pull(dt)
        self.hitbox.y = round(self.shift.y)
        self.rect.centery = self.hitbox.centery
        self.collistion_check("Y")

    def gravity_pull(self, dt):
        self.speed.y += s.GRAVITY * dt
        self.shift.y += self.speed.y

    def check_ground(self):
        bottom_rect = pygame.Rect(
            self.hitbox.left, self.hitbox.bottom, self.hitbox.width, 2
        )
        ground_sprites = [
            sprite
            for sprite in self.collision_sprites
            if sprite.rect.colliderect(bottom_rect)
        ]
        self.touch_ground = True if ground_sprites else False

    def collistion_check(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox):
                if direction == "X":
                    if self.speed.x > 0:
                        self.hitbox.right = sprite.rect.left
                    if self.speed.x < 0:
                        self.hitbox.left = sprite.rect.right
                    self.rect.centerx = self.hitbox.centerx
                    self.shift.x = self.hitbox.x
                    self.speed.x = 0

                if direction == "Y":
                    if self.speed.y > 0:
                        self.hitbox.bottom = sprite.rect.top
                    if self.speed.y < 0:
                        self.hitbox.top = sprite.rect.bottom
                    self.rect.centery = self.hitbox.centery
                    self.shift.y = self.hitbox.y
                    self.speed.y = 0

    def update(self, dt):
        self.input()
        self.move(dt)
        self.check_ground()


class Enemy(Generic):
    def __init__(self, pos, group, player, collision_sprites):
        super().__init__(pos, pygame.Surface((80, 80)), group)
        self.image.fill("blue")
        self.speed = vector()
        self.thrust = vector()
        self.drag = vector()
        self.shift = vector(self.rect.topleft)
        self.drag_coeff = 0.01

        self.player = player
        self.collision_sprites = collision_sprites
        self.last_target = None
        self.target = vector(self.rect.center)

        self.hitbox = self.rect.inflate(-40, -40)
        self.repulsion_rect = self.rect.inflate(40, 40)
        self.repulsion = vector()

    def input(self):
        target_diff = vector(pygame.mouse.get_pos()) - vector(self.rect.center)
        if target_diff != vector((0, 0)):
            self.thrust = 500 * target_diff.normalize()

    def enemy_vision(self):
        obstuctions = []
        for sprite in self.collision_sprites:
            if sprite.rect.clipline(self.player.rect.center, self.rect.center):
                obstuctions.append(sprite)

        if obstuctions:
            self.terget = self.last_target
            self.image.fill("blue")
        else:
            self.target = vector(self.player.rect.center)
            self.last_target = self.target
            self.image.fill("red")

    def friction(self):
        self.drag.x = (
            self.drag_coeff * (self.speed.x**2)
            if self.speed.x < 0
            else -self.drag_coeff * (self.speed.x**2)
        )
        self.drag.y = (
            self.drag_coeff * (self.speed.y**2)
            if self.speed.y < 0
            else -self.drag_coeff * (self.speed.y**2)
        )

    def move(self, dt):
        self.friction()
        self.repulsion_check()

        self.speed.x += (self.thrust.x + self.drag.x + 200 * self.repulsion.x) * dt
        self.speed.y += (self.thrust.y + self.drag.y + 200 * self.repulsion.y) * dt

        self.shift.x += self.speed.x * dt
        self.hitbox.x = round(self.shift.x)
        self.repulsion_rect.centerx = self.hitbox.centerx
        self.collistion_check("X")
        self.rect.centerx = self.hitbox.centerx

        self.shift.y += self.speed.y * dt
        self.hitbox.y = round(self.shift.y)
        self.repulsion_rect.centery = self.hitbox.centery
        self.collistion_check("Y")
        self.rect.centery = self.hitbox.centery

    def repulsion_check(self):
        self.repulsion = vector()
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.repulsion_rect):
                repulsion_distance = vector(self.rect.center) - vector(
                    sprite.rect.center
                )
                repulsion_multi = repulsion_distance.normalize() * (
                    100 / repulsion_distance.magnitude()
                )
                self.repulsion += repulsion_multi

        if abs(self.repulsion.x) < 2:
            self.repulsion.x = 0
        if abs(self.repulsion.y) < 2:
            self.repulsion.y = 0

    def collistion_check(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox):
                if direction == "X":
                    if self.speed.x > 0:
                        self.hitbox.right = sprite.rect.left
                    if self.speed.x < 0:
                        self.hitbox.left = sprite.rect.right
                    self.shift.x = self.hitbox.x
                    self.speed.x = -self.speed.x

                if direction == "Y":
                    if self.speed.y > 0:
                        self.hitbox.bottom = sprite.rect.top
                    if self.speed.y < 0:
                        self.hitbox.top = sprite.rect.bottom
                    self.shift.y = self.hitbox.y
                    self.speed.y = -self.speed.y

    def update(self, dt):
        self.enemy_vision()
        self.input()
        self.move(dt)


class Prop(Generic):
    def __init__(self, pos, surf, group):
        super().__init__(pos, surf, group)