import os
from os.path import join
import pygame, random
from pygame.math import Vector2
from settings import (
    HP_PER_LEVEL, DMG_PER_LEVEL,
    MINIBOSS_SPECIAL_MULT, MINIBOSS_SPECIAL_CD_MS,
    TILE_SIZE
)
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
    """ศัตรูที่มีเลเวล – HP – ดาเมจตามเลเวล"""
    def __init__(
        self, pos, enemy_type, level,
        base_hp, base_dmg, path,
        groups, collision_sprites, player, exp_reward,
        is_miniboss=False
    ):
        super().__init__(groups)
        self.type   = enemy_type
        self.level  = level
        self.path = path
        self.player = player
        self.collision_sprites = collision_sprites
        self.exp_reward = exp_reward
        self.is_miniboss = is_miniboss
        self.special_cd = MINIBOSS_SPECIAL_CD_MS
        self.last_special = 0  # เอาไว้จับเวลาคูลดาวน์
        self.pending_damage = 0
        self.final_hit_frame = None  # เฟรมที่จะลงดาเมจ
        self.warped = False  # ให้วาร์ปครั้งเดียว
        self.hit_frame_index = 0
        self.attack_range = 60 if is_miniboss else 40
        self.frames: dict[str, list[pygame.Surface]] = {}

        from settings import HP_PER_LEVEL, DMG_PER_LEVEL
        self.max_hp = base_hp + HP_PER_LEVEL * (level - 1)
        self.hp = self.max_hp
        # --------- Damage ---------
        if is_miniboss:
            # ★ ให้แรงขึ้นตามเลเวลผู้เล่น ★
            self.dmg_normal = base_dmg + DMG_PER_LEVEL * (level - 1)
            self.dmg_special = self.dmg_normal * MINIBOSS_SPECIAL_MULT
        else:
            # ศัตรูทั่วไป
            self.dmg_normal = base_dmg + DMG_PER_LEVEL * (level - 1)
            self.dmg_special = self.dmg_normal

        self.last_attack_time = 0
        self.attack_delay = 600
        self.state = 'walk_right'
        self.frame_index = 0
        self.animation_speed = 12
        for state in self.frames:
            if not self.frames[state]:
                self.frames[state] = [pygame.Surface((32, 32), pygame.SRCALPHA)]

        self.frames = {state: [] for state in [
            'walk_left', 'walk_right', 'attack_left', 'attack_right','special_left', 'special_right',
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
            self.player.gain_exp(self.exp_reward * self.level)  # ★ แจก EXP ★
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
        frames = self.frames[self.state]

        # ถ้าเฟรมหมด ให้รีเซ็ตเป็น 0
        if self.frame_index >= len(frames):
            self.frame_index = 0

        # ค่าดัชนีปัจจุบัน (ป้องกัน list ว่าง)
        if not frames:
            frames = [pygame.Surface((32, 32), pygame.SRCALPHA)]
            self.frames[self.state] = frames

        idx = int(self.frame_index) % len(frames)
        if self.pending_damage \
                and self.final_hit_frame is not None \
                and idx >= self.final_hit_frame:
            self.player.take_damage(self.pending_damage)
            self.pending_damage = 0
        old_mid = self.rect.midbottom
        self.image = frames[idx]
        self.rect = self.image.get_rect(midbottom=old_mid)

        # เดินอนิเมชันรอบเดียว
        self.frame_index += self.animation_speed * dt

        # ---------- เฟรมวาร์ป ----------
        if self.type == "werewolf" and self.state.startswith("special"):

            # คำนวณเฟรมสุดท้ายสกิล (ครั้งเดียว)
            if self.final_hit_frame is None:
                self.final_hit_frame = len(frames) - 1

            # เฟรม 8 : วาร์ปมาอยู่บนตัวผู้เล่น
            if idx == self.hit_frame_index and not self.warped:
                self.rect.center = self.player.rect.center
                self.warped = True
            # เฟรมสุดท้าย : ดาเมจ
            if self.pending_damage and idx == self.final_hit_frame:
                self.player.take_damage(self.pending_damage)
                self.pending_damage = 0

        # จบ hurt / attack → กลับเดิน
        if self.frame_index >= len(frames):
            if "death" in self.state:
                self.kill(); return
            if "attack" in self.state or "hurt" in self.state or "special" in self.state:
                self.state = "walk_left" if "left" in self.state else "walk_right"
            self.frame_index = 0

    def update(self, dt):
        if not self.is_dead:
            dist = (pygame.Vector2(self.player.rect.center)
                    - pygame.Vector2(self.rect.center)).length()
            if dist < self.attack_range:
                self.attack_player()
            else:
                self.move(dt)
        self.animate(dt)

    def attack_player(self):
        if self.is_dead:
            return

        now = pygame.time.get_ticks()

        # ---------- ดีเลย์รวม ----------
        if now - self.last_attack_time < self.attack_delay:
            return                    # ยังไม่ถึงเวลาออกท่าใด ๆ
        self.last_attack_time = now

        # ---------- เลือกท่า ----------
        use_special = (
                self.is_miniboss
                and self.hp / self.max_hp <= 0.75
                and now - self.last_special >= self.special_cd  # ← 5 000 ms
        )

        if self.is_miniboss:
            # --------- มินิบอส ---------
            if use_special:
                if now - self.last_special < self.attack_delay:
                    return
                self.last_special = now
                dmg = self.dmg_special
                prefix = "special"
            else:
                dmg = self.dmg_normal
                prefix = "attack"
        else:
            # --------- ศัตรูทั่วไป ---------
            dmg = self.dmg_normal
            prefix = "attack"

        # ---------- บันทึกดาเมจไว้รอเฟรมสุดท้าย ----------
        self.pending_damage = dmg

        # ---------- ตั้ง state อนิเมชัน ----------
        dx = self.player.rect.centerx - self.rect.centerx
        self.state = f"{prefix}_left" if dx < 0 else f"{prefix}_right"
        self.frame_index = 0

        # 👇 คำนวณจากอนิเมชัน "attack_*" ที่เพิ่งตั้ง
        frames_for_state = self.frames[self.state] or [pygame.Surface((32, 32))]
        self.hit_frame_index = max(0, len(frames_for_state) // 2)  # เฟรมกลาง ๆ
        self.final_hit_frame = self.hit_frame_index  # ตรงกลางคอมโบ
        if self.type == 'werewolf' and use_special:
            self.state = 'special_left' if dx < 0 else 'special_right'
            self.frame_index = 0
            self.hit_frame_index = 8  # เฟรมวาร์ป
            self.final_hit_frame = None  # ให้คำนวณใน animate()
            self.pending_damage = self.dmg_special
            self.last_special = now
            return

        if self.type == 'eliteorc' and use_special:
            # Jump-smash (ดาเมจแรง)
            self.state = 'special_left' if dx < 0 else 'special_right'
            self.frame_index = 0
            self.pending_damage = self.dmg_special * 1.5
            self.hit_frame_index = max(0, len(self.frames[self.state]) // 2)
            self.final_hit_frame = len(self.frames[self.state]) - 1  # 👈 เพิ่ม
            self.last_special = now
            return

class Arrow(pygame.sprite.Sprite):
    def __init__(self, image_or_list, pos, direction, groups,
                 collision_sprites, damage=0, speed=350, anim_fps=12):
        super().__init__(groups)


        # -------------------------------------------------
        # 1) โหลดเฟรมภาพจากไฟล์/ลิสต์ให้เรียบร้อยก่อน
        # -------------------------------------------------
        if isinstance(image_or_list, list):
            raw_frames = [pygame.image.load(p).convert_alpha()
                          for p in image_or_list]
        else:
            raw_frames = [pygame.image.load(image_or_list).convert_alpha()]

        # -------------------------------------------------
        # 2) หมุนทุกเฟรมให้ตรงกับทิศกระสุน
        # -------------------------------------------------
        angle = math.degrees(math.atan2(-direction.y, direction.x))
        self.frames = [pygame.transform.rotate(surf, angle)
                       for surf in raw_frames]

        # -------------------------------------------------
        # 3) ตั้งค่าพื้นฐาน
        # -------------------------------------------------
        self.frame_index = 0
        self.anim_speed  = anim_fps / 1000      # เฟรมต่อ ms
        self.image       = self.frames[0]
        self.rect        = self.image.get_rect(center=pos)
        self.lifetime = 700

        shrink_x = 0.6  # เอา 60 % ของความกว้างออก
        shrink_y = 0.7  # เอา 70 % ของความสูงออก
        self.hitbox_rect = self.rect.inflate(-self.rect.width * shrink_x,
                                             -self.rect.height * shrink_y)

        # ---------- การเคลื่อนที่ ----------
        self.pos        = Vector2(pos)
        self.direction  = direction
        self.speed      = speed
        self.damage     = damage
        self.spawn_time = pygame.time.get_ticks()
        self.collision_sprites = collision_sprites

    def update(self, dt):
        # --- อนิเมชัน ---
        if len(self.frames) > 1:
            self.frame_index += self.anim_speed * dt * 1000
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]

        # --- เคลื่อนที่ (ทุกกรณี) ---
        self.pos += self.direction * self.speed * dt
        self.rect.center = round(self.pos.x), round(self.pos.y)
        self.hitbox_rect.center = self.rect.center  # ← เพิ่ม

        # --- อายุเกิน 2 วิ ลบทิ้ง ---
        if pygame.time.get_ticks() - self.spawn_time > 2000:
            self.kill()

