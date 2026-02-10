import ctypes
import pygame
import sys
import random
import numpy as np

# Initialize pygame
pygame.init()

# Window setup
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Little Dude")
little_dude_image = pygame.image.load("Data/Sprites/little_dude.png").convert_alpha()
pygame.display.set_icon(little_dude_image)

# Clock for controlling frame rate
clock = pygame.time.Clock()

### Utility Functions
def curved_path(p0, p1, control, steps=50):
    path = [] 
    for t in np.linspace(0, 1, steps): 
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * control[0] + t**2 * p1[0] 
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * control[1] + t**2 * p1[1] 
        path.append([x, y]) 
    return np.array(path)

# Game objects
class player:
    def __init__(self):
        self.size = 50
        self.color = (0, 0, 0)
        self.x = WIDTH // 2
        self.y = HEIGHT - self.size
        self.speed = 5
        self.jumpDuration = 0
        self.jump = False
        self.visible = False
        self.moving = False
        self.stayDuration = 30
        self.target_platform = None
        self.path = None
        self.path_index = 0
class platform:
    def __init__(self, x, y, width=100, height=20):
        self.width = width
        self.height = height
        self.color = (100, 50, 0)
        self.x = x
        self.y = y
class floor:
    def __init__(self):
        self.platforms = []

### Initial Game Variables
fire_guy = player()
player1 = player()
player1.visible = True
fire_guy_image = pygame.image.load("Data/Sprites/fire_guy.png").convert_alpha()
num_platforms = 6
floors = []
for floor_idx in range(10):
    new_floor = floor()
    # Create 4-6 platforms per floor with random spacing
    
    last_x = random.randint(0, WIDTH - 100)
    for plat_idx in range(num_platforms):
        # Random x position (ensure platform stays on screen)
        deviation = 150
        x = 0
        leftOrRight = -1
        left_deviation = last_x - deviation
        right_deviation = last_x + 100 + deviation

        if left_deviation >= 0 and right_deviation <= WIDTH - 100:
            leftOrRight = random.randint(0,1)
        elif left_deviation >= 0:
            leftOrRight = 0
        else:
            leftOrRight = 1

        if leftOrRight == 0:
            lower_bound = max(0, last_x - deviation)
            upper_bound = last_x - 100
            x = random.randint(lower_bound, upper_bound)
        elif leftOrRight == 1:
            lower_bound = last_x + 100
            upper_bound = min(WIDTH - 100, last_x + 100 + deviation) 
            x = random.randint(lower_bound, upper_bound)

        # Space platforms vertically
        y = HEIGHT - 20 - ((plat_idx + 1)  * 60)
        new_platform = platform(x, y)
        new_floor.platforms.append(new_platform)
        last_x = x
    floors.append(new_floor)
floor_Index = 0
player_height_limit = player1.y
direction = "right"

### Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Key handling
    lastLoc = player1.x
    keys = pygame.key.get_pressed()
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player1.x > 0:
        player1.x -= player1.speed
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player1.x < WIDTH - player1.size:
        player1.x += player1.speed
    if (keys[pygame.K_UP] or keys[pygame.K_w]) and player1.jumpDuration == 0 and player1.y >= player_height_limit:
        player1.jumpDuration = 20
    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and player1.y < HEIGHT - player1.size:
        player1.y += player1.speed

    # Jumping
    if player1.jumpDuration > 0:
        player1.y -= player1.speed
        player1.jumpDuration -= 1

    # New floor transition
    if player1.y < 0:
        if floor_Index < len(floors) - 1:
            floor_Index += 1
        player1.y = HEIGHT - player1.size
        if floor_Index > 0:
            platformIndex = random.randint(0, num_platforms - 1)
            platform_ = floors[floor_Index].platforms[platformIndex]
            fire_guy.x = platform_.x + platform_.width // 2 - fire_guy.size // 2
            fire_guy.y = platform_.y - fire_guy.size
            fire_guy.visible = True

    # Check for landing on platforms
    if player1.jumpDuration == 0:
        for platform_ in floors[floor_Index].platforms:
            if (
                ((player1.x + player1.size) >= platform_.x) and 
                (player1.x <= (platform_.x + platform_.width)) and 
                ((player1.y + player1.size) <= platform_.y) and 
                (player1.y >= (platform_.y - 80))
                ):
                player_height_limit = platform_.y - player1.size
                break
            else:
                player_height_limit = HEIGHT - player1.size

    # Gravity
    if player1.y < player_height_limit and player1.jumpDuration == 0:
        if player_height_limit - player1.y < 2:
            player1.y += 1
        else:
            player1.y += 2

    # Fire guy changing platforms
    if fire_guy.visible and fire_guy.moving is False and fire_guy.stayDuration <= 0:
        fire_guy.moving = True
        fire_guy.target_platform = random.choice(floors[floor_Index].platforms)
        target = fire_guy.target_platform
        p0 = (fire_guy.x, fire_guy.y)
        p1 = (target.x + target.width // 2 - fire_guy.size // 2, target.y - fire_guy.size)
        fire_guy.path = curved_path(p0, p1, [320, 0], steps=50)
        fire_guy.path_index = 0
    elif fire_guy.visible and fire_guy.moving is False:
        fire_guy.stayDuration -= 1
    if fire_guy.moving:
        if fire_guy.path_index < len(fire_guy.path):
            fire_guy.x, fire_guy.y = fire_guy.path[fire_guy.path_index]

        if fire_guy.x == fire_guy.path[-1][0] and fire_guy.y == fire_guy.path[-1][1]:
              fire_guy.moving = False
              fire_guy.stayDuration = 20
        
        fire_guy.path_index += 1

    # Direction tracking
    if player1.x > lastLoc and direction != "right":
        direction = "right"
        little_dude_image = pygame.transform.flip(little_dude_image, True, False)
    elif player1.x < lastLoc and direction != "left":
        direction = "left"
        little_dude_image = pygame.transform.flip(little_dude_image, True, False)

### Draw everything on the screen
    # Fill screen
    screen.fill((190, 190, 255))

    # Draw player
    screen.blit(little_dude_image, (player1.x, player1.y))
    
    # Draw platforms``
    for platform_ in floors[floor_Index].platforms:
        pygame.draw.rect(screen, platform_.color, 
                         (platform_.x, platform_.y, platform_.width, platform_.height))
        
    # Draw fire guy
    if fire_guy.visible:
        screen.blit(fire_guy_image, (fire_guy.x, fire_guy.y))

    # Update display
    pygame.display.flip()

    # Cap FPS
    clock.tick(60)
