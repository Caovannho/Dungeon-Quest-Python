# -*- coding: utf-8 -*-
import pygame
import random
import os
from collections import deque
import math
import asyncio  # BAT BUOC CHO WEB

# --- THIET LAP THU MUC LAM VIEC ---
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

pygame.init()
pygame.mixer.init()

# Co dinh kich thuoc de dam bao UI tren dien thoai khong bi vo
SIZE = 10
CELL = 64
WIDTH = SIZE * CELL
HEIGHT = SIZE * CELL
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dungeon Quest - Mobile Web Ready")
clock = pygame.time.Clock()

# Tu dong nhan dien thiet bi cam ung
IS_TOUCH_DEVICE = True  # Dat True de luon hien thi bo dieu khien

# ==================== AUDIO MANAGER ====================
current_bgm = ""
settings = {
    "music_volume": 0.6, "sfx_volume": 0.7,
    "key_up": pygame.K_w, "key_down": pygame.K_s,
    "key_left": pygame.K_a, "key_right": pygame.K_d
}

def play_bgm(filename, loop=-1):
    global current_bgm
    if current_bgm != filename:
        try:
            pygame.mixer.music.load(f"sound/{filename}")
            pygame.mixer.music.set_volume(settings["music_volume"])
            pygame.mixer.music.play(loop)
            current_bgm = filename
        except:
            current_bgm = filename

sfx_slash = None
try:
    sfx_slash = pygame.mixer.Sound("sound/vungkiem.mp3")
    sfx_slash.set_volume(settings["sfx_volume"])
except: pass

# ==================== TAO QUAI VAT ANIMATION ====================
def create_monster_frames(monster_type="normal", size=CELL):
    frames = []
    for frame in range(4):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        bob = [0, 3, 0, -2][frame]
        leg_offset = [0, 6, 0, -6][frame]
        
        if monster_type == "normal":
            color = (34, 139, 34)
            pygame.draw.circle(surf, color, (cx, cy + 6 + bob), 23)
            pygame.draw.circle(surf, color, (cx, cy - 6 + bob), 17)
            pygame.draw.line(surf, (20, 80, 20), (cx-10, cy+22), (cx-12, cy+32 + leg_offset), 8)
            pygame.draw.line(surf, (20, 80, 20), (cx+10, cy+22), (cx+13, cy+32 - leg_offset), 8)
            pygame.draw.circle(surf, (255, 60, 60), (cx-7, cy-8 + bob), 6)
            pygame.draw.circle(surf, (255, 60, 60), (cx+7, cy-8 + bob), 6)
        elif monster_type == "fast":
            color = (220, 20, 60)
            pygame.draw.ellipse(surf, color, (cx-19, cy-20 + bob, 38, 42))
            pygame.draw.line(surf, (180,0,0), (cx-12, cy+18), (cx-18, cy+28 + leg_offset*1.5), 6)
            pygame.draw.line(surf, (180,0,0), (cx+12, cy+18), (cx+19, cy+28 - leg_offset*1.5), 6)
        elif monster_type == "tank":
            color = (105, 105, 105)
            pygame.draw.rect(surf, color, (cx-26, cy-20 + bob, 52, 48), border_radius=12)
            pygame.draw.rect(surf, (70,70,70), (cx-20, cy+18, 12, 18 + leg_offset//2), border_radius=4)
            pygame.draw.rect(surf, (70,70,70), (cx+8, cy+18, 12, 18 - leg_offset//2), border_radius=4)
        elif monster_type == "shooter":
            color = (138, 43, 226)
            pygame.draw.polygon(surf, color, [(cx, cy-22 + bob), (cx-22, cy+18), (cx+22, cy+18)])
            pygame.draw.circle(surf, (255, 215, 0), (cx, cy-5 + bob), 10)
            
        pygame.draw.circle(surf, (0,0,0), (cx, cy-5 + bob), 19, width=4)
        pygame.draw.circle(surf, (0,0,0,90), (cx+5, cy+25), 19)
        frames.append(surf)
    return frames

monster_anims = {k: create_monster_frames(k) for k in ["normal", "fast", "tank", "shooter"]}

# ==================== LOAD TAI NGUYEN (WEB SAFE) ====================
def safe_load(path, size, alpha=True):
    paths_to_try = [
        path, path.replace(".jpg", ".png"), path.replace(".png", ".jpg"),
        path.replace("assets/", "assets/PNG/"), path.replace("assets/", "assets/PNG/").replace(".jpg", ".png")
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            try:
                img = pygame.image.load(p)
                img = img.convert_alpha() if alpha else img.convert()
                return pygame.transform.scale(img, size)
            except: pass
            
    surf = pygame.Surface(size, pygame.SRCALPHA)
    if "hiepsi" in path: pygame.draw.rect(surf, (40, 120, 255), (12, 12, size[0]-24, size[1]-24), border_radius=8)
    elif "nen" in path: surf.fill((50, 50, 50))
    elif "wall" in path: surf.fill((100, 100, 100))
    elif "binhthuoc" in path: pygame.draw.circle(surf, (255, 80, 80), (size[0]//2, size[1]//2), size[0]//3)
    elif "khobau" in path: pygame.draw.rect(surf, (200, 160, 50), (15, 15, size[0]-30, size[1]-30))
    else: surf.fill((200, 0, 200))
    return surf

menu_background = safe_load("assets/menu_bg.jpg", (WIDTH, HEIGHT), False)
floor_tile = safe_load("assets/nen.jpg", (CELL, CELL), False)
wall_tile = safe_load("assets/wall.jpg", (CELL, CELL), False)
player_image = safe_load("assets/hiepsi.jpg", (CELL, CELL))
treasure_image = safe_load("assets/khobau.jpg", (CELL, CELL))
potion_image = safe_load("assets/binhthuoc1.jpg", (CELL, CELL))
boss_image = safe_load("assets/boss.jpg", (CELL + 80, CELL + 80))
bullet_image = safe_load("assets/bongdo.jpg", (24, 24))

slash_frames = []
chem_paths = ["assets/chem.png", "assets/chem.jpg", "assets/PNG/chem.png", "assets/PNG/chem.jpg"]
valid_chem = next((p for p in chem_paths if os.path.exists(p)), None)
if valid_chem:
    try:
        slash_sheet = pygame.image.load(valid_chem).convert_alpha()
        sw, sh = slash_sheet.get_size()
        slash_sheet.lock()
        for x in range(sw):
            for y in range(sh):
                r, g, b, a = slash_sheet.get_at((x, y))
                brightness = (r + g + b) // 3
                if brightness < 150: slash_sheet.set_at((x, y), (0, 0, 0, 0))
                else: slash_sheet.set_at((x, y), (r, g, b, min(255, (brightness - 150) * 2)))
        slash_sheet.unlock()
        for i in range(4):
            f = slash_sheet.subsurface(pygame.Rect(i*(sw//4), 0, sw//4, sh))
            slash_frames.append(pygame.transform.scale(f, (int(CELL * 3.0), int(CELL * 3.0))))
    except: pass

web_safe_font = pygame.font.get_default_font()
font_big = pygame.font.Font(web_safe_font, 62)
font_small = pygame.font.Font(web_safe_font, 22)

try:
    font_title = pygame.font.Font("assets/fonts/DungeonQuest.ttf", 62)
    font_subtitle = pygame.font.Font("assets/fonts/DungeonQuest.ttf", 28)
except:
    font_title = pygame.font.Font(web_safe_font, 62)
    font_subtitle = pygame.font.Font(web_safe_font, 28)

def draw_fancy_button(screen, rect, text, base_color, hover=False):
    fill_col = tuple(min(255, c+55) for c in base_color) if hover else base_color
    border_col = (255, 220, 100) if hover else (170, 130, 70)
    shadow_rect = rect.copy(); shadow_rect.x += 5; shadow_rect.y += 7
    pygame.draw.rect(screen, (35, 20, 8), shadow_rect, border_radius=20)
    pygame.draw.rect(screen, fill_col, rect, border_radius=20)
    pygame.draw.rect(screen, border_col, rect, width=8, border_radius=20)
    pygame.draw.rect(screen, (255, 245, 180), rect.inflate(-10, -10), width=3, border_radius=16)
    txt_surf = font_subtitle.render(text, True, (255, 255, 240))
    screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))

# ==================== VIRTUAL CONTROLS ====================
dpad_center = (100, HEIGHT - 100)
dpad_radius = 60
dpad_btns = {
    "UP": pygame.Rect(dpad_center[0]-25, dpad_center[1]-80, 50, 50),
    "DOWN": pygame.Rect(dpad_center[0]-25, dpad_center[1]+30, 50, 50),
    "LEFT": pygame.Rect(dpad_center[0]-80, dpad_center[1]-25, 50, 50),
    "RIGHT": pygame.Rect(dpad_center[0]+30, dpad_center[1]-25, 50, 50)
}

action_btns = {
    "SPACE": {"rect": pygame.Rect(WIDTH - 110, HEIGHT - 110, 80, 80), "color": (200, 50, 50), "text": "ATK"},
    "Q": {"rect": pygame.Rect(WIDTH - 190, HEIGHT - 80, 60, 60), "color": (50, 200, 50), "text": "Q"},
    "E": {"rect": pygame.Rect(WIDTH - 80, HEIGHT - 190, 60, 60), "color": (50, 200, 255), "text": "E"},
    "R": {"rect": pygame.Rect(WIDTH - 160, HEIGHT - 160, 60, 60), "color": (255, 215, 0), "text": "ULT"}
}

def draw_virtual_controls(screen):
    pygame.draw.circle(screen, (50, 50, 50, 150), dpad_center, dpad_radius)
    for btn_rect in dpad_btns.values():
        pygame.draw.rect(screen, (100, 100, 100, 180), btn_rect, border_radius=10)
    for key, data in action_btns.items():
        rect = data["rect"]
        pygame.draw.circle(screen, (30, 30, 30, 150), rect.center, rect.width//2 + 4)
        pygame.draw.circle(screen, data["color"], rect.center, rect.width//2)
        txt = font_small.render(data["text"], True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))

def check_virtual_controls(pos):
    for key, rect in dpad_btns.items():
        if rect.collidepoint(pos): return key
    for key, data in action_btns.items():
        if data["rect"].collidepoint(pos): return key
    return None

# ==================== LOGIC TIM DUONG ====================
def check_path(start, target, grid):
    queue = deque([tuple(start)])
    visited = {tuple(start)}
    while queue:
        curr = queue.popleft()
        if curr == tuple(target): return True
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = curr[0]+dr, curr[1]+dc
            if 0<=nr<SIZE and 0<=nc<SIZE and grid[nr][nc] != 1 and (nr,nc) not in visited:
                visited.add((nr,nc))
                queue.append((nr,nc))
    return False

def bfs_move(start, target, grid, monsters_pos):
    queue = deque([[tuple(start)]])
    visited = {tuple(start)}
    while queue:
        path = queue.popleft()
        curr = path[-1]
        if curr == tuple(target): return path
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = curr[0]+dr, curr[1]+dc
            if 0<=nr<SIZE and 0<=nc<SIZE and grid[nr][nc] not in [1, 2] and (nr,nc) not in monsters_pos and (nr,nc) not in visited:
                visited.add((nr,nc))
                queue.append(path + [(nr,nc)])
    return None

# ==================== GAME STATE & RESET ====================
GAME_STATE = "MENU"
current_level = 1
player_hp = player_max_hp = 300
current_diff = "NORMAL"
player_pos = [0, 0]
monsters = []
boss = None
boss_projectiles = []
kill_count = 0
ULTIMATE_THRESHOLD = 10
shake_amount = dash_cd = spin_cd = 0
attack_dx, attack_dy = 0, -1
is_attacking = False
attack_start = 0
attack_type = "normal"
floating_texts = []
dash_trails = []
grid = []
treasure = None

def reset_game(lv, hp=300, diff="NORMAL"):
    global grid, player_pos, monsters, treasure, boss, current_level, player_hp, player_max_hp, boss_projectiles, current_diff
    global floating_texts, dash_trails, kill_count
    current_level = lv
    current_diff = diff
    player_hp = player_max_hp = hp
    boss_projectiles = []
    floating_texts = []
    dash_trails = []
    
    if lv < 4:
        while True:
            grid = [[1]*SIZE for _ in range(SIZE)]
            stack = [(0, 0)]
            grid[0][0] = 0
            while stack:
                r, c = stack[-1]
                dirs = [(-1,0), (1,0), (0,-1), (0,1)]
                random.shuffle(dirs)
                carved = False
                for dr, dc in dirs:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < SIZE and 0 <= nc < SIZE and grid[nr][nc] == 1:
                        open_n = sum(1 for ddr, ddc in [(-1,0), (1,0), (0,-1), (0,1)] 
                                     if 0 <= nr+ddr < SIZE and 0 <= nc+ddc < SIZE and grid[nr+ddr][nc+ddc] == 0)
                        if open_n == 1 or random.random() < 0.05:
                            grid[nr][nc] = 0; stack.append((nr, nc)); carved = True; break
                if not carved: stack.pop()
            
            grid[9][9] = grid[8][9] = grid[9][8] = 0
            if check_path((0,0), (9,9), grid): break 

        player_pos = [0, 0]
        treasure = (9, 9)
        boss = None
        placed = 0
        while placed < 3:
            rx, ry = random.randint(0, 9), random.randint(0, 9)
            if grid[rx][ry] == 0 and (rx,ry) not in [(0,0), (9,9)]:
                grid[rx][ry] = 2; placed += 1
        monsters = []
        types = ["normal", "fast", "tank", "shooter"]
        for _ in range(5 + lv):
            while True:
                rx, ry = random.randint(0, 9), random.randint(0, 9)
                if grid[rx][ry] == 0 and (rx,ry) not in [(0,0), (9,9)]:
                    m_type = random.choice(types)
                    m_hp = 40 + (30 if m_type == "tank" else -10 if m_type == "fast" else 0)
                    monsters.append({"pos": [rx, ry], "hp": m_hp, "max_hp": m_hp, "type": m_type, "last_atk": 0, "anim_offset": random.randint(0, 3)})
                    break
    else:
        grid = [[0]*SIZE for _ in range(SIZE)]
        for i in range(SIZE): grid[0][i]=grid[9][i]=grid[i][0]=grid[i][9]=1
        player_pos = [1, 1]; treasure = None; monsters = []
        b_hp = 100 if diff == "EASY" else 200 if diff == "NORMAL" else 350
        boss = {"pos": [4, 4], "hp": b_hp, "max_hp": b_hp}

# ==================== MAIN VONG LAP ASYNC ====================
async def main():
    global GAME_STATE, current_level, player_hp, player_max_hp, current_diff
    global player_pos, monsters, boss, boss_projectiles, kill_count
    global shake_amount, dash_cd, spin_cd, attack_dx, attack_dy, is_attacking
    global attack_start, attack_type, floating_texts, dash_trails, grid, treasure, IS_TOUCH_DEVICE

    reset_game(1)
    running = True
    frame_counter = 0

    while running:
        dt = clock.tick(60)
        curr_t = pygame.time.get_ticks()
        frame_counter += 1
        anim_idx = (frame_counter // 10) % 4
        mouse = pygame.mouse.get_pos()
        active_key = None

        if GAME_STATE == "MENU": play_bgm("batdau.mp3")
        elif GAME_STATE == "PLAYING": play_bgm("gamee.mp3")
        elif GAME_STATE == "VICTORY": play_bgm("youwin.mp3", 0)
        elif GAME_STATE == "GAME_OVER": play_bgm("thuagame.mp3", 0)

        if dash_cd > 0: dash_cd -= 1
        if spin_cd > 0: spin_cd -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            # --- TOUCH / MOUSE ---
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                pos = mouse
                if event.type == pygame.FINGERDOWN:
                    pos = (event.x * WIDTH, event.y * HEIGHT)
                    IS_TOUCH_DEVICE = True

                if GAME_STATE == "MENU":
                    if pygame.Rect(195, 255, 250, 68).collidepoint(pos): GAME_STATE = "DIFFICULTY"
                elif GAME_STATE == "DIFFICULTY":
                    if pygame.Rect(170, 200, 300, 72).collidepoint(pos): reset_game(1, 400, "EASY"); kill_count=0; GAME_STATE = "PLAYING"
                    if pygame.Rect(170, 290, 300, 72).collidepoint(pos): reset_game(1, 300, "NORMAL"); kill_count=0; GAME_STATE = "PLAYING"
                    if pygame.Rect(170, 380, 300, 72).collidepoint(pos): reset_game(1, 200, "HARD"); kill_count=0; GAME_STATE = "PLAYING"
                elif GAME_STATE in ["GAME_OVER", "VICTORY"]:
                    if pygame.Rect(180, 400, 280, 55).collidepoint(pos): GAME_STATE = "MENU"
                elif GAME_STATE == "PLAYING" and IS_TOUCH_DEVICE:
                    active_key = check_virtual_controls(pos)

            # --- KEYBOARD ---
            if event.type == pygame.KEYDOWN:
                if event.key == settings["key_up"]: active_key = "UP"
                elif event.key == settings["key_down"]: active_key = "DOWN"
                elif event.key == settings["key_left"]: active_key = "LEFT"
                elif event.key == settings["key_right"]: active_key = "RIGHT"
                elif event.key == pygame.K_SPACE: active_key = "SPACE"
                elif event.key == pygame.K_q: active_key = "Q"
                elif event.key == pygame.K_e: active_key = "E"
                elif event.key == pygame.K_r: active_key = "R"

            if active_key and GAME_STATE == "PLAYING":
                dr = dc = 0
                if active_key == "UP": dr, dc = -1, 0; attack_dx, attack_dy = -1, 0
                elif active_key == "DOWN": dr, dc = 1, 0; attack_dx, attack_dy = 1, 0
                elif active_key == "LEFT": dr, dc = 0, -1; attack_dx, attack_dy = 0, -1
                elif active_key == "RIGHT": dr, dc = 0, 1; attack_dx, attack_dy = 0, 1
                
                if dr or dc:
                    nr, nc = player_pos[0]+dr, player_pos[1]+dc
                    hit_m = any(m["pos"] == [nr, nc] for m in monsters)
                    hit_b = boss and abs(boss["pos"][0] - nr) <= 1 and abs(boss["pos"][1] - nc) <= 1
                    if 0<=nr<SIZE and 0<=nc<SIZE and grid[nr][nc]!=1 and not hit_m and not hit_b:
                        player_pos = [nr, nc]
                        if grid[nr][nc] == 2: 
                            player_hp = min(player_max_hp, player_hp + 25); grid[nr][nc] = 0
                            floating_texts.append({"text": "+25", "color": (0, 255, 0), "pos": [nc*64+32, nr*64], "life": 40})
                        if treasure and (nr, nc) == treasure:
                            if current_level < 4: reset_game(current_level+1, player_hp, current_diff)
                            else: GAME_STATE = "VICTORY"

                if active_key == "SPACE":
                    is_attacking = True; attack_type = "normal"; attack_start = curr_t
                    if sfx_slash: sfx_slash.play()
                    tx, ty = player_pos[0] + attack_dx, player_pos[1] + attack_dy
                    for m in monsters[:]:
                        if m["pos"] == [tx, ty]:
                            dmg = random.randint(20, 30); m["hp"] -= dmg
                            floating_texts.append({"text": f"-{dmg}", "color": (255, 255, 0), "pos": [m["pos"][1]*64+32, m["pos"][0]*64], "life": 30})
                            if m["hp"]<=0: monsters.remove(m); kill_count += 1
                    if boss and abs(boss["pos"][0]-player_pos[0])<=2 and abs(boss["pos"][1]-player_pos[1])<=2:
                        boss["hp"] -= 20
                        floating_texts.append({"text": "-20", "color": (255, 255, 0), "pos": [boss["pos"][1]*64+32, boss["pos"][0]*64], "life": 30})
                        if boss["hp"]<=0: GAME_STATE = "VICTORY"

                if active_key == "Q" and dash_cd <= 0:
                    nr, nc = player_pos[0] + attack_dx*2, player_pos[1] + attack_dy*2
                    hit_m = any(m["pos"] == [nr, nc] for m in monsters)
                    hit_b = boss and abs(boss["pos"][0] - nr) <= 1 and abs(boss["pos"][1] - nc) <= 1
                    if 0<=nr<SIZE and 0<=nc<SIZE and grid[nr][nc]!=1 and not hit_m and not hit_b:
                        dash_trails.append({"pos": list(player_pos), "life": 15})
                        dash_trails.append({"pos": [player_pos[0] + attack_dx, player_pos[1] + attack_dy], "life": 10})
                        player_pos = [nr, nc]; dash_cd = 60; shake_amount = 5

                if active_key == "E" and spin_cd <= 0:
                    is_attacking = True; attack_type = "spin"; attack_start = curr_t
                    spin_cd = 180; shake_amount = 8
                    if sfx_slash: sfx_slash.play()
                    for m in monsters[:]:
                        if abs(m["pos"][0]-player_pos[0])<=2 and abs(m["pos"][1]-player_pos[1])<=2:
                            m["hp"] -= 35
                            floating_texts.append({"text": "-35", "color": (255, 100, 0), "pos": [m["pos"][1]*64+32, m["pos"][0]*64], "life": 30})
                            if m["hp"]<=0: monsters.remove(m); kill_count += 1

                if active_key == "R" and kill_count >= ULTIMATE_THRESHOLD:
                    shake_amount = 25; kill_count = 0
                    for m in monsters[:]: 
                        m["hp"] -= 100
                        floating_texts.append({"text": "-100", "color": (255, 50, 50), "pos": [m["pos"][1]*64+32, m["pos"][0]*64], "life": 40})
                        monsters.remove(m) if m["hp"]<=0 else None
                    if boss: 
                        boss["hp"] -= 150
                        floating_texts.append({"text": "-150", "color": (255, 50, 50), "pos": [boss["pos"][1]*64+32, boss["pos"][0]*64], "life": 40})
                        if boss["hp"] <= 0: GAME_STATE = "VICTORY"

        if GAME_STATE == "PLAYING":
            if frame_counter % 40 == 0 and not boss:
                m_set = {tuple(m["pos"]) for m in monsters}
                for m in monsters:
                    old = tuple(m["pos"]); m_set.discard(old)
                    p = bfs_move(m["pos"], player_pos, grid, m_set)
                    if p and len(p) > 1: 
                        if list(p[1]) != player_pos: m["pos"] = list(p[1])
                    m_set.add(tuple(m["pos"]))
                    if abs(m["pos"][0]-player_pos[0])<=1 and abs(m["pos"][1]-player_pos[1])<=1:
                        if curr_t - m["last_atk"] > 1000:
                            dmg = 15 if m["type"] == "tank" else 10
                            player_hp -= dmg; m["last_atk"] = curr_t
                            floating_texts.append({"text": f"-{dmg}", "color": (255, 0, 0), "pos": [player_pos[1]*64+32, player_pos[0]*64], "life": 20})

            if boss:
                if frame_counter % 80 == 0:
                    bx, by = boss["pos"][1]*64+64, boss["pos"][0]*64+64
                    px, py = player_pos[1]*64+32, player_pos[0]*64+32
                    ang = math.atan2(py-by, px-bx)
                    for a in [ang-0.3, ang, ang+0.3]:
                        boss_projectiles.append({"x":bx, "y":by, "vx":math.cos(a)*6, "vy":math.sin(a)*6})
                for p in boss_projectiles[:]:
                    p["x"]+=p["vx"]; p["y"]+=p["vy"]
                    if math.hypot(p["x"]-(player_pos[1]*64+32), p["y"]-(player_pos[0]*64+32))<25:
                        player_hp-=15; shake_amount=10; boss_projectiles.remove(p)
                        floating_texts.append({"text": "-15", "color": (255, 0, 0), "pos": [player_pos[1]*64+32, player_pos[0]*64], "life": 20})
                    elif not (0<p["x"]<WIDTH and 0<p["y"]<HEIGHT): boss_projectiles.remove(p)
            
            if player_hp <= 0: GAME_STATE = "GAME_OVER"

        ox = random.randint(-shake_amount, shake_amount) if shake_amount > 0 else 0
        oy = random.randint(-shake_amount, shake_amount) if shake_amount > 0 else 0
        if shake_amount > 0: shake_amount -= 1

        screen.fill((15, 15, 25))
        if GAME_STATE == "MENU":
            if menu_background: screen.blit(menu_background, (0, 0))
            t = font_title.render("DUNGEON QUEST", True, (255, 215, 0))
            screen.blit(t, (WIDTH//2 - t.get_width()//2, 100))
            rect = pygame.Rect(195, 255, 250, 68)
            draw_fancy_button(screen, rect, "START GAME", (0, 180, 100), hover=rect.collidepoint(mouse))

        elif GAME_STATE == "DIFFICULTY":
            if menu_background: screen.blit(menu_background, (0, 0))
            title = font_subtitle.render("CHOOSE DIFFICULTY", True, (255, 240, 180))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
            diffs = [("EASY - 400 HP", (0, 200, 100), 200), ("NORMAL - 300 HP", (255, 180, 60), 290), ("HARD - 200 HP", (200, 50, 50), 380)]
            for text, color, y in diffs:
                rect = pygame.Rect(170, y, 300, 72)
                draw_fancy_button(screen, rect, text, color, hover=rect.collidepoint(mouse))

        elif GAME_STATE == "PLAYING":
            for r in range(SIZE):
                for c in range(SIZE): 
                    screen.blit(wall_tile if grid[r][c]==1 else floor_tile, (c*64+ox, r*64+oy))
                    if grid[r][c] == 2: screen.blit(potion_image, (c*64+ox, r*64+oy))
            if treasure: screen.blit(treasure_image, (treasure[1]*64+ox, treasure[0]*64+oy))
            for trail in dash_trails[:]:
                ghost = player_image.copy()
                ghost.set_alpha(int((trail["life"] / 15) * 120))
                screen.blit(ghost, (trail["pos"][1]*64 + ox, trail["pos"][0]*64 + oy))
                trail["life"] -= 1; dash_trails.remove(trail) if trail["life"] <= 0 else None
            for m in monsters:
                m_f = (anim_idx + m["anim_offset"]) % 4
                screen.blit(monster_anims[m["type"]][m_f], (m["pos"][1]*64+ox, m["pos"][0]*64+oy))
                pygame.draw.rect(screen, (255,0,0), (m["pos"][1]*64+10+ox, m["pos"][0]*64+5+oy, 44, 4))
                pygame.draw.rect(screen, (0,255,0), (m["pos"][1]*64+10+ox, m["pos"][0]*64+5+oy, int(44*max(0, m["hp"]/m["max_hp"])), 4))
            if boss:
                screen.blit(boss_image, (boss["pos"][1]*64-40+ox, boss["pos"][0]*64-40+oy))
                pygame.draw.rect(screen, (255,0,0), (220+ox, 40+oy, 200, 10))
                pygame.draw.rect(screen, (0,255,0), (220+ox, 40+oy, (boss["hp"]/boss["max_hp"])*200, 10))
                screen.blit(font_small.render(f"{int(max(0, boss['hp']))}/{boss['max_hp']}", True, (255,255,255)), (430+ox, 35+oy))
            for p in boss_projectiles: screen.blit(bullet_image, (int(p["x"])-12+ox, int(p["y"])-12+oy))
            screen.blit(player_image, (player_pos[1]*64+ox, player_pos[0]*64+oy))
            if is_attacking and curr_t - attack_start < 280:
                idx = int((curr_t - attack_start) / 280 * len(slash_frames))
                if idx < len(slash_frames):
                    cx, cy = player_pos[1]*64 + 32 + ox, player_pos[0]*64 + 32 + oy
                    if attack_type == "normal":
                        angle = 0
                        if attack_dy == 1: angle = 0
                        elif attack_dy == -1: angle = 180
                        elif attack_dx == -1: angle = 90
                        elif attack_dx == 1: angle = -90
                        rot = pygame.transform.rotate(slash_frames[idx], angle)
                        screen.blit(rot, rot.get_rect(center=(cx + attack_dy*70, cy + attack_dx*70)))
                    elif attack_type == "spin":
                        for ang, d_dx, d_dy in [(0, 0, 1), (180, 0, -1), (90, -1, 0), (-90, 1, 0)]:
                            rot = pygame.transform.rotate(slash_frames[idx], ang)
                            screen.blit(rot, rot.get_rect(center=(cx + d_dy*70, cy + d_dx*70)))
            else: is_attacking = False
            for ft in floating_texts[:]:
                t_surf = font_small.render(ft["text"], True, ft["color"])
                screen.blit(t_surf, (ft["pos"][0] + ox - t_surf.get_width()//2, ft["pos"][1] + oy))
                ft["pos"][1] -= 1; ft["life"] -= 1
                if ft["life"] <= 0: floating_texts.remove(ft)
            pygame.draw.rect(screen, (180, 0, 0), (20, 45, 150, 10))
            pygame.draw.rect(screen, (0, 255, 0), (20, 45, int(150*max(0, player_hp/player_max_hp)), 10))
            screen.blit(font_small.render(f"{int(max(0, player_hp))}/{player_max_hp}", True, (255,255,255)), (180, 40))
            screen.blit(font_small.render(f"LV: {current_level} | Diff: {current_diff}", True, (255,255,255)), (20, 15))
            if IS_TOUCH_DEVICE: draw_virtual_controls(screen)

        elif GAME_STATE in ["GAME_OVER", "VICTORY"]:
            screen.fill((90, 15, 15) if GAME_STATE == "GAME_OVER" else (15, 90, 40))
            title = font_title.render("GAME OVER" if GAME_STATE == "GAME_OVER" else "VICTORY!", True, (255,70,70) if GAME_STATE=="GAME_OVER" else (255,240,80))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 140))
            rect = pygame.Rect(180, 400, 280, 55)
            draw_fancy_button(screen, rect, "BACK TO MENU", (80, 80, 120), hover=rect.collidepoint(mouse))

        pygame.display.flip()
        await asyncio.sleep(0)

asyncio.run(main())