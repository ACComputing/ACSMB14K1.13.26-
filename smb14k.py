import pygame
import sys
import random

# ---------- Configuration ----------
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60

# Physics
GRAVITY = 0.5
JUMP_POWER = -14
PLAYER_SPEED = 6
FRICTION = 0.85

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (107, 140, 255)

# Mario Palette
MARIO_RED = (232, 32, 32)
MARIO_BLUE = (32, 56, 236)
MARIO_SKIN = (228, 188, 136)
MARIO_BROWN = (128, 64, 0)

# Environment Palette
GROUND_BROWN = (146, 64, 0)
BRICK_RED = (185, 78, 16)
PIPE_GREEN = (0, 180, 0)
PIPE_DARK = (0, 130, 0)
BLOCK_GOLD = (248, 184, 0)

# Enemy Palette
GOOMBA_BROWN = (180, 90, 30)

# ---------- Classes ----------

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = 0 # Lock Y axis
        
        # Limit scrolling to map bounds
        x = min(0, x) # Left side
        x = max(-(self.width - SCREEN_WIDTH), x) # Right side
        self.camera = pygame.Rect(x, y, self.width, self.height)

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.facing = 1

    def apply_gravity(self):
        self.vy += GRAVITY
        if self.vy > 12: self.vy = 12

    def move_and_collide(self, platforms):
        self.rect.x += int(self.vx)
        self.collide(platforms, 'x')
        
        self.rect.y += int(self.vy)
        self.on_ground = False
        self.collide(platforms, 'y')

    def collide(self, platforms, axis):
        hits = [p for p in platforms if self.rect.colliderect(p)]
        for p in hits:
            if axis == 'x':
                if self.vx > 0: self.rect.right = p.left
                elif self.vx < 0: self.rect.left = p.right
                self.vx = 0
            if axis == 'y':
                if self.vy > 0: 
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0: 
                    self.rect.top = p.bottom
                    self.vy = 0

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 64) # Super Mario Size
        self.hp = 1
        self.score = 0
        self.walk_frame = 0
        self.dead = False
        self.win = False

    def update(self, platforms, enemies, input_active=True):
        if self.dead: return

        keys = pygame.key.get_pressed()
        
        # Movement
        if input_active:
            if keys[pygame.K_LEFT]:
                self.vx -= 0.5
                self.facing = -1
                self.walk_frame += 0.25
            elif keys[pygame.K_RIGHT]:
                self.vx += 0.5
                self.facing = 1
                self.walk_frame += 0.25
            else:
                self.vx *= FRICTION
                self.walk_frame = 0

            # Jump
            if keys[pygame.K_SPACE] and self.on_ground:
                self.vy = JUMP_POWER
                self.on_ground = False
        else:
            # Auto-walk logic for cutscenes (optional) or just friction stop
            self.vx *= FRICTION
            self.walk_frame = 0

        # Max Speed Cap
        if self.vx > PLAYER_SPEED: self.vx = PLAYER_SPEED
        if self.vx < -PLAYER_SPEED: self.vx = -PLAYER_SPEED
        if abs(self.vx) < 0.1: self.vx = 0

        self.apply_gravity()
        self.move_and_collide(platforms)

        # Pit Death
        if self.rect.y > SCREEN_HEIGHT:
            self.dead = True

        # Enemy Interaction
        if not self.win: # Invincible if won
            player_hitbox = self.rect
            for enemy in enemies:
                if enemy.alive and player_hitbox.colliderect(enemy.rect):
                    # Stomp logic: Moving down and player bottom is above enemy center
                    if self.vy > 0 and self.rect.bottom < enemy.rect.centery + 10:
                        enemy.die()
                        self.vy = -6 # Bounce
                        self.score += 100
                    else:
                        self.dead = True

    def draw(self, surface, camera):
        if self.dead: return 
        
        rect = camera.apply(self)
        x, y = rect.x, rect.y
        
        # Simple Pixel Art Representation
        color = MARIO_RED
        overalls = MARIO_BLUE
        
        # Legs
        leg_offset = 0
        if int(self.walk_frame) % 2 == 1 and abs(self.vx) > 1:
            leg_offset = 4 # Simple animation
            
        pygame.draw.rect(surface, overalls, (x + 8 - leg_offset, y + 40, 6, 24)) # Left Leg
        pygame.draw.rect(surface, overalls, (x + 18 + leg_offset, y + 40, 6, 24)) # Right Leg
        
        # Torso
        pygame.draw.rect(surface, overalls, (x + 6, y + 24, 20, 16))
        
        # Arms/Shirt
        pygame.draw.rect(surface, color, (x, y + 24, 6, 16)) # Left Arm
        pygame.draw.rect(surface, color, (x + 26, y + 24, 6, 16)) # Right Arm
        
        # Head
        pygame.draw.rect(surface, MARIO_SKIN, (x + 6, y, 20, 20))
        
        # Hat
        pygame.draw.rect(surface, MARIO_RED, (x + 4, y, 24, 6))
        pygame.draw.rect(surface, MARIO_RED, (x + 4, y-4, 16, 4))
        
        # Eye (Directional)
        eye_x = x + 20 if self.facing == 1 else x + 8
        pygame.draw.rect(surface, BLACK, (eye_x, y + 6, 4, 4))

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32)
        self.vx = -2
        self.alive = True
    
    def update(self, platforms):
        if not self.alive: return
        
        self.apply_gravity()
        
        # Look ahead for walls or edges
        self.rect.x += int(self.vx)
        hits = [p for p in platforms if self.rect.colliderect(p)]
        if hits:
            self.vx *= -1
            self.rect.x += int(self.vx) # Bounce back
        
        self.rect.y += int(self.vy)
        self.on_ground = False
        self.collide(platforms, 'y')

        if self.rect.y > SCREEN_HEIGHT:
            self.alive = False

    def die(self):
        self.alive = False

    def draw(self, surface, camera):
        if not self.alive: return
        r = camera.apply(self)
        pygame.draw.rect(surface, GOOMBA_BROWN, r)
        # Eyes
        pygame.draw.rect(surface, WHITE, (r.x + 4, r.y + 4, 8, 8))
        pygame.draw.rect(surface, WHITE, (r.x + 20, r.y + 4, 8, 8))
        pygame.draw.rect(surface, BLACK, (r.x + 6, r.y + 6, 4, 4))
        pygame.draw.rect(surface, BLACK, (r.x + 22, r.y + 6, 4, 4))
        # Feet animation
        t = pygame.time.get_ticks()
        if (t // 200) % 2 == 0:
            pygame.draw.rect(surface, BLACK, (r.x, r.bottom - 4, 10, 4))
            pygame.draw.rect(surface, BLACK, (r.x + 22, r.bottom - 4, 10, 4))

# ---------- Level Generation ----------

def create_level():
    platforms = []
    enemies = []
    
    # Scale: 1 Block = 32px
    BLOCK = 32
    FLOOR_Y = SCREEN_HEIGHT - 64 # Floor level
    
    # 1. The Ground
    segments = [
        (0, 69), (71, 86), (89, 153), (155, 200)
    ]
    
    for start, end in segments:
        w = (end - start) * BLOCK
        h = 64 # Height of ground
        rect = pygame.Rect(start * BLOCK, FLOOR_Y, w, h)
        platforms.append(rect)

    # 2. Pipes
    pipe_x_coords = [28, 38, 46, 57]
    pipe_heights =  [2,  3,  4,  4]
    
    for i, x in enumerate(pipe_x_coords):
        h_blocks = pipe_heights[i]
        px = x * BLOCK
        py = FLOOR_Y - (h_blocks * BLOCK)
        w = 2 * BLOCK
        h = h_blocks * BLOCK
        platforms.append(pygame.Rect(px, py, w, h))
        if i % 2 == 0:
            enemies.append(Enemy(px - 100, FLOOR_Y - 32))

    # 3. Bricks and Question Blocks
    block_patterns = [
        (16, 4), (20, 4), (21, 4), (22, 4), (23, 4), (24, 4),
        (77, 4), (78, 4), (79, 4),
        (94, 8), (100, 4), (118, 4), (129, 8), (130, 8)
    ]
    
    for bx, by in block_patterns:
        rect = pygame.Rect(bx * BLOCK, FLOOR_Y - (by * BLOCK), BLOCK, BLOCK)
        platforms.append(rect)
        if random.random() > 0.8:
             enemies.append(Enemy(bx * BLOCK, FLOOR_Y - (by * BLOCK) - 40))

    # 4. Staircase
    stair_start = 134
    for i in range(4):
        for h in range(i + 1):
            rect = pygame.Rect((stair_start + i) * BLOCK, FLOOR_Y - (h+1)*BLOCK, BLOCK, BLOCK)
            platforms.append(rect)
            
    stair_down = 140
    for i in range(4):
        for h in range(4 - i):
            rect = pygame.Rect((stair_down + i) * BLOCK, FLOOR_Y - (h+1)*BLOCK, BLOCK, BLOCK)
            platforms.append(rect)
            
    # 5. Flagpole
    flag_x = 198 * BLOCK
    # Base block
    platforms.append(pygame.Rect(flag_x, FLOOR_Y - 32, 32, 32))
    
    # The actual pole for collision trigger (invisible physics sensor)
    # 9 blocks high, thin
    flag_rect = pygame.Rect(flag_x + 12, FLOOR_Y - 9 * BLOCK, 8, 9 * BLOCK)
    
    return platforms, enemies, 200 * BLOCK, flag_rect

# ---------- Main Game Loop ----------

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Super Mario Python 1-1")
    clock = pygame.time.Clock()
    
    # Fonts
    font_main = pygame.font.Font(None, 40)
    font_title = pygame.font.Font(None, 64)
    font_small = pygame.font.Font(None, 24)

    # Game Constants
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GAMEOVER = 2
    STATE_WIN = 3

    game_state = STATE_MENU

    # Init Level placeholders
    platforms = []
    enemies = []
    level_width = 0
    flag_rect = None
    player = None
    camera = None

    running = True
    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state == STATE_MENU:
                    if event.key == pygame.K_RETURN:
                        # Start Game
                        platforms, enemies, level_width, flag_rect = create_level()
                        player = Player(100, 100)
                        camera = Camera(level_width, SCREEN_HEIGHT)
                        game_state = STATE_PLAYING
                
                elif game_state == STATE_GAMEOVER or game_state == STATE_WIN:
                    if event.key == pygame.K_RETURN:
                        game_state = STATE_MENU

        # State Logic
        if game_state == STATE_MENU:
            screen.fill(SKY_BLUE)
            
            # Simple Checkerboard floor for menu
            for x in range(0, SCREEN_WIDTH, 32):
                pygame.draw.rect(screen, GROUND_BROWN, (x, SCREEN_HEIGHT - 64, 32, 64))
                pygame.draw.rect(screen, BLACK, (x, SCREEN_HEIGHT - 64, 32, 64), 2)

            title_surf = font_title.render("SUPER MARIO PYTHON", True, WHITE)
            shadow_surf = font_title.render("SUPER MARIO PYTHON", True, BLACK)
            screen.blit(shadow_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2 + 4, 154))
            screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 150))
            
            start_surf = font_main.render("PRESS ENTER TO START", True, WHITE)
            screen.blit(start_surf, (SCREEN_WIDTH//2 - start_surf.get_width()//2, 300))
            
            cred_surf = font_small.render("2D BROS STYLE - 60 FPS", True, MARIO_RED)
            screen.blit(cred_surf, (SCREEN_WIDTH//2 - cred_surf.get_width()//2, 350))

        elif game_state == STATE_PLAYING:
            player.update(platforms, enemies)
            camera.update(player)
            
            # Check Win
            if player.rect.colliderect(flag_rect):
                game_state = STATE_WIN
                player.win = True
                player.vx = 0 # Stop movement

            # Check Death
            if player.dead:
                game_state = STATE_GAMEOVER

            # Update enemies
            cam_x_start = -camera.camera.x - 100
            cam_x_end = -camera.camera.x + SCREEN_WIDTH + 100
            for e in enemies:
                if cam_x_start < e.rect.x < cam_x_end:
                    e.update(platforms)

            # --- DRAWING ---
            screen.fill(SKY_BLUE)

            # Draw Level
            for p in platforms:
                rect = camera.apply_rect(p)
                color = GROUND_BROWN
                if p.width == 64 and p.height >= 64: color = PIPE_GREEN 
                elif p.width == 32 and p.height == 32 and p.y < SCREEN_HEIGHT - 100: color = BRICK_RED 
                
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 2) 

                if color == PIPE_GREEN:
                    pygame.draw.rect(screen, PIPE_DARK, (rect.x, rect.y, rect.width, 30))
                    pygame.draw.rect(screen, BLACK, (rect.x, rect.y, rect.width, 30), 2)

            # Draw Flagpole Visuals
            pole_visual = camera.apply_rect(flag_rect)
            pygame.draw.rect(screen, (200, 200, 200), pole_visual) # Gray Pole
            # Ball on top
            pygame.draw.circle(screen, BLOCK_GOLD, (pole_visual.centerx, pole_visual.top), 8)
            # Flag (Triangle)
            flag_tri = [
                (pole_visual.left, pole_visual.top + 20),
                (pole_visual.left - 40, pole_visual.top + 40),
                (pole_visual.left, pole_visual.top + 60)
            ]
            pygame.draw.polygon(screen, MARIO_RED, flag_tri)

            # Draw Entities
            for e in enemies:
                e.draw(screen, camera)
            player.draw(screen, camera)
            
            # HUD
            text_score = font_main.render(f"SCORE: {player.score}", True, WHITE)
            screen.blit(text_score, (20, 20))

        elif game_state == STATE_GAMEOVER:
            screen.fill(BLACK)
            msg = font_title.render("GAME OVER", True, MARIO_RED)
            sub = font_main.render("Press ENTER to Menu", True, WHITE)
            screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, SCREEN_HEIGHT//2 + 20))

        elif game_state == STATE_WIN:
            # Keep drawing level in background, but frozen
            screen.fill(SKY_BLUE)
            for p in platforms:
                pygame.draw.rect(screen, GROUND_BROWN, camera.apply_rect(p))
            
            # Draw Pole
            pole_visual = camera.apply_rect(flag_rect)
            pygame.draw.rect(screen, (200, 200, 200), pole_visual)
            pygame.draw.circle(screen, BLOCK_GOLD, (pole_visual.centerx, pole_visual.top), 8)
            
            # Draw Player at flag
            player.draw(screen, camera)

            # Overlay
            msg = font_title.render("COURSE CLEAR!", True, WHITE)
            shadow = font_title.render("COURSE CLEAR!", True, BLACK)
            
            center_x = SCREEN_WIDTH//2 - msg.get_width()//2
            center_y = SCREEN_HEIGHT//3
            
            screen.blit(shadow, (center_x + 4, center_y + 4))
            screen.blit(msg, (center_x, center_y))
            
            score_txt = font_main.render(f"Final Score: {player.score}", True, WHITE)
            screen.blit(score_txt, (SCREEN_WIDTH//2 - score_txt.get_width()//2, center_y + 80))
            
            sub = font_small.render("Press ENTER to Return", True, WHITE)
            screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, center_y + 130))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
