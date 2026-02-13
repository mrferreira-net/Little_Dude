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
# Generates a curved path using a quadratic Bezier curve
def curved_path(p0, p1, control, steps=50):
    path = [] 
    for t in np.linspace(0, 1, steps): 
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * control[0] + t**2 * p1[0] 
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * control[1] + t**2 * p1[1] 
        path.append([x, y]) 
    return np.array(path)

# Check for collision between two rectangles
def is_colliding(rect1, rect2):
    return (
        rect1.x < rect2.x + rect2.width and
        rect1.x + rect1.width > rect2.x and
        rect1.y < rect2.y + rect2.height and
        rect1.y + rect1.height > rect2.y
    )

# Game objects
class player:
    def __init__(self):
        self.width = 50
        self.height = 50
        self.size = 50
        self.color = (0, 0, 0)
        self.x = (WIDTH - self.size) // 2
        self.y = HEIGHT - self.size - 10
        self.speed = 5
        self.jumpDuration = 0
        self.jump = False
        self.visible = False
        self.moving = False
        self.stayDuration = 30
        self.path = None
        self.path_index = 0
class platform:
    def __init__(self, x, y):
        self.width = 100
        self.height = 20
        self.color = (100, 50, 0)
        self.x = x
        self.y = y
        self.direction = "right"
class floor:
    def __init__(self):
        self.platforms = []

### Initial Game Variables
fire_guy = player()
fire_guy.x, fire_guy.y, fire_guy.speed = -100, -100, 0.7
fire_guy.width, fire_guy.height, fire_guy.size = 25, 25, 25
numOfPoints = int(100*(1/fire_guy.speed))
player1 = player()
player1.visible = True
fire_guy_image = pygame.image.load("Data/Sprites/fire_guy_s.png").convert_alpha()
num_platforms = 6
floors = []
for floor_idx in range(10):
    new_floor = floor()
    new_floor.platforms.append(platform(0, 0))
    new_floor.platforms[0].color = (158, 153, 146)
    new_floor.platforms[0].width = 300
    new_floor.platforms[0].x = (WIDTH - 300) // 2 
    new_floor.platforms[0].y = HEIGHT - 10

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
        y = HEIGHT - 40 - ((plat_idx + 1)  * 60)
        new_platform = platform(x, y)
        new_floor.platforms.append(new_platform)
        last_x = x
    floors.append(new_floor)
floor_Index = 0
player_height_limit = player1.y
direction = "right"
shifting_platforms = [0]

### Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Key handling for key down events
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if player1.jumpDuration == 0 and player1.y >= player_height_limit:
                    player1.jumpDuration = 18
                
    # Key handling for hold down keys
    lastLoc = player1.x
    keys = pygame.key.get_pressed()
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player1.x > 0:
        player1.x -= player1.speed
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player1.x < WIDTH - player1.size:
        player1.x += player1.speed
    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and player1.y < HEIGHT - player1.size:
        player1.y += player1.speed

    # Jumping
    if player1.jumpDuration > 0:
        player1.y -= player1.speed
        player1.jumpDuration -= 1

    # New floor transition
    if player1.y < 0:
        shifting_platforms = [0]
        fire_guy.path = None
        fire_guy.path_index = 0
        fire_guy.moving = False

        # Changes floor index and resets player vertical position
        if floor_Index < len(floors) - 1:
            floor_Index += 1
        player1.y = HEIGHT - player1.size - 10

        # Chooses where fire guy spawns
        if floor_Index > 0:
            platformIndex = random.randint(1, num_platforms - 1)
            platform_ = floors[floor_Index].platforms[platformIndex]
            fire_guy.x = platform_.x + platform_.width // 2 - fire_guy.size // 2
            fire_guy.y = platform_.y - fire_guy.size
            fire_guy.visible = True

        # Chooses which platforms will shift
        for i in range(floor_Index - 1):
            selected_platform_index = random.randint(1, num_platforms - 1)
            while selected_platform_index in shifting_platforms:
                selected_platform_index = random.randint(1, num_platforms - 1)
            shifting_platforms.append(selected_platform_index)

    # Fire guy changing platforms
    if fire_guy.visible and fire_guy.moving is False and fire_guy.stayDuration <= 0:
        fire_guy.moving = True
        i = random.randint(1, num_platforms - 1)
        while i in shifting_platforms:
            i = random.randint(1, num_platforms - 1)
        target = floors[floor_Index].platforms[i]
        p0 = (fire_guy.x, fire_guy.y)
        p1 = (target.x + target.width // 2 - fire_guy.size // 2, target.y - fire_guy.size)
        fire_guy.path = curved_path(p0, p1, [100, 0], steps=numOfPoints)
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

    # Fire guy collision with player
    if fire_guy.visible:
        if is_colliding(player1, fire_guy):
            fire_guy.visible = False
            fire_guy.x, fire_guy.y = -100, -100
            floor_Index = 0
            player1.x, player1.y = (WIDTH - player1.size) // 2, HEIGHT - player1.size
            shifting_platforms = [0]

    # Lava
    if player1.y >= HEIGHT - player1.size:
        floor_Index = 0
        player1.x, player1.y = (WIDTH - player1.size) // 2, HEIGHT - player1.size
        shifting_platforms = [0]

    # Shift platforms at higher floors
    for i, platform_ in enumerate(floors[floor_Index].platforms):
        if i in shifting_platforms:
            if platform_.direction == "right":
                platform_.x += 1
                if platform_.x + platform_.width >= WIDTH:
                    platform_.direction = "left"
            else:
                platform_.x -= 1
                if platform_.x <= 0:
                    platform_.direction = "right"

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
    
    pygame.draw.rect(screen, (255, 0, 0), (200, 150, 100, 50), 0)

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
