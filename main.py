import pygame
import sys
from os.path import join
from random import choice
from pytmx.util_pygame import load_pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE
from groups import AllSprites
from player import Player
from sprites import Enemy, Sprite, CollisionSprite




class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("The Last Crusade")
        self.clock = pygame.time.Clock()
        self.running = True

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
            'slime': {'hp':50, 'path':'images/enemies/slime'},
            'skeleton': {'hp':100, 'path':'images/enemies/skeleton'},
            'orc': {'hp':150, 'path':'images/enemies/orc'},
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

    def spawn_enemy(self):
        """
        Choose random type from self.enemy_data, random spawn pos,
        create Enemy.
        """
        if not self.spawn_positions:
            return
        t = choice(list(self.enemy_data.keys()))
        data = self.enemy_data[t]
        pos = choice(self.spawn_positions)
        Enemy(
            pos = pos,
            enemy_type = t,
            hp = data['hp'],
            path = data['path'],
            groups = (self.all_sprites, self.enemy_sprites),
            collision_sprites = self.collision_sprites,
            player = self.player
        )

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == self.enemy_event:
                    self.spawn_enemy()

            self.all_sprites.update(dt)

            # arrow vs enemy collisions
            collisions = pygame.sprite.groupcollide(
                self.arrow_sprites, self.enemy_sprites,
                False, False, pygame.sprite.collide_mask
            )
            for arrow, enemies in collisions.items():
                for e in enemies:
                    e.take_damage(50)
                arrow.kill()

            # player vs enemy
            hits = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask)
            if hits:
                now = pygame.time.get_ticks()
                if now - self.player.last_damage_time >= self.player.damage_cooldown:
                    self.player.take_damage(10)
                    self.player.last_damage_time = now

            # check if player is dead
            if self.player.is_dead and self.player.death_done:
                self.show_game_over()
                self.running=False

            # draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.hitbox_rect.center)
            self.draw_health_bar()
            pygame.display.update()

        pygame.quit()
        sys.exit()

    def draw_health_bar(self):
        bw = 300
        bh = 25
        x = 20
        y = 20
        ratio = max(self.player.health,0)/self.player.max_health
        cw = int(bw * ratio)
        pygame.draw.rect(self.display_surface,(50,50,50),(x,y,bw,bh))
        pygame.draw.rect(self.display_surface,(200,0,0),(x,y,cw,bh))

    def show_game_over(self):
        font = pygame.font.SysFont(None,120)
        txt = font.render("GAME OVER", True, (255,0,0))
        r = txt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
        self.display_surface.fill('black')
        self.display_surface.blit(txt, r)
        pygame.display.update()
        pygame.time.delay(2000)

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
        game = Game()
        print(f"Starting game with player name: {player_name}")
        game.run()
    else:
        pygame.quit()
        sys.exit()
