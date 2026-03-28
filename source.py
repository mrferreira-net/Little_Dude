import ctypes
import pygame
import sys
import random
import numpy as np

# Initialize pygame
pygame.init()

# Initualize mixer for sounds
pygame.mixer.init()
pygame.mixer.music.load("Data/Sounds/Littledude_music.wav")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

# Window setup
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Little Dude")

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

# Function to destroy a platform when player lands on new platform, making it invisible and uncollidable
def destroy_Platform(platform_):
        global floors, floor_Index, valid_platforms
        for i, platform in enumerate(floors[floor_Index].platforms):
            if platform == platform_ and i != 0:
                try:
                    valid_platforms.remove(i)
                except:
                    pass
        platform_.visible = False
        if little_dude.current_Platform == platform_:
            little_dude.height_limit = HEIGHT - little_dude.size
            little_dude.current_Platform = None

# Reset game state after player dies         
def reset():
    global floor_Index, shifting_platforms, valid_platforms, balls
    global numOfPoints, fire_guy, smoke, little_dude, floors, running

    running = False
    little_dude.image = pygame.image.load("Data/Sprites/dead.png").convert_alpha()
    render_display()
    explosion_sound.play()
    start_time = pygame.time.get_ticks()
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - start_time
    while elapsed_time < 200:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time
    running = True
    little_dude.image = pygame.image.load("Data/Sprites/little_dude.png").convert_alpha()
    little_dude.direction = "right"

    floor_Index = 0
    fire_guy.visible = False
    fire_guy.moving = False
    smoke.visible = False
    bolt.visible = False
    fire_guy.x, fire_guy.y, fire_guy.speed = -100, -100, 0.3
    numOfPoints = int(100*(1/fire_guy.speed))
    little_dude.x, little_dude.y = (WIDTH - little_dude.size) // 2, floors[0].platforms[0].y - little_dude.size
    little_dude.last_Platform = floors[0].platforms[0]
    little_dude.current_Platform = floors[0].platforms[0]
    shifting_platforms = []
    for floor in floors:
        for platform in floor.platforms:
            platform.visible = True
    valid_platforms = [1, 2, 3, 4, 5, 6]
    balls = []

# Function to move fire guy to a new platform
def fire_guy_target_platform():
    global smoke, shifting_platforms, floor_Index, fire_guy, floors, num_platforms, numOfPoints
    if not fire_guy.moving:
        smoke.x = fire_guy.x
        smoke.y = fire_guy.y
        smoke.visible = True
        fire_jump_sound.play()
    fire_guy.moving = True
    if len(valid_platforms) <= 1:
        return
    i = random.choice(valid_platforms)
    while (i in shifting_platforms or floors[floor_Index].platforms[i].visible is False or 
           floors[floor_Index].platforms[i] == fire_guy.current_Platform):
        i = random.choice(valid_platforms)
    target = floors[floor_Index].platforms[i]
    fire_guy.current_Platform = target
    p0 = (fire_guy.x, fire_guy.y)
    p1 = (target.x + target.width // 2 - fire_guy.size // 2, target.y - fire_guy.size)
    fire_guy.path = curved_path(p0, p1, [100, 0], steps=numOfPoints)
    fire_guy.path_index = 0

# Game objects
class sprite:
    def __init__(self):
        self.width = 25
        self.height = 25
        self.size = 25
        self.color = (0, 0, 0)
        self.x = (WIDTH - self.size) // 2
        self.y = HEIGHT - self.size - 10
        self.speed = 5
        self.x_del = 1
        self.y_del = 1
        self.jumpDuration = 0
        self.jump = False
        self.visible = False
        self.moving = False
        self.stayDuration = 30
        self.path = None
        self.path_index = 0
        self.image = None
        self.last_Platform = None
        self.current_Platform = None
        self.height_limit = self.y
        self.direction = "right"
        self.angle = 0
class platform:
    def __init__(self, x, y):
        self.width = 100
        self.height = 20
        self.color = (158, 153, 146)
        self.x = x
        self.y = y
        self.speed = 1
        self.direction = "right"
        self.visible = True
        self.moving = False
class floor:
    def __init__(self):
        self.platforms = []

### Initial Game Variables
def initiate_vars():
    global fire_guy, little_dude, smoke
    global bolt, numOfPoints, num_platforms, floors, floor_Index
    global little_dude, shifting_platforms, valid_platforms
    global balls, jump_sound, explosion_sound, fire_jump_sound
    global powerUp_sound, fire_explosion_sound
    global smoke_sound, running, fire_guy_dead

    running = True

    jump_sound = pygame.mixer.Sound("Data/Sounds/jump.wav")
    jump_sound.set_volume(0.2)
    explosion_sound = pygame.mixer.Sound("Data/Sounds/explosion.wav")
    fire_jump_sound = pygame.mixer.Sound("Data/Sounds/fire_jump.wav")
    powerUp_sound = pygame.mixer.Sound("Data/Sounds/powerUp.wav")
    fire_explosion_sound = pygame.mixer.Sound("Data/Sounds/fire_explosion.wav")
    smoke_sound = pygame.mixer.Sound("Data/Sounds/smoke.wav")

    fire_guy = sprite()
    fire_guy.x, fire_guy.y, fire_guy.speed = -100, -100, 0.3
    fire_guy.image = pygame.image.load("Data/Sprites/fire_guy_s.png").convert_alpha()
    fire_guy_dead = 0

    little_dude = sprite()
    little_dude.visible = True
    little_dude.size, little_dude.width, little_dude.height = 50, 50, 50
    
    little_dude.image = pygame.image.load("Data/Sprites/little_dude.png").convert_alpha()
    
    smoke = sprite()
    smoke.image = pygame.image.load("Data/Sprites/smoke.png").convert_alpha()

    bolt = sprite()
    bolt.width, bolt.height, bolt.size = 10, 15, None
    bolt.image = pygame.image.load("Data/Sprites/bolt.png").convert_alpha()

    balls = []

    numOfPoints = int(100*(1/fire_guy.speed))
    num_platforms = 6
    floors = []
    for floor_idx in range(100):
        new_floor = floor()
        new_floor.platforms.append(platform(0, 0))
        new_floor.platforms[0].width = 300
        new_floor.platforms[0].x = (WIDTH - 300) // 2 
        new_floor.platforms[0].y = HEIGHT - 10

        # Create 4-6 platforms per floor with random spacing
        last_x = random.randint(0, WIDTH - 100)
        for plat_idx in range(num_platforms):
            # Random x position (ensure platform stays on screen)
            deviation = 100
            x = 0
            leftOrRight = -1
            left_deviation = last_x - deviation - 50
            right_deviation = last_x + 100 + deviation + 50

            if left_deviation >= 0 and right_deviation <= WIDTH - 100:
                leftOrRight = random.randint(0,1)
            elif left_deviation >= 0:
                leftOrRight = 0
            elif right_deviation <= WIDTH - 100:
                leftOrRight = 1

            if leftOrRight == 0:
                lower_bound = max(0, left_deviation)
                x = random.randint(lower_bound, last_x - 50 - 100)
            elif leftOrRight == 1:
                upper_bound = min(WIDTH - 100, right_deviation) 
                x = random.randint(last_x + 100 + 50, upper_bound)

            # Space platforms vertically
            y = HEIGHT - 30 - ((plat_idx + 1)  * 60)

            new_platform = platform(x, y)
            new_floor.platforms.append(new_platform)
            last_x = x
        floors.append(new_floor)
    floor_Index = 0
    little_dude.last_Platform = floors[0].platforms[0]
    little_dude.current_Platform = floors[0].platforms[0]
    little_dude.y = floors[0].platforms[0].y - little_dude.size
    little_dude.x, little_dude.y = (WIDTH - little_dude.size) // 2, floors[0].platforms[0].y - little_dude.size
    shifting_platforms = []
    
    valid_platforms = [1, 2, 3, 4, 5, 6]

### Draw everything on the screen
def render_display():
    global fire_guy_dead
    # Fill screen
    screen.blit(pygame.image.load("Data/Sprites/background.png").convert(), (0, 0))

    # Draw player
    screen.blit(little_dude.image, (little_dude.x, little_dude.y))
    
    # Draw floor number
    screen.blit(text, text_rect)

    # Draw lava
    pygame.draw.rect(screen, (240, 105, 22), (0, HEIGHT - 6, WIDTH, 10), 0)

    # Draw platforms
    for platform_ in floors[floor_Index].platforms:
        if platform_.visible:
            pygame.draw.rect(screen, 'black', 
                            (platform_.x - 1, platform_.y - 1, platform_.width + 2, platform_.height + 2))
            pygame.draw.rect(screen, platform_.color, 
                            (platform_.x, platform_.y, platform_.width, platform_.height))
        
    # Draw fire guy
    if fire_guy.visible:
        screen.blit(fire_guy.image, (fire_guy.x, fire_guy.y))

    if fire_guy_dead == 1:
        global fg_death_time
        fg_death_time = pygame.time.get_ticks()
        fire_guy_dead = -1
    elif fire_guy_dead == -1:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - fg_death_time
        if elapsed_time < 200:
            explosion_image = pygame.image.load("Data/Sprites/dead.png").convert_alpha()
            explosion_diff = (50 - fire_guy.size) // 2
            explosion_x = fire_guy.x - explosion_diff
            explosion_y = fire_guy.y - explosion_diff
            screen.blit(explosion_image, (explosion_x, explosion_y))
        else:
            fire_guy_dead = 0

    # Draw smoke
    if smoke.visible:
        screen.blit(smoke.image, (smoke.x, smoke.y))

    # Draw bolt    
    if bolt.visible:
        screen.blit(bolt.image, (bolt.x, bolt.y))

    # Draw ball
    for ball_ in balls:
        ball_.angle += 5
        if ball_.angle >= 360:
            ball_.angle = 0
        rotated_ball = pygame.transform.rotate(ball_.image, ball_.angle)
        screen.blit(rotated_ball, (ball_.x, ball_.y))

    # Update display
    pygame.display.flip()

    # Cap FPS
    clock.tick(60)

### Main game loop
initiate_vars()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Key handling for key down events
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if little_dude.jumpDuration == 0 and little_dude.y >= little_dude.height_limit:
                    little_dude.jumpDuration = 18
                    jump_sound.play()
            # Debugging teleportation
            if event.key == pygame.K_t:
                little_dude.y = -10
    # Key handling for hold down keys
    lastLoc = little_dude.x
    keys = pygame.key.get_pressed()
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and little_dude.x > 0:
        little_dude.x -= little_dude.speed
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and little_dude.x < WIDTH - little_dude.size:
        little_dude.x += little_dude.speed
    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and little_dude.y < HEIGHT - little_dude.size - 10:
        little_dude.y += little_dude.speed

    # Jumping
    if little_dude.jumpDuration > 0:
        little_dude.y -= little_dude.speed
        little_dude.jumpDuration -= 1

    # New floor transition
    if little_dude.y < 0:
        shifting_platforms = [0]
        fire_guy.path = None
        smoke.visible = False
        bolt.visible = False
        fire_guy.path_index = 0
        fire_guy.moving = False
        fire_guy.stayDuration = 30
        valid_platforms = [1, 2, 3, 4, 5, 6]

        # Changes floor index and resets player vertical position
        if floor_Index < len(floors) - 1:
            floor_Index += 1
        little_dude.y = HEIGHT - little_dude.size - 10

        # Centers platform on player
        floor_platform = floors[floor_Index].platforms[0]
        if little_dude.x <= floor_platform.width / 2:
            floors[floor_Index].platforms[0].x = 0
        elif little_dude.x >= WIDTH - floor_platform.width / 2:
            floors[floor_Index].platforms[0].x = WIDTH - floor_platform.width 
        else:
            floors[floor_Index].platforms[0].x = little_dude.x - (floor_platform.width - little_dude.size) // 2

        # Chooses which platforms will shift
        range_ = 0
        if floor_Index < 4:
            range_ = floor_Index - 1
        else:
            range_ = 3
        range_ = random.randint(0, range_)
        for i in range(range_):
            selected_platform_index = random.randint(1, num_platforms)
            while selected_platform_index in shifting_platforms:
                selected_platform_index = random.randint(1, num_platforms)
            shifting_platforms.append(selected_platform_index)
            valid_platforms.remove(selected_platform_index)

        # Chooses where fire guy spawns
        if floor_Index > 0:
            platformIndex = random.randint(2, num_platforms)
            while platformIndex in shifting_platforms:
                platformIndex = random.randint(2, num_platforms)
            platform_ = floors[floor_Index].platforms[platformIndex]
            fire_guy.x = platform_.x + platform_.width // 2 - fire_guy.size // 2
            fire_guy.y = platform_.y - fire_guy.size
            fire_guy.visible = True
            fire_guy.current_Platform = platform_

        # Spawn new balls after floor 5, up to 4 balls at once
        if floor_Index >= 5:
            if len(balls) < 4:
                ball = sprite()
                ball.x, ball.y, ball.size, ball.speed = -100, -100, 10, 2
                ball.width, ball.height = 10, 10
                ball.x_del = random.choice([-1, 1])
                ball.y_del = random.choice([-1, 1])
                ball.image = pygame.image.load("Data/Sprites/ball.png").convert_alpha()
                ball.visible = True
                ball.x = random.randint(0, WIDTH - ball.size)
                ball.y = random.randint(0, (HEIGHT - ball.size - 10) // 2)
                balls.append(ball)

        # Increase fire guy speed after floor 4
        if floor_Index > 1:
            if fire_guy.speed < 1:
                fire_guy.speed += 0.1
                numOfPoints = int(100*(1/fire_guy.speed))

        if floor_Index > 10:
            for platform_ in floors[floor_Index].platforms:
                platform_.speed += 0.1 * floor_Index / 10

    # Fire guy changing platforms
    if fire_guy.moving:
        if fire_guy.path_index < len(fire_guy.path):
            fire_guy.x, fire_guy.y = fire_guy.path[fire_guy.path_index]

        if fire_guy.x == fire_guy.path[-1][0] and fire_guy.y == fire_guy.path[-1][1]:
              fire_guy.moving = False
              smoke_sound.play()
              smoke.visible = False
              
        fire_guy.path_index += 1

    # Check for landing on platforms
    if little_dude.jumpDuration == 0:
        for platform_ in floors[floor_Index].platforms:
            if (
                ((little_dude.x + little_dude.size) >= platform_.x) and 
                (little_dude.x <= (platform_.x + platform_.width)) and 
                ((little_dude.y + little_dude.size) <= platform_.y) and 
                (little_dude.y >= (platform_.y - 80)) and platform_.visible
                ):
                little_dude.height_limit = platform_.y - little_dude.size
                little_dude.current_Platform = platform_
                break
            else:
                little_dude.height_limit = HEIGHT - little_dude.size

    # Gravity
    if little_dude.y < little_dude.height_limit and little_dude.jumpDuration == 0:
        if little_dude.height_limit - little_dude.y < 3:
            little_dude.y += 1
        elif little_dude.height_limit - little_dude.y >= 3:
            little_dude.y += 3
        if (little_dude.current_Platform is not little_dude.last_Platform
            and little_dude.y == little_dude.height_limit):
            if little_dude.last_Platform != floors[floor_Index].platforms[0] and floor_Index > 50:
                destroy_Platform(little_dude.last_Platform)
            if fire_guy.visible and little_dude.current_Platform != floors[floor_Index].platforms[0] and fire_guy.moving is False:
                fire_guy.last_Platform = fire_guy.current_Platform
                fire_guy_target_platform()
            little_dude.last_Platform = little_dude.current_Platform

    # Fire guy collision with player
    if fire_guy.visible:
        if is_colliding(little_dude, fire_guy):
            reset()

    # Player collides with smoke sprite
    if smoke.visible:
        if is_colliding(little_dude, smoke):
            powerUp_sound.play()
            smoke.visible = False
            bolt.visible = True
            bolt.x = smoke.x
            bolt.y = smoke.y

    # Cast bolt towards fire guy
    if bolt.visible:
        if bolt.x > fire_guy.x:
            bolt.x -= 2
        elif bolt.x < fire_guy.x:
            bolt.x += 2
        if bolt.y > fire_guy.y:
            bolt.y -= 2
        elif bolt.y < fire_guy.y:
            bolt.y += 2

        if is_colliding(bolt, fire_guy):
            fire_guy_dead = 1
            fire_explosion_sound.play()
            fire_guy.visible = False
            smoke.visible = False
            bolt.visible = False
            fire_guy.moving = False

    # Lava
    if little_dude.y >= HEIGHT - little_dude.size:
        reset()

    # Shift platforms at higher floors
    for i, platform_ in enumerate(floors[floor_Index].platforms):
        if i in shifting_platforms:
            if platform_.direction == "right":
                platform_.x += platform_.speed
                if platform_.x + platform_.width >= WIDTH:
                    platform_.direction = "left"
            else:
                platform_.x -= platform_.speed
                if platform_.x <= 0:
                    platform_.direction = "right"

    # Direction tracking
    if little_dude.x > lastLoc and little_dude.direction != "right":
        little_dude.direction = "right"
        little_dude.image = pygame.transform.flip(little_dude.image, True, False)
    elif little_dude.x < lastLoc and little_dude.direction != "left":
        little_dude.direction = "left"
        little_dude.image = pygame.transform.flip(little_dude.image, True, False)

    # Ball physics
    for ball_ in balls:
        if is_colliding(little_dude, ball_):
            reset()
        if ball_.x <= 0 or ball_.x >= WIDTH - ball_.size:
            ball_.x_del = -ball_.x_del
        if ball_.y <= 0 or ball_.y >= HEIGHT - ball_.size:
            ball_.y_del = -ball_.y_del

        ball_.x += ball_.x_del * ball_.speed
        ball_.y += ball_.y_del * ball_.speed

    # Render floor number text
    font_size = 40
    text_font = pygame.font.SysFont('arial', font_size)
    floor_num = floor_Index + 1
    text = text_font.render("Floor " + str(floor_num), True, (255, 255, 255))
    text_rect = text.get_rect()
    text_rect.topleft = (10, 0)
        
    render_display()
