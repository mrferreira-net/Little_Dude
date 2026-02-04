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
little_dude_rect = little_dude_image.get_rect()
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
    b=0

### Initial Game Variables
direction = "right"
floors = []
for floor_idx in range(10):
    new_floor = floor()
    # Create 4-6 platforms per floor with random spacing
    num_platforms = 10
    last_x = random.randint(0, WIDTH - 100)
    for plat_idx in range(num_platforms):
        # Random x position (ensure platform stays on screen)
        deviation = 100
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

        # Space platforms vertically, with some randomness
        y = HEIGHT - 20 - ((plat_idx + 1)  * 60)
        new_platform = platform(x, y)
        new_floor.platforms.append(new_platform)
        last_x = x
    floors.append(new_floor)
floor_Index = 0

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
    if keys[pygame.K_UP] and player.jumpDuration == 0 and player.y >= HEIGHT - player.size:
        player.jumpDuration = 20
    if keys[pygame.K_DOWN] and player.y < HEIGHT - player.size:
        player.y += player.speed

    # Jumping
    if player.jumpDuration > 0 and player.y > 0:
        player.y -= player.speed
        player.jumpDuration -= 1

    # Gravity
    if player.y < HEIGHT - player.size and player.jumpDuration == 0:
        player.y += 2

    # Direction tracking
    if player.x > lastLoc and direction is not "right":
        direction = "right"
        little_dude_image = pygame.transform.flip(little_dude_image, True, False)
    elif player.x < lastLoc and direction is not "left":
        direction = "left"
        little_dude_image = pygame.transform.flip(little_dude_image, True, False)


### Draw everything on the screen
    # Fill screen
    screen.fill((190, 190, 255))

    # Draw sprite
    screen.blit(little_dude_image, (player.x, player.y))

    # Draw platforms
    for platform_ in floors[floor_Index].platforms:
        pygame.draw.rect(screen, platform_.color, 
                         (platform_.x, platform_.y, platform_.width, platform_.height))

    # Update display
    pygame.display.flip()

    # Cap FPS
    clock.tick(60)
