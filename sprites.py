import pygame
import os
from os.path import join
from settings import *
import math

class Sprite(pygame.sprite.Sprite):
    """Basic sprite for ground tiles and decorative map objects."""
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.ground = True

class CollisionSprite(pygame.sprite.Sprite):
    """Invisible sprite used for collision areas."""
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, enemy_type, hp, path, groups, collision_sprites, player):
        super().__init__(groups)
        self.type = enemy_type
        self.max_hp = hp
        self.hp = hp
        self.path = path
        self.player = player
        self.collision_sprites = collision_sprites

        self.last_attack_time = 0
        self.attack_delay = 600
        self.state = 'walk_right'
        self.frame_index = 0
        self.animation_speed = 12

        self.frames = {state: [] for state in [
            'walk_left', 'walk_right', 'attack_left', 'attack_right',
            'hurt_left', 'hurt_right', 'death_left', 'death_right']}
        self.load_enemy_images()

        self.image = self.frames['walk_right'][0] if self.frames['walk_right'] else pygame.Surface((32, 32))
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-150, -160)
        self.speed = 80
        self.is_dead = False

    def load_enemy_images(self):
        scale_factor = 2.0
        for state in self.frames.keys():
            folder = join(self.path, state)
            temp = []

            if not os.path.exists(folder):
                self.frames[state] = []
                continue

            for _, _, fnames in os.walk(folder):
                numeric_files = sorted([
                    f for f in fnames if f.endswith('.png') and f.rsplit('.', 1)[0].isdigit()
                ], key=lambda x: int(x.split('.')[0]))

                for f in numeric_files:
                    surf = pygame.image.load(join(folder, f)).convert_alpha()
                    w, h = int(surf.get_width() * scale_factor), int(surf.get_height() * scale_factor)
                    temp.append(pygame.transform.scale(surf, (w, h)))

            self.frames[state] = temp

    def take_damage(self, amt):
        if self.is_dead:
            return
        self.hp -= amt
        if self.hp <= 0:
            self.is_dead = True
            self.state = 'death_left' if 'left' in self.state else 'death_right'
            self.frame_index = 0
        else:
            self.state = 'hurt_left' if 'left' in self.state else 'hurt_right'
            self.frame_index = 0

    def collision(self):
        for c in self.collision_sprites:
            if c.rect.colliderect(self.hitbox_rect):
                self.hitbox_rect.center = self.rect.center
                break

    def move(self, dt):
        direction = (pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center))
        if direction.length() > 0:
            direction = direction.normalize()

        if direction.x < 0 and not any(sub in self.state for sub in ['attack', 'hurt', 'death']):
            self.state = 'walk_left'
        elif direction.x > 0 and not any(sub in self.state for sub in ['attack', 'hurt', 'death']):
            self.state = 'walk_right'

        self.hitbox_rect.center += direction * self.speed * dt
        self.collision()
        self.rect.center = self.hitbox_rect.center

    def animate(self, dt):
        frames = self.frames.get(self.state, [pygame.Surface((32, 32))])
        self.frame_index += self.animation_speed * dt

        if self.frame_index >= len(frames):
            if 'death' in self.state:
                self.kill()
                return
            if 'attack' in self.state or 'hurt' in self.state:
                self.state = 'walk_left' if 'left' in self.state else 'walk_right'
            self.frame_index = 0

        idx = int(self.frame_index) % len(frames)
        old_center = self.rect.center
        self.image = frames[idx]
        self.rect = self.image.get_rect(center=old_center)

    def update(self, dt):
        if not self.is_dead:
            dist = (pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)).length()
            if dist < 40:
                self.attack_player()
            else:
                self.move(dt)
        self.animate(dt)

    def attack_player(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time >= self.attack_delay:
            self.last_attack_time = now
            dx = self.player.rect.centerx - self.rect.centerx
            self.state = 'attack_left' if dx < 0 else 'attack_right'
            self.frame_index = 0
            self.player.take_damage(5)

class Arrow(pygame.sprite.Sprite):
    def __init__(self, image_path, pos, direction, groups, collision_sprites):
        super().__init__(groups)
        self.collision_sprites = collision_sprites
        self.direction = direction
        self.speed = 350
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1000

        surf = pygame.image.load(image_path).convert_alpha()
        scale = 1.85
        surf = pygame.transform.scale(surf, (int(surf.get_width() * scale), int(surf.get_height() * scale)))
        angle = math.degrees(math.atan2(-direction.y, direction.x))
        self.image = pygame.transform.rotate(surf, angle)
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.spawn_time >= self.lifetime:
            self.kill()
