# SUPER MARIO BROS – FULL WORLD 1-1 LOCK BUILD
# Single File – Goombas + Flagpole + Physics + Restart

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

WHITE = (255,255,255)
BLACK = (0,0,0)
SKY = (107,140,255)
GROUND = (146,64,0)
PIPE = (0,200,0)
GOOMBA = (180,90,30)
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
    def __init__(self,x,y,w,h,color):
        self.rect = pygame.Rect(x,y,w,h)
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
            pygame.draw.rect(screen,GOOMBA,camera.apply(self.rect))

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
# LEVEL BUILD (FULL 1-1 STYLE)
# -------------------------------------------------

def build_level():
    width = 210
    platforms = []
    goombas = []

    for x in range(width):
        platforms.append(Block(x*TILE,17*TILE,TILE,TILE,GROUND))
        platforms.append(Block(x*TILE,18*TILE,TILE,TILE,GROUND))

    # Pipes
    for y in range(2):
        platforms.append(Block(28*TILE,(16-y)*TILE,TILE,TILE,PIPE))
        platforms.append(Block(29*TILE,(16-y)*TILE,TILE,TILE,PIPE))

    # Goombas
    for x in [22,40,80,114,174]:
        goombas.append(Goomba(x*TILE,16*TILE))

    # Flag
    flag = pygame.Rect(198*TILE,7*TILE,8,10*TILE)

    return platforms,goombas,flag,width*TILE

# -------------------------------------------------
# GAME LOOP
# -------------------------------------------------

STATE_MENU = 0
STATE_PLAY = 1
STATE_OVER = 2
STATE_WIN = 3

state = STATE_MENU
platforms,goombas,flag,level_width = build_level()
player = Player(100,100)
camera = Camera(level_width)

while True:
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if state == STATE_MENU and event.key == pygame.K_RETURN:
                platforms,goombas,flag,level_width = build_level()
                player = Player(100,100)
                camera = Camera(level_width)
                state = STATE_PLAY
            elif state in (STATE_OVER,STATE_WIN) and event.key == pygame.K_RETURN:
                state = STATE_MENU

    if state == STATE_MENU:
        screen.fill(SKY)
        screen.blit(font_big.render("WORLD 1-1",True,WHITE),(260,200))
        screen.blit(font_small.render("PRESS ENTER",True,WHITE),(270,300))

    elif state == STATE_PLAY:
        player.update(platforms,goombas,flag,keys)
        camera.update(player)

        for g in goombas:
            g.update(platforms)

        if player.dead:
            state = STATE_OVER
        if player.win:
            state = STATE_WIN

        screen.fill(SKY)

        for p in platforms:
            pygame.draw.rect(screen,p.color,camera.apply(p.rect))

        pygame.draw.rect(screen,FLAG_COLOR,camera.apply(flag))
        pygame.draw.circle(screen,GOLD,camera.apply(flag).topleft,8)

        for g in goombas:
            g.draw(camera)

        player.draw(camera)

    elif state == STATE_OVER:
        screen.fill(BLACK)
        screen.blit(font_big.render("GAME OVER",True,(232,32,32)),(230,250))
        screen.blit(font_small.render("PRESS ENTER",True,WHITE),(250,320))

    elif state == STATE_WIN:
        screen.fill(BLACK)
        screen.blit(font_big.render("YOU CLEARED 1-1!",True,GOLD),(120,250))
        screen.blit(font_small.render("PRESS ENTER",True,WHITE),(250,320))

    pygame.display.flip()
    clock.tick(FPS)
