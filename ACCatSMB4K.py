import pygame
import sys
import random

pygame.init()

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
TILE = 32
GRAVITY = 0.8
MAX_FALL = 14
JUMP_POWER = -17
WALK_SPEED = 6
FRICTION = 0.85

# Colors
WHITE = (255,255,255)
BLACK = (0,0,0)
SKY = (107,140,255)
GROUND_COLOR = (146,64,0)
BRICK_COLOR = (180,90,30)
QUESTION_COLOR = (248,184,0)
PIPE_COLOR = (0,200,0)
HIDDEN_COLOR = None  # invisible
FLAG_COLOR = (200,200,200)
GOLD = (248,184,0)

screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("SMB Deluxe – World 1-1 LOCK")
clock = pygame.time.Clock()

font_big = pygame.font.Font(None,72)
font_small = pygame.font.Font(None,40)

# -------------------------------------------------
# BASIC OBJECTS
# -------------------------------------------------
class Block:
    def __init__(self, x, y, w, h, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color

class Goomba:
    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,32,32)
        self.vx = -2
        self.vy = 0
        self.alive = True

    def update(self,platforms):
        if not self.alive:
            return
        
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.rect.x += self.vx
        
        for p in platforms:
            if self.rect.colliderect(p.rect):
                self.vx *= -1
                self.rect.x += self.vx * 2
                
        self.rect.y += self.vy
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0

    def draw(self,camera):
        if self.alive:
            pygame.draw.rect(screen, (180,90,30), camera.apply(self.rect))

class Camera:
    def __init__(self,width):
        self.x = 0
        self.width = width

    def apply(self,rect):
        return rect.move(self.x,0)

    def update(self,target):
        self.x = -target.rect.centerx + SCREEN_WIDTH//2
        self.x = min(0,self.x)
        self.x = max(-(self.width-SCREEN_WIDTH),self.x)

# -------------------------------------------------
# PLAYER
# -------------------------------------------------
class Player:
    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,28,56)
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.dead = False
        self.win = False

    def update(self,platforms,goombas,flag,keys):
        if self.dead or self.win:
            return

        if keys[pygame.K_LEFT]:
            self.vx -= 0.5
        elif keys[pygame.K_RIGHT]:
            self.vx += 0.5
        else:
            self.vx *= FRICTION

        self.vx = max(-WALK_SPEED,min(WALK_SPEED,self.vx))
        if abs(self.vx) < 0.1:
            self.vx = 0

        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = JUMP_POWER
            self.on_ground = False

        self.vy = min(self.vy + GRAVITY, MAX_FALL)

        # X collision
        self.rect.x += int(self.vx)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.rect.right = p.rect.left
                elif self.vx < 0:
                    self.rect.left = p.rect.right
                self.vx = 0

        # Y collision
        self.rect.y += int(self.vy)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy = 0

        # Goomba collision
        for g in goombas:
            if g.alive and self.rect.colliderect(g.rect):
                if self.vy > 0 and self.rect.bottom - 10 < g.rect.top + 20:
                    g.alive = False
                    self.vy = -8
                else:
                    self.dead = True

        # Flag
        if self.rect.colliderect(flag):
            self.win = True
        
        if self.rect.y > 1000:
            self.dead = True

    def draw(self,camera):
        r = camera.apply(self.rect)
        pygame.draw.rect(screen,(232,32,32),(r.x,r.y+20,28,16))
        pygame.draw.rect(screen,(32,56,236),(r.x+4,r.y+36,8,20))
        pygame.draw.rect(screen,(32,56,236),(r.x+16,r.y+36,8,20))
        pygame.draw.rect(screen,(228,188,136),(r.x+4,r.y,20,20))

# -------------------------------------------------
# LEVEL BUILD (ACCURATE 1-1)
# -------------------------------------------------
def build_level():
    width_tiles = 220
    platforms = []
    goombas = []

    # Helper to add a pipe
    def add_pipe(left_col, top_row, height, color):
        for row in range(top_row, top_row + height):
            platforms.append(Block(left_col * TILE, row * TILE, TILE, TILE, color))
            platforms.append(Block((left_col + 1) * TILE, row * TILE, TILE, TILE, color))

    # Pit ranges (columns where ground is missing)
    pit_ranges = [(87, 90), (118, 121), (158, 161), (170, 173)]

    # Ground (two rows thick) everywhere except pits
    for x in range(width_tiles):
        in_pit = False
        for start, end in pit_ranges:
            if start <= x <= end:
                in_pit = True
                break
        if not in_pit:
            platforms.append(Block(x * TILE, 17 * TILE, TILE, TILE, GROUND_COLOR))
            platforms.append(Block(x * TILE, 18 * TILE, TILE, TILE, GROUND_COLOR))

    # -------------------------------------------------
    # Pipes
    # -------------------------------------------------
    add_pipe(38, 15, 2, PIPE_COLOR)   # height 2 (rows 15,16)
    add_pipe(57, 14, 3, PIPE_COLOR)   # height 3 (rows 14,15,16)
    add_pipe(73, 13, 4, PIPE_COLOR)   # height 4 (rows 13-16)
    add_pipe(85, 13, 4, PIPE_COLOR)   # height 4
    add_pipe(179, 15, 2, PIPE_COLOR)  # height 2
    add_pipe(187, 16, 1, PIPE_COLOR)  # height 1 (row 16)

    # -------------------------------------------------
    # Question blocks (row 13)
    # -------------------------------------------------
    q_blocks = [16, 94, 121, 123]
    for col in q_blocks:
        platforms.append(Block(col * TILE, 13 * TILE, TILE, TILE, QUESTION_COLOR))

    # -------------------------------------------------
    # Hidden block (row 13)
    # -------------------------------------------------
    platforms.append(Block(91 * TILE, 13 * TILE, TILE, TILE, HIDDEN_COLOR))

    # -------------------------------------------------
    # Bricks at row 13
    # -------------------------------------------------
    brick_row13 = [20, 21, 22, 23, 100, 109, 112, 130, 131, 182, 183, 184, 185]
    for col in brick_row13:
        platforms.append(Block(col * TILE, 13 * TILE, TILE, TILE, BRICK_COLOR))

    # -------------------------------------------------
    # Bricks at row 9
    # -------------------------------------------------
    brick_row9 = [21, 22, 122, 131]
    for col in brick_row9:
        platforms.append(Block(col * TILE, 9 * TILE, TILE, TILE, BRICK_COLOR))
    # Long row from 99 to 114
    for col in range(99, 115):
        platforms.append(Block(col * TILE, 9 * TILE, TILE, TILE, BRICK_COLOR))

    # -------------------------------------------------
    # First pyramid (small) – columns 140-146
    # -------------------------------------------------
    pyramid1 = [
        (140, 17), (141, 16), (142, 15), (143, 14),
        (144, 15), (145, 16), (146, 17)
    ]
    for col, row in pyramid1:
        platforms.append(Block(col * TILE, row * TILE, TILE, TILE, BRICK_COLOR))

    # -------------------------------------------------
    # Second pyramid (large) – columns 150-159
    # -------------------------------------------------
    pyramid2 = [
        (150, 17), (151, 16), (152, 15), (153, 14), (154, 13),
        (155, 13), (156, 14), (157, 15), (158, 16), (159, 17)
    ]
    for col, row in pyramid2:
        platforms.append(Block(col * TILE, row * TILE, TILE, TILE, BRICK_COLOR))

    # -------------------------------------------------
    # Staircase before castle (steps)
    # -------------------------------------------------
    for i in range(8):
        col = 191 + i
        row = 17 - i
        platforms.append(Block(col * TILE, row * TILE, TILE, TILE, BRICK_COLOR))

    # -------------------------------------------------
    # Castle (simple shape)
    # -------------------------------------------------
    # Base
    for col in range(201, 206):
        platforms.append(Block(col * TILE, 17 * TILE, TILE, TILE, GROUND_COLOR))
        platforms.append(Block(col * TILE, 16 * TILE, TILE, TILE, GROUND_COLOR))
    # Left wall
    for row in range(13, 16):
        platforms.append(Block(201 * TILE, row * TILE, TILE, TILE, GROUND_COLOR))
    # Right wall
    for row in range(13, 16):
        platforms.append(Block(205 * TILE, row * TILE, TILE, TILE, GROUND_COLOR))
    # Top
    for col in range(201, 206):
        platforms.append(Block(col * TILE, 12 * TILE, TILE, TILE, GROUND_COLOR))
    # Tower top
    platforms.append(Block(203 * TILE, 11 * TILE, TILE, TILE, GROUND_COLOR))

    # -------------------------------------------------
    # Flag
    # -------------------------------------------------
    flag = pygame.Rect(198 * TILE, 7 * TILE, 8, 10 * TILE)

    # -------------------------------------------------
    # Goombas (positions approximate from original)
    # -------------------------------------------------
    goomba_positions = [21, 50, 52, 65, 67, 80, 82, 100, 102, 104, 128, 135, 137, 148, 150, 182, 184]
    for x in goomba_positions:
        goombas.append(Goomba(x * TILE, 16 * TILE))

    return platforms, goombas, flag, width_tiles * TILE

# -------------------------------------------------
# GAME LOOP
# -------------------------------------------------
STATE_MENU = 0
STATE_PLAY = 1
STATE_OVER = 2
STATE_WIN = 3
state = STATE_MENU

platforms, goombas, flag, level_width = build_level()
player = Player(32, 17 * TILE - 56)  # start at left edge on ground
camera = Camera(level_width)

while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if state == STATE_MENU and event.key == pygame.K_RETURN:
                platforms, goombas, flag, level_width = build_level()
                player = Player(32, 17 * TILE - 56)
                camera = Camera(level_width)
                state = STATE_PLAY
            elif state in (STATE_OVER, STATE_WIN) and event.key == pygame.K_RETURN:
                state = STATE_MENU

    if state == STATE_MENU:
        screen.fill(SKY)
        screen.blit(font_big.render("WORLD 1-1", True, WHITE), (260, 200))
        screen.blit(font_small.render("PRESS ENTER", True, WHITE), (270, 300))

    elif state == STATE_PLAY:
        player.update(platforms, goombas, flag, keys)
        camera.update(player)
        
        for g in goombas:
            g.update(platforms)
            
        if player.dead:
            state = STATE_OVER
        if player.win:
            state = STATE_WIN
            
        screen.fill(SKY)
        # Draw all platforms except hidden ones
        for p in platforms:
            if p.color is not None:
                pygame.draw.rect(screen, p.color, camera.apply(p.rect))
            
        # Draw flag
        pygame.draw.rect(screen, FLAG_COLOR, camera.apply(flag))
        pygame.draw.circle(screen, GOLD, camera.apply(flag).topleft, 8)
        
        for g in goombas:
            g.draw(camera)
            
        player.draw(camera)

    elif state == STATE_OVER:
        screen.fill(BLACK)
        screen.blit(font_big.render("GAME OVER", True, (232,32,32)), (230,250))
        screen.blit(font_small.render("PRESS ENTER", True, WHITE), (250,320))

    elif state == STATE_WIN:
        screen.fill(BLACK)
        screen.blit(font_big.render("YOU CLEARED 1-1!", True, GOLD), (120,250))
        screen.blit(font_small.render("PRESS ENTER", True, WHITE), (250,320))

    pygame.display.flip()
    clock.tick(FPS)
