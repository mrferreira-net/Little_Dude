import pygame
import sys

# Initialize pygame
pygame.init()

# Window setup
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Little Dude")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Load or create a sprite (here we use a simple rectangle)
player_size = 50
player_color = (0, 200, 255)
player_x = WIDTH // 2
player_y = HEIGHT - player_size
player_speed = 5
player_jumpDuration = 0
player_jump = False

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Key handling
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < WIDTH - player_size:
        player_x += player_speed
    if keys[pygame.K_UP] and player_jumpDuration == 0 and player_y >= HEIGHT - player_size:
        player_jumpDuration = 20
    if keys[pygame.K_DOWN] and player_y < HEIGHT - player_size:
        player_y += player_speed

    if player_jumpDuration > 0 and player_y > 0:
        player_y -= player_speed
        player_jumpDuration -= 1

    # Gravity
    if player_y < HEIGHT - player_size and player_jumpDuration == 0:
        player_y += 2

    # Fill screen
    screen.fill((30, 30, 30))

    # Draw sprite
    pygame.draw.rect(screen, player_color, (player_x, player_y, player_size, player_size))

    # Update display
    pygame.display.flip()

    # Cap FPS
    clock.tick(60)
