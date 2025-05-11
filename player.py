import pygame, os, math
from os.path import join, exists
from os import walk
from random import randint
import settings
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    EXP_BASE, EXP_GROWTH_RATE,
)
from sprites import Arrow
from pygame import Vector2

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, arrow_group, enemy_sprites):
        super().__init__(groups)
        self.collision_sprites = collision_sprites
        self.arrow_group       = arrow_group
        self.enemy_sprites     = enemy_sprites

        # Health & death state
        self.max_health = 100
        self.health = self.max_health
        self.is_dead = False
        self.death_done = False
        self.death_time = None
        self.death_delay = 700  # ms

        # LEVEL / EXP
        self.level = 1
        self.exp = 0
        self.exp_needed = EXP_BASE

        # Damage cooldown
        self.last_damage_time = 0
        self.damage_cooldown = 1000

        # ---------- Class / Job ----------
        self.job = "soldier"  # เริ่มต้น
        self.special_cd = 2500  # default 2.5 วิ
        self.last_special = 0

        # Load all animations
        self.animations = {state: [] for state in [
            'idle_left', 'idle_right', 'walk_left', 'walk_right',
            'attack_melee_left', 'attack_melee_right',
            'attack_bow_left', 'attack_bow_right',
            'hurt_left', 'hurt_right',
            'death_left', 'death_right']}
        self.load_player_images()
        self.prev_lmb = self.prev_rmb = False

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

        self.pending_actions = []

        self.debug_attack_shapes = []

    def _add_pending(self, trigger_frame, func):
        """เรียกเมธอด func() เมื่อเฟรมถึง trigger_frame"""
        self.pending_actions.append((trigger_frame, func))

    def gain_exp(self, amount: int) -> None:
        """รับ EXP แล้วเช็กเลเวลอัป"""
        self.exp += amount
        while self.exp >= self.exp_needed:
            self.exp -= self.exp_needed
            self.level += 1
            self.exp_needed = int(self.exp_needed * EXP_GROWTH_RATE)

            # อัพเกรดค่าสถานะต่าง ๆ ตามต้องการ
            self.max_health += 10
            self.health = self.max_health

    def change_job(self, job_name: str):
        # ---------- บันทึก job ----------
        self.job = job_name

        # ---------- สเตตัส ----------
        if job_name == "knight":
            self.max_health += 100;  self.special_cd = 2500
        elif job_name == "wizard":
            self.max_health -= 50;  self.special_cd = 1800
        elif job_name == "judiciar":
            self.max_health += 200; self.special_cd = 3000
        self.health = self.max_health

        # ---------- โหลด sprite ใหม่ ----------
        self.load_player_images(job_name)
        self.state = 'idle_right'
        self.frame_index = 0
        self.image = self.animations[self.state][0]
        # hitbox อาจใหญ่ขึ้น/เล็กลง => รีเซ็ตขนาดให้ตรง sprite ใหม่
        self.rect = self.image.get_rect(center=self.rect.center)
        self.hitbox_rect = self.rect.inflate(-160, -180)
        self.hitbox_rect.midbottom = self.rect.midbottom



    # --------------------------------------------
    #      LOAD SPRITE SHEETS ตาม 'job' ปัจจุบัน
    # --------------------------------------------
    def load_player_images(self, job: str = None):
        job = job or self.job
        base_folder = join('images', job)
        scale_factor = 2.0

        for state in self.animations.keys():
            folder_path = join(base_folder, state)
            frames = []

            if not exists(folder_path):
                # ถ้าโฟลเดอร์นี้ไม่มี ให้ใส่ surface เปล่าแทน
                self.animations[state] = [pygame.Surface((64, 64))]
                continue

            for _, _, fnames in walk(folder_path):
                numeric_files = sorted([
                    f for f in fnames
                    if f.endswith('.png') and f.rsplit('.', 1)[0].isdigit()
                ], key=lambda x: int(x.split('.')[0]))

                for f in numeric_files:
                    surf = pygame.image.load(join(folder_path, f)).convert_alpha()
                    w, h = int(surf.get_width() * scale_factor), int(surf.get_height() * scale_factor)
                    frames.append(pygame.transform.scale(surf, (w, h)))

            self.animations[state] = frames or [pygame.Surface((64, 64))]

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

        # ---------------- Movement ----------------
        keys = pygame.key.get_pressed()
        self.direction.x = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        self.direction.y = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        if self.direction.x < 0:
            self.facing = "left"
        elif self.direction.x > 0:
            self.facing = "right"

        # ---------------- Mouse ----------------
        lmb, _, rmb = pygame.mouse.get_pressed()
        just_lmb = lmb and not self.prev_lmb
        just_rmb = rmb and not self.prev_rmb
        self.prev_lmb, self.prev_rmb = lmb, rmb

        now = pygame.time.get_ticks()

        # ── R-CLICK (สกิล/ยิงธนู) ────────────────────────────────
        if just_rmb \
                and not self.pending_actions \
                and 'attack_bow' not in self.state:  # ★ อย่าแทรกขณะยิงธนูยังเล่นอยู่
            self._trigger_rmb(now)  # (ย้ายโค้ดฝั่งขวาไปใส่ใน helper)
            # ยกเลิก L-MB ของเฟรมนี้
            just_lmb = False

        # ── L-CLICK (โจมตีประชิด) ───────────────────────────────
        # ห้าม L-MB ถ้าอนิเมชันยิงธนูยังเล่น หรือยังมี action ค้าง
        if just_lmb \
                and not self.pending_actions \
                and 'attack_bow' not in self.state \
                and now - self.last_attack_time >= self.attack_cooldown:
            self.last_attack_time = now
            self._trigger_lmb()

        # ---------------- Idle / Walk state ----------------
        if self.state not in [
            "attack_melee_left","attack_melee_right",
            "attack_bow_left","attack_bow_right",
            "hurt_left","hurt_right",
            "death_left","death_right"]:
            self.state = ("idle_" if self.direction.length() == 0 else "walk_") + self.facing

    def _trigger_rmb(self, now):
        if self.job == "knight" and now - self.last_special >= self.special_cd:
            self.knight_special();
            self.last_special = now
        elif self.job == "wizard" and now - self.last_special >= self.special_cd:
            self.queue_wizard_fire()  # last_special เซ็ตภายหลัง
        elif self.job == "judiciar" and now - self.last_special >= self.special_cd:
            self.judiciar_chop();
            self.last_special = now
        elif self.job == "soldier" and now - self.last_shoot_time >= self.shoot_cooldown:
            self.last_shoot_time = now;
            self.queue_arrow_shot()

        self.state = "attack_bow_" + self.facing
        self.frame_index = 0

    def _trigger_lmb(self):
        if self.job == "knight":
            self.knight_slash()
        elif self.job == "wizard":
            self.wizard_ice_burst()
        elif self.job == "judiciar":
            self.spin_attack()
        else:
            self.melee_attack()

        self.state = "attack_melee_" + self.facing
        self.frame_index = 0

    def melee_attack(self):
        melee_range = 120  # เพิ่มระยะให้ตีโดนง่ายขึ้น
        center = self.hitbox_rect.center
        base = settings.MELEE_BASE_DMG + settings.MELEE_DMG_PER_LEVEL * (self.level - 1)
        for e in self.enemy_sprites:
            if Vector2(e.rect.center).distance_to(center) <= melee_range:
                e.take_damage(base)

    def queue_arrow_shot(self):
        """กำหนดเฟรมที่จะปล่อยลูกธนูให้ตรงกับจำนวนเฟรมจริงของอนิเมชัน"""
        state = f"attack_bow_{self.facing}"
        frames = self.animations.get(state, [])
        trigger = max(0, len(frames) - 1)  # ถ้ามี 1 เฟรม = 0
        self._add_pending(trigger, self.fire_arrow)

    # player.py  ── ภายในคลาส Player (วางใกล้ๆ queue_arrow_shot ก็ได้)
    def queue_wizard_fire(self):
        """ต่อคิวปล่อยลูกไฟที่เฟรมสุดท้ายของอนิเมชันยิง"""
        state = f"attack_bow_{self.facing}"
        frames = self.animations.get(state, [])
        trigger = max(0, len(frames) - 1)  # มีกี่เฟรมก็ใช้เฟรมสุดท้าย

        # ฟังก์ชันจริงที่สร้างกระสุน + เซ็ตคูลดาวน์
        def _do_fire():
            self.wizard_fire_arrow()
            self.last_special = pygame.time.get_ticks()  # เริ่มคูลดาวน์หลังปล่อยจริง

        self._add_pending(trigger, _do_fire)

    def fire_arrow(self):
        """ยิงลูกธนู (Soldier) หรือใช้เป็น fallback projectile"""
        # ---------- ทิศทาง ----------
        mouse_pos = Vector2(pygame.mouse.get_pos())
        center_scr = Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        direction = (mouse_pos - center_scr).normalize() if mouse_pos != center_scr else Vector2(1, 0)

        # ---------- จุดเกิด ----------
        offset = Vector2(+30, -10) if self.facing == 'right' else Vector2(-30, -10)
        spawn_pos = Vector2(self.rect.center) + offset

        # ---------- หา “รูป” กระสุน ----------
        folder = join('images', 'projectiles', 'arrow')  # <— แนะนำให้ทำโฟลเดอร์นี้
        if os.path.isdir(folder):
            frames = [join(folder, f)
                      for f in sorted(os.listdir(folder))
                      if f.endswith('.png')]
            img_arg = frames
        else:  # ไม่มีโฟลเดอร์ => ใช้ไฟล์เดี่ยว
            img_arg = join('images', 'projectiles', 'arrow.png')

        Arrow(
            img_arg,
            spawn_pos,
            direction,
            (self.arrow_group, self.groups()[0]),  # → AllSprites + arrow_group
            self.collision_sprites,
            damage=settings.ARROW_BASE_DMG + settings.ARROW_DMG_PER_LEVEL * (self.level - 1),
            speed=300  # เร็วขึ้นให้สังเกตง่าย
        )

        # -------------------------------------------------
        #                 KNIGHT ATTACKS
        # -------------------------------------------------

    def knight_slash(self):
        reach_w, reach_h = 70, 60
        hit = pygame.Rect(0, 0, reach_w, reach_h)

        if self.facing == "right":
            hit.midleft = (self.hitbox_rect.right - 2, self.hitbox_rect.centery - 6)
        else:
            hit.midright = (self.hitbox_rect.left + 2, self.hitbox_rect.centery - 6)

        dmg = settings.KNIGHT_SLASH_BASE + settings.KNIGHT_SLASH_PER_LVL * (self.level - 1)
        for e in self.enemy_sprites:
            if hit.colliderect(e.hitbox_rect):
                e.take_damage(dmg)

        self.debug_attack_shapes.append(("rect", hit.copy()))

    def knight_special(self):
        hit = pygame.Rect(0, 0, 90, 70)

        if self.facing == "right":
            hit.midleft = (self.hitbox_rect.right - 2,  # ชิดขอบจริง
                           self.hitbox_rect.centery - 6)
        else:
            hit.midright = (self.hitbox_rect.left + 2,
                            self.hitbox_rect.centery - 6)

        self.debug_attack_shapes.append(("rect", hit.copy()))
        for e in self.enemy_sprites:
            if hit.colliderect(e.hitbox_rect):
                e.take_damage(180 + 8 * (self.level - 1))

        # -------------------------------------------------
        #                 WIZARD ATTACKS
        # -------------------------------------------------

    def wizard_ice_burst(self):
        """น้ำแข็งระเบิดระยะประชิด (ใช้อนิเมชัน attack_melee_* ของตัวละคร)"""
        radius = 65
        center = self.rect.midright if self.facing == "right" else self.rect.midleft

        for e in self.enemy_sprites:
            if Vector2(e.rect.center).distance_to(center) <= radius:
                e.take_damage(140 + 7 * (self.level - 1))

        self.debug_attack_shapes.append(
            ("circle", (center, radius)))

    def wizard_fire_arrow(self):
        """ยิงลูกไฟไปยังตำแหน่งเมาส์ (projectile แบบอนิเมชันลูป)"""
        target = Vector2(pygame.mouse.get_pos())
        dir_vec = (target - Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)).normalize()
        spawn = Vector2(self.rect.center) + (Vector2(+30, -10) if self.facing == "right"
                                             else Vector2(-30, -10))

        # ----- โหลดเฟรมภาพทั้งหมดในโฟลเดอร์ fire_arrow -----
        folder = "images/wizard/fire_arrow"
        if os.path.isdir(folder):
            frames = [join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith(".png")]
        else:  # ถ้าเผลอลืมไฟล์
            frames = [join('images', 'projectiles', 'fireball.png')]

        Arrow(frames,  # << เปลี่ยนจาก path เดี่ยว เป็น list
              spawn,
              dir_vec,
              (self.arrow_group, self.groups()[0]),
              self.collision_sprites,
              damage=150 + 6 * (self.level - 1),
              speed=500)

        # -------------------------------------------------
        #               JUDICIAR ATTACKS
        # -------------------------------------------------

    def spin_attack(self):
        """Judiciar: หมุนดาบรอบตัว ฟันศัตรู 360°"""
        radius = 85
        center = Vector2(self.rect.center)
        dmg = (settings.JUDICIAR_SPIN_BASE +
               settings.JUDICIAR_SPIN_PER_LV * (self.level - 1))

        for e in self.enemy_sprites:
            if Vector2(e.rect.center).distance_to(center) <= radius:
                e.take_damage(dmg)

        # ตั้งอนิเมชัน (ใช้ชุด ‘attack_melee_...’ เดิม)
        self.state = "attack_melee_" + self.facing
        self.frame_index = 0

        self.debug_attack_shapes.append(
            ("circle", (center, radius)))

    def judiciar_chop(self):
        hit = pygame.Rect(0, 0, 75, 80)

        if self.facing == "right":
            hit.midleft = (self.hitbox_rect.right - 2,
                           self.hitbox_rect.centery - 6)
        else:
            hit.midright = (self.hitbox_rect.left + 2,
                            self.hitbox_rect.centery - 6)

        self.debug_attack_shapes.append(("rect", hit.copy()))
        for e in self.enemy_sprites:
            if hit.colliderect(e.hitbox_rect):
                e.take_damage(130 + 7 * (self.level - 1))

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
        cur = int(self.frame_index)
        for tp in self.pending_actions[:]:
            trigger, func = tp
            if cur >= trigger:
                func()
                self.pending_actions.remove(tp)

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
