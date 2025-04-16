import pygame
import os
from os.path import join, exists
from os import walk
from settings import WINDOW_WIDTH, WINDOW_HEIGHT
from sprites import Arrow
from pygame import Vector2

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, arrow_group, enemy_sprites):
        super().__init__(groups)
        self.collision_sprites = collision_sprites
        self.arrow_group = arrow_group
        self.enemy_sprites = enemy_sprites

        # Health & death state
        self.max_health = 100
        self.health = 100
        self.is_dead = False
        self.death_done = False
        self.death_time = None
        self.death_delay = 700  # ms

        # Damage cooldown
        self.last_damage_time = 0
        self.damage_cooldown = 1000

        # Load all animations
        self.animations = {state: [] for state in [
            'idle_left', 'idle_right', 'walk_left', 'walk_right',
            'attack_melee_left', 'attack_melee_right',
            'attack_bow_left', 'attack_bow_right',
            'hurt_left', 'hurt_right',
            'death_left', 'death_right']}
        self.load_player_images()

        # Initial animation state
        self.state = 'idle_right'
        self.frame_index = 0
        self.animation_speed = 12

        # Visuals and positioning
        self.image = pygame.Surface((64, 64))
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-20, -30)
        self.hitbox_rect.midbottom = self.rect.midbottom

        # Movement & direction
        self.direction = Vector2()
        self.speed = 200
        self.facing = 'right'

        # Attack timing
        self.last_attack_time = 0
        self.attack_cooldown = 700
        self.last_shoot_time = 0
        self.shoot_cooldown = 1000
        self.arrow_delay = 700
        self.arrow_ready_time = None

    def load_player_images(self):
        base_folder = join('images', 'soldier')
        scale_factor = 2.0
        for state in self.animations.keys():
            folder_path = join(base_folder, state)
            frames = []

            if not exists(folder_path):
                self.animations[state] = [pygame.Surface((64,64))]
                continue

            for _, _, fnames in walk(folder_path):
                numeric_files = sorted([
                    f for f in fnames if f.endswith('.png') and f.rsplit('.', 1)[0].isdigit()
                ], key=lambda x: int(x.split('.')[0]))

                for f in numeric_files:
                    surf = pygame.image.load(join(folder_path, f)).convert_alpha()
                    w, h = int(surf.get_width() * scale_factor), int(surf.get_height() * scale_factor)
                    frames.append(pygame.transform.scale(surf, (w, h)))

            self.animations[state] = frames or [pygame.Surface((64,64))]

    def take_damage(self, amt):
        if self.is_dead:
            return
        self.health -= amt
        if self.health <= 0:
            self.die()
        else:
            self.state = 'hurt_left' if 'left' in self.state else 'hurt_right'
            self.frame_index = 0

    def die(self):
        self.is_dead = True
        self.death_time = pygame.time.get_ticks()
        self.state = 'death_left' if 'left' in self.state else 'death_right'
        self.frame_index = 0

    def move(self, dt):
        if self.is_dead:
            return
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    elif self.direction.x < 0:
                        self.hitbox_rect.left = sprite.rect.right
                if direction == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top
                    elif self.direction.y < 0:
                        self.hitbox_rect.top = sprite.rect.bottom

    def input(self):
        if self.is_dead:
            self.direction = Vector2()
            return

        keys = pygame.key.get_pressed()
        self.direction.x = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        self.direction.y = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])

        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        # Update facing
        if self.direction.x < 0:
            self.facing = 'left'
        elif self.direction.x > 0:
            self.facing = 'right'

        now = pygame.time.get_ticks()
        mouse_btns = pygame.mouse.get_pressed()

        if mouse_btns[0] and now - self.last_attack_time >= self.attack_cooldown:
            self.last_attack_time = now
            self.melee_attack()
            self.state = 'attack_melee_' + self.facing
            self.frame_index = 0

        if mouse_btns[2] and now - self.last_shoot_time >= self.shoot_cooldown:
            self.last_shoot_time = now
            self.arrow_ready_time = now + self.arrow_delay
            self.state = 'attack_bow_' + self.facing
            self.frame_index = 0

        if self.state not in [
            'attack_melee_left','attack_melee_right',
            'attack_bow_left','attack_bow_right',
            'hurt_left','hurt_right',
            'death_left','death_right']:
            self.state = 'idle_' + self.facing if self.direction.length() == 0 else 'walk_' + self.facing

    def melee_attack(self):
        melee_range = 100
        for e in self.enemy_sprites:
            if Vector2(e.rect.center).distance_to(Vector2(self.rect.center)) <= melee_range:
                e.take_damage(100)

    def fire_arrow(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        center_scr = pygame.Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        direction = mouse_pos - center_scr
        if direction.length() > 0:
            direction = direction.normalize()

        arrow_offset = pygame.Vector2(+30, -10) if self.facing == 'right' else pygame.Vector2(-30, -10)
        spawn_pos = pygame.Vector2(self.rect.center) + arrow_offset
        arrow_path = join('images', 'Arrow', 'Arrow01(100x100).png')

        Arrow(arrow_path, spawn_pos, direction, (self.arrow_group, self.groups()[0]), self.collision_sprites)

    def animate(self, dt):
        frames = self.animations.get(self.state, [pygame.Surface((64, 64))])
        self.frame_index += self.animation_speed * dt

        if 'death' in self.state and self.frame_index >= len(frames):
            self.frame_index = len(frames) - 1
            return

        if self.frame_index >= len(frames):
            if 'attack' in self.state or 'hurt' in self.state:
                self.state = 'idle_' + self.facing
            self.frame_index = 0

        idx = int(self.frame_index) % len(frames)
        old_center = self.rect.center
        self.image = frames[idx]
        self.rect = self.image.get_rect(center=old_center)

    def update(self, dt):
        self.input()
        now = pygame.time.get_ticks()

        if self.arrow_ready_time and now >= self.arrow_ready_time:
            self.fire_arrow()
            self.arrow_ready_time = None

        self.move(dt)
        self.animate(dt)

        # Check if death animation finished
        if self.is_dead and not self.death_done and self.death_time:
            if now - self.death_time >= self.death_delay:
                self.death_done = True
