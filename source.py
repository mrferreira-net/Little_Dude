import ctypes
import pygame
import sys
import random

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
def floorChange(vert_direction):
    b = 0

# Game objects
class player:
    size = 50
    color = (0, 0, 0)
    x = WIDTH // 2
    y = HEIGHT - size
    speed = 5
    jumpDuration = 0
    jump = False
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
class sprite:
    size = 50


### Initial Game Variables
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
player_height_limit = player.y
enemy_sprite_platforms = []
direction = "right"

### Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Key handling
    lastLoc = player.x
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player.x > 0:
        player.x -= player.speed
    if keys[pygame.K_RIGHT] and player.x < WIDTH - player.size:
        player.x += player.speed
    if keys[pygame.K_UP] and player.jumpDuration == 0 and player.y >= player_height_limit:
        player.jumpDuration = 20
    if keys[pygame.K_DOWN] and player.y < HEIGHT - player.size:
        player.y += player.speed

    # Jumping
    if player.jumpDuration > 0:
        player.y -= player.speed
        player.jumpDuration -= 1

    # New floor transition
    if player.y < 0:
        if floor_Index < len(floors) - 1:
            floor_Index += 1
        player.y = HEIGHT - player.size
        if len(enemy_sprite_platforms) < 3:
            enemy_sprite_platforms.append(random.randint(0, num_platforms - 1))

            

    # Check for landing on platforms
    if player.jumpDuration == 0:
        for platform_ in floors[floor_Index].platforms:
            if (
                ((player.x + player.size) >= platform_.x) and 
                (player.x <= (platform_.x + platform_.width)) and 
                ((player.y + player.size) <= platform_.y) and 
                (player.y >= (platform_.y - 80))
                ):
                player_height_limit = platform_.y - player.size
                break
            else:
                player_height_limit = HEIGHT - player.size

    # Gravity
    if player.y < player_height_limit and player.jumpDuration == 0:
        if player_height_limit - player.y < 2:
            player.y += 1
        else:
            player.y += 2

    # Direction tracking
    if player.x > lastLoc and direction != "right":
        direction = "right"
        little_dude_image = pygame.transform.flip(little_dude_image, True, False)
    elif player.x < lastLoc and direction != "left":
        direction = "left"
        little_dude_image = pygame.transform.flip(little_dude_image, True, False)

### Draw everything on the screen
    # Fill screen
    screen.fill((190, 190, 255))

    # Draw sprites
    screen.blit(little_dude_image, (player.x, player.y))
    for platform_ in enemy_sprite_platforms:
        screen.blit(fire_guy_image, (floors[floor_Index].platforms[platform_].x + (floors[floor_Index].platforms[platform_].width - fire_guy_image.get_width()) // 2, floors[floor_Index].platforms[platform_].y - 50))

    # Draw platforms``
    for platform_ in floors[floor_Index].platforms:
        pygame.draw.rect(screen, platform_.color, 
                         (platform_.x, platform_.y, platform_.width, platform_.height))

    # Update display
    pygame.display.flip()

    # Cap FPS
    clock.tick(60)
