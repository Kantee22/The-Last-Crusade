import pygame
import sys
from os.path import join
from random import choice
from pytmx.util_pygame import load_pygame
import random
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE,ARROW_BASE_DMG,ARROW_DMG_PER_LEVEL,
    MINIBOSS_DMG, MINIBOSS_HP, MINIBOSS_EXP, MINIBOSS_NAME, MINIBOSS_IMG_PATH, MINIBOSS_TRIGGER_LEVEL
    ,GAME_TIME_LIMIT, WEREWOLF_HP, WEREWOLF_DMG, WEREWOLF_EXP, WEREWOLF_NAME, WEREWOLF_IMG_PATH, WEREWOLF_TRIGGER_LV,
    WEREWOLF_SPECIAL_CD, ELITE_HP, ELITE_DMG, ELITE_EXP, ELITE_NAME, ELITE_IMG_PATH, ELITE_TRIGGER_LV, ELITE_SPECIAL_CD)
from groups import AllSprites
from player import Player
from sprites import Enemy, Sprite, CollisionSprite
import csv, os
from datetime import datetime      # ⬅ เพิ่ม

CSV_PATH = "runs.csv"



class Game:
    def __init__(self, player_name):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("The Last Crusade")
        self.clock = pygame.time.Clock()
        self.running = True
        self.player_name = player_name  # ⬅ เก็บไว้
        self.start_time = pygame.time.get_ticks()

        self.miniboss_spawned = False
        self.miniboss = None
        self.miniboss_defeated = False

        self.miniboss2_spawned = False
        self.miniboss2 = None
        self.elite_spawned = False
        self.elite = None

        self.class_chosen = False
        self.showing_class_menu = False

        self.start_time = pygame.time.get_ticks()

        # sprite groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.arrow_sprites = pygame.sprite.Group()

        # spawn event
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 2000)  # spawn every 2 seconds
        self.spawn_positions = []

        # enemy data (three example types)
        self.enemy_data = {
            'slime': {'hp': 50, 'dmg': 5, 'exp': 25, 'path': 'images/enemies/slime'},
            'skeleton': {'hp': 90, 'dmg': 10, 'exp': 40, 'path': 'images/enemies/skeleton'},
            'orc': {'hp': 150, 'dmg': 15, 'exp': 75, 'path': 'images/enemies/orc'},
        }

        self.setup_map()

    def setup_map(self):
        """
        Load Tiled map from data/maps/world.tmx (edit as needed).
        """
        tmx_map = load_pygame(join('data','maps','world.tmx'))

        # ground layer
        for x,y,image in tmx_map.get_layer_by_name('Ground').tiles():
            Sprite((x*TILE_SIZE,y*TILE_SIZE), image, self.all_sprites)

        # object & collisions
        for obj in tmx_map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x,obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in tmx_map.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            CollisionSprite((obj.x,obj.y), surf, self.collision_sprites)

        # player & spawns
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    (obj.x,obj.y),
                    self.all_sprites,
                    self.collision_sprites,
                    self.arrow_sprites,
                    self.enemy_sprites
                )
            else:
                self.spawn_positions.append((obj.x,obj.y))

    @staticmethod
    def collide_hitbox(sprite_a, sprite_b):
        return sprite_a.hitbox_rect.colliderect(sprite_b.hitbox_rect)

    def spawn_enemy(self):
        """สุ่มสร้างศัตรูธรรมดา ถ้าไม่มีบอสมีชีวิตอยู่"""
        # --- ถ้ามีมินิบอส/Boss ตัวใดยังไม่ตาย → ไม่สปอว์น ---
        if (self.miniboss and not self.miniboss.is_dead) \
                or (self.miniboss2 and not self.miniboss2.is_dead) \
                or (self.elite and not self.elite.is_dead):
            return
        if not self.spawn_positions:
            return

        pos   = random.choice(self.spawn_positions)
        etype = random.choice(list(self.enemy_data.keys()))
        data  = self.enemy_data[etype]

        # เลเวลใกล้ผู้เล่น (±1) อย่างน้อย 1
        player_lvl = self.player.level
        level = random.randint(max(1, player_lvl - 1), player_lvl + 1)

        Enemy(
            pos      = pos,
            enemy_type = etype,
            level    = level,
            exp_reward=data['exp'],
            base_hp  = data['hp'],
            base_dmg = data['dmg'],
            path     = data['path'],
            groups   = (self.all_sprites, self.enemy_sprites),
            collision_sprites = self.collision_sprites,
            player   = self.player
        )

    def spawn_miniboss(self):
        """สปอว์นมินิบอสครั้งเดียว แล้วลบศัตรูอื่นออก"""
        self.miniboss_spawned = True

        # ลบศัตรูปกติทั้งหมด
        for e in list(self.enemy_sprites):
            e.kill()

        # ตำแหน่งเกิด – หา spawn point ที่ใกล้ผู้เล่น (< 500px) ไม่ก็กลางจอ
        near = [p for p in self.spawn_positions
                if pygame.Vector2(p).distance_to(self.player.rect.center) < 500]
        pos = choice(near) if near else (self.player.rect.centerx + 150, self.player.rect.centery)

        # สร้างมินิบอส
        self.miniboss = Enemy(
            pos=pos, enemy_type='miniboss', level=self.player.level,
            base_hp=MINIBOSS_HP, base_dmg=MINIBOSS_DMG,
            path=MINIBOSS_IMG_PATH,
            groups=(self.all_sprites, self.enemy_sprites),
            collision_sprites=self.collision_sprites,
            player=self.player,
            exp_reward=MINIBOSS_EXP,
            is_miniboss=True
        )

    def spawn_boss(self, name, hp, dmg, exp, path,
                   special_cd=0, dmg_special=0,  # ★ ค่าปริยาย
                   is_miniboss=False, is_elite=False):

        # เคลียร์ศัตรูธรรมดาทั้งหมด
        for e in list(self.enemy_sprites):
            e.kill()

        boss = Enemy(
            self.player.rect.center + pygame.Vector2(250, 0),
            name.lower(), self.player.level,
            hp, dmg, path,
            (self.all_sprites, self.enemy_sprites),
            self.collision_sprites, self.player,
            exp, is_miniboss or is_elite
        )
        # ---------- กำหนดสกิล ----------
        boss.special_cd = special_cd
        boss.dmg_special = dmg_special
        boss.last_special = -9999
        return boss

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == self.enemy_event:
                    self.spawn_enemy()

            self.all_sprites.update(dt)

            elapsed_sec = (pygame.time.get_ticks() - self.start_time) // 1000
            elapsed_sec = (pygame.time.get_ticks() - self.start_time) // 1000
            lv_cond = self.player.level >= ELITE_TRIGGER_LV  # เลเวล 30 ขึ้นไป
            time_cond = elapsed_sec >= GAME_TIME_LIMIT  # หรือครบ 10 นาที

            # --- Mini-boss #1 (เดิม) ---
            if not self.miniboss_spawned and not self.miniboss_defeated \
                    and self.player.level >= MINIBOSS_TRIGGER_LEVEL:
                self.miniboss = self.spawn_boss(MINIBOSS_NAME, MINIBOSS_HP,
                                                MINIBOSS_DMG, MINIBOSS_EXP,
                                                MINIBOSS_IMG_PATH, is_miniboss=True)
                self.miniboss_spawned = True

            if not self.miniboss2_spawned and self.player.level >= WEREWOLF_TRIGGER_LV:
                self.miniboss2 = self.spawn_boss(
                    WEREWOLF_NAME, WEREWOLF_HP, WEREWOLF_DMG, WEREWOLF_EXP,
                    WEREWOLF_IMG_PATH, WEREWOLF_SPECIAL_CD, WEREWOLF_DMG * 2,
                    is_miniboss=True)
                self.miniboss2_spawned = True

            # Elite Orc  (LV30 หรือ 10 นาที)
            if not self.elite_spawned and (lv_cond or time_cond):
                self.elite = self.spawn_boss(
                    ELITE_NAME, ELITE_HP, ELITE_DMG, ELITE_EXP,
                    ELITE_IMG_PATH, ELITE_SPECIAL_CD, ELITE_DMG * 2.5,
                    is_elite=True)
                self.elite_spawned = True

            if self.miniboss and self.miniboss.is_dead and self.miniboss_spawned:
                self.miniboss_spawned = False
                self.miniboss_defeated = True  # ★ เคยกำจัดแล้ว
                self.miniboss = None

            # ถ้า player ถึง LV 10 แล้วยังไม่ได้เรียกมินิบอส → สปอว์น
            if (
                    not self.miniboss_spawned
                    and not self.miniboss_defeated
                    and self.player.level >= MINIBOSS_TRIGGER_LEVEL
            ):
                self.spawn_miniboss()

            # arrow vs enemy collisions
            base = ARROW_BASE_DMG + (self.player.level - 1) * ARROW_DMG_PER_LEVEL
            for arrow, enemies in pygame.sprite.groupcollide(
                    self.arrow_sprites,
                    self.enemy_sprites,
                    False, False,
                    self.collide_hitbox  # ← อ้างผ่าน self
            ).items():
                dmg_each = arrow.damage if getattr(arrow, "damage", 0) else base
                for e in enemies:
                    e.take_damage(dmg_each)
                arrow.kill()

            if not self.class_chosen and self.player.level >= 15 and not self.showing_class_menu:
                self.showing_class_menu = True
                choice = self.show_class_menu(self.display_surface)
                self.player.change_job(choice)
                self.class_chosen = True
                self.showing_class_menu = False

            # check if player is dead
            if self.player.is_dead and self.player.death_done:
                self.show_game_over()
                self._log_run(False)
                self.running=False

            if self.elite and self.elite.is_dead:
                self.show_victory()
                self._log_run(True)
                self.running = False

            # draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.hitbox_rect.center)
            self.draw_boss_hud()
            self.draw_timer()
            self.draw_health_bar()
            pygame.display.update()

        pygame.quit()
        sys.exit()

    def show_victory(self):
        font = pygame.font.SysFont(None, 60)
        msg = font.render("Glory to the Victor – The Crusade Ends in Light", True, (255, 255, 0))
        r = msg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.display_surface.fill('black')
        self.display_surface.blit(msg, r)
        pygame.display.update()
        pygame.time.delay(4000)

    def draw_timer(self):
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        mins, secs = divmod(elapsed, 60)
        txt = f"{mins:02}:{secs:02}"
        font = pygame.font.SysFont(None, 40)
        surf = font.render(txt, True, (255, 255, 255))
        self.display_surface.blit(surf, surf.get_rect(topright=(WINDOW_WIDTH - 20, 20)))

    def draw_boss_hud(self):
        boss = self.elite or self.miniboss2 or self.miniboss
        if not boss or boss.is_dead:
            return

        # ---------- พารามิเตอร์หลอด ----------
        bar_w, bar_h = 500, 24
        x = (WINDOW_WIDTH - bar_w) // 2
        y = WINDOW_HEIGHT - bar_h - 30
        ratio = max(boss.hp, 0) / boss.max_hp

        # ---------- วาด ----------
        pygame.draw.rect(self.display_surface, (50, 50, 50), (x, y, bar_w, bar_h))
        pygame.draw.rect(self.display_surface, (200, 0, 0), (x, y, bar_w * ratio, bar_h))

        font = pygame.font.SysFont(None, 30)
        name_surf = font.render(boss.type.upper(), True, (255, 255, 255))
        self.display_surface.blit(name_surf, name_surf.get_rect(midbottom=(WINDOW_WIDTH // 2, y - 6)))

    def draw_health_bar(self):
        bw = 300
        bh = 25
        x = 20
        y = 20
        ratio = max(self.player.health,0)/self.player.max_health
        cw = int(bw * ratio)
        pygame.draw.rect(self.display_surface,(50,50,50),(x,y,bw,bh))
        pygame.draw.rect(self.display_surface,(200,0,0),(x,y,cw,bh))

        bar_w, bar_h = 200, 18
        x, y = 20, 60
        ratio = self.player.exp / self.player.exp_needed
        pygame.draw.rect(self.display_surface, (40, 40, 40), (x, y, bar_w, bar_h))
        pygame.draw.rect(self.display_surface, (0, 120, 255), (x, y, bar_w * ratio, bar_h))
        font = pygame.font.SysFont(None, 26)  # local
        lvl_txt = font.render(f"LV {self.player.level}", True, (255, 255, 0))
        self.display_surface.blit(lvl_txt, (x, y - 22))

    def show_game_over(self):
        font = pygame.font.SysFont(None,120)
        txt = font.render("GAME OVER", True, (255,0,0))
        r = txt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
        self.display_surface.fill('black')
        self.display_surface.blit(txt, r)
        pygame.display.update()
        pygame.time.delay(2000)

    def show_class_menu(self, screen):      # ← เพิ่ม self
        font = pygame.font.SysFont(None, 70)
        knight_btn  = pygame.Rect(0, 0, 300, 90)
        knight_btn.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 120)
        wizard_btn = pygame.Rect(0, 0, 300, 90);
        wizard_btn.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        judiciar_btn = pygame.Rect(0, 0, 300, 90);
        judiciar_btn.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 120)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if knight_btn.collidepoint(event.pos):   return "knight"
                    if wizard_btn.collidepoint(event.pos):   return "wizard"
                    if judiciar_btn.collidepoint(event.pos): return "judiciar"

            screen.fill((25, 25, 25))
            pygame.draw.rect(screen, (180, 180, 180), knight_btn);
            screen.blit(font.render("Knight", True, (0, 0, 0)), knight_btn.move(65, 15))
            pygame.draw.rect(screen, (180, 180, 180), wizard_btn);
            screen.blit(font.render("Wizard", True, (0, 0, 0)), wizard_btn.move(65, 15))
            pygame.draw.rect(screen, (180, 180, 180), judiciar_btn);
            screen.blit(font.render("Judiciar", True, (0, 0, 0)), judiciar_btn.move(50, 15))
            pygame.display.update()

    def _miniboss_progress(self) -> str:
        killed = []
        if getattr(self, "miniboss", None) and self.miniboss.is_dead:
            killed.append("skeleton")
        if getattr(self, "miniboss2", None) and self.miniboss2.is_dead:
            killed.append("werewolf")
        return ",".join(killed) or "none"

    def _log_run(self, victory: bool):
        secs = (pygame.time.get_ticks() - self.start_time) // 1000
        row = [
            self.player_name,
            secs,
            self.player.job,  # ‘soldier’ หากไม่เคยเปลี่ยนคลาส
            self.player.level,
            self._miniboss_progress(),
            int(victory)  # 1 ถ้าชนะ, 0 ถ้าตาย
        ]

        write_header = not os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["Player", "Play_Time_Sec", "Class", "Level",
                            "Miniboss_Killed", "Beat_Final_Boss"])
            w.writerow(row)

def show_menu(screen):
    """ แสดงหน้าเมนูหลัก มีตัวเลือก Play, Leaderboard, Quit """
    font = pygame.font.SysFont(None, 80)
    clock = pygame.time.Clock()

    # โหลดรูปภาพเมนู (ภาพที่อัปโหลดไว้ ตั้งชื่อไฟล์ตามที่ต้องการ)
    try:
        bg_image = pygame.image.load(join('images', 'menu', 'menu_background.png')).convert()
        # สมมติว่า bg_image คือรูปที่ pygame.image.load(...) ได้มา
        bg_image = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))

    except:
        # ถ้าโหลดไม่ได้ ให้ใส่สีพื้นธรรมดา
        bg_image = None

    # ตำแหน่งของแต่ละปุ่ม
    play_rect = pygame.Rect(0, 0, 400, 80)
    leaderboard_rect = pygame.Rect(0, 0, 400, 80)
    quit_rect = pygame.Rect(0, 0, 400, 80)

    # จัดให้อยู่กึ่งกลางจอ
    play_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100)
    leaderboard_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    quit_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100)

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                if play_rect.collidepoint(mouse_pos):
                    # กดปุ่ม Play -> ดึงชื่อผู้เล่น -> return 'play', ชื่อ
                    player_name = get_player_name(screen)
                    return 'play', player_name
                elif leaderboard_rect.collidepoint(mouse_pos):
                    # กดปุ่ม Leaderboard (ยังไม่ทำอะไร)
                    print("Leaderboard clicked (ยังไม่เปิดใช้งาน)")
                elif quit_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        # วาด background
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((50, 50, 50))  # สีเทาถ้าไม่เจอรูป

        # วาดปุ่ม Play
        pygame.draw.rect(screen, (200, 200, 200), play_rect)
        screen.blit(font.render("Play", True, (0, 0, 0)), (play_rect.x + 145, play_rect.y + 10))

        # วาดปุ่ม Leaderboard
        pygame.draw.rect(screen, (200, 200, 200), leaderboard_rect)
        screen.blit(font.render("Leaderboard", True, (0, 0, 0)), (leaderboard_rect.x + 25, leaderboard_rect.y + 10))

        # วาดปุ่ม Quit
        pygame.draw.rect(screen, (200, 200, 200), quit_rect)
        screen.blit(font.render("Quit", True, (0, 0, 0)), (quit_rect.x + 145, quit_rect.y + 10))

        pygame.display.update()


def get_player_name(screen):
    """ ฟังก์ชันให้ผู้เล่นกรอกชื่อ ก่อนเข้าเกม """
    font = pygame.font.SysFont(None, 60)
    clock = pygame.time.Clock()

    input_box = pygame.Rect(0, 0, 400, 60)
    input_box.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    user_text = ""

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # ถ้ากด Enter
                    return user_text  # ส่งชื่อผู้เล่นกลับ
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    # เพิ่มตัวอักษรลงไป ถ้าต้องการจำกัดความยาวให้เช็คได้
                    user_text += event.unicode

        screen.fill((0, 0, 0))
        # แสดงข้อความ "Enter your name:"
        label_surf = font.render("Enter your name:", True, (255, 255, 255))
        label_rect = label_surf.get_rect(midbottom=(WINDOW_WIDTH // 2, input_box.y - 10))
        screen.blit(label_surf, label_rect)

        # วาดกล่อง input
        pygame.draw.rect(screen, (255, 255, 255), input_box, 2)
        text_surf = font.render(user_text, True, (255, 255, 255))
        screen.blit(text_surf, (input_box.x + 10, input_box.y + 10))

        pygame.display.update()


# -----------------------------------------------------------------------------
# ส่วน main เริ่มต้นโปรแกรม: แสดงเมนูก่อน -> เข้าเกม
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("The Last Crusade")

    # 1) เรียกหน้าเมนู
    choic, player_name = show_menu(screen)

    if choic == 'play':
        game = Game(player_name)  # ⬅ ส่งชื่อเข้าไป
        game.run()

    else:
        pygame.quit()
        sys.exit()
