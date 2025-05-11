import pygame
from os.path import join
from os import walk

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
TILE_SIZE = 64


# ---------- Level / EXP ----------
EXP_BASE        = 50     # EXP  Level 1 ➜ 2
EXP_GROWTH_RATE = 1.25
DMG_PER_LEVEL   = 2       # ศัตรู +DMG/เลเวล
HP_PER_LEVEL    = 10      # ศัตรู +HP /เลเวล

# ---------- Arrow damage ----------
ARROW_BASE_DMG      = 30   # ดาเมจพื้นฐาน
ARROW_DMG_PER_LEVEL = 5   # +/เลเวลผู้เล่น

# ---------- Player damage (ปรับตรงนี้ง่ายที่สุด) ----------
MELEE_BASE_DMG       = 60   # Soldier/Lv1
MELEE_DMG_PER_LEVEL  = 5

WIZARD_MELEE_BASE    = 140   # ice burst
WIZARD_MELEE_PER_LVL = 5

KNIGHT_SLASH_BASE    = 120
KNIGHT_SLASH_PER_LVL = 5

JUDICIAR_SPIN_BASE   = 90
JUDICIAR_SPIN_PER_LV = 5

# ---------- Mini-boss ----------
MINIBOSS_HP        = 1000
MINIBOSS_DMG       = 50
MINIBOSS_EXP       = 300
MINIBOSS_NAME      = "GREATSWORD SKELETON"
MINIBOSS_IMG_PATH  = 'images/enemies/Greatsword Skeleton'   # ชี้ไปโฟลเดอร์รูป
MINIBOSS_SPECIAL_MULT   = 2      # พลังโจมตีพิเศษแรงกว่าปกติกี่เท่า
MINIBOSS_SPECIAL_CD_MS  = 2000   # 2 วินาที
MINIBOSS_TRIGGER_LEVEL  = 10     # เลเวลที่เรียกมินิบอส

GAME_TIME_LIMIT = 600        # 600 วินาที = 10 นาที

# ---------- Mini-boss #2 ----------
WEREWOLF_HP        = 2000
WEREWOLF_DMG       = 70
WEREWOLF_EXP       = 450
WEREWOLF_NAME      = "WEREWOLF"
WEREWOLF_IMG_PATH  = "images/enemies/Werewolf"
WEREWOLF_TRIGGER_LV = 20
WEREWOLF_SPECIAL_CD = 5000    # 5 วิ

# ---------- Final boss ----------
ELITE_HP           = 3500
ELITE_DMG          = 90
ELITE_EXP          = 1000
ELITE_NAME         = "ELITE ORC"
ELITE_IMG_PATH     = "images/enemies/EliteOrc"
ELITE_TRIGGER_LV   = 30
ELITE_SPECIAL_CD   = 6000     # 6 วิ