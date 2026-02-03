import ctypes
import pygame
import sys

myappid = 'mycompany.myproduct.subproduct.version' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

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
    width = 100
    height = 20
    color = (100, 50, 0)
    x = WIDTH // 2 - width // 2
    y = HEIGHT - 100
    


# Game loop
direction = "right"
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
    pygame.draw.rect(screen, platform.color, (platform.x, platform.y, platform.width, platform.height))

    # Update display
    pygame.display.flip()

    # Cap FPS
    clock.tick(60)
