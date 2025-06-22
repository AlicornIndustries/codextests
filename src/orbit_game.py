import math
import pygame
from pygame.math import Vector2

# Constants
WIDTH, HEIGHT = 800, 600
DT = 1/60

PLANET_POS = Vector2(WIDTH/2, HEIGHT/2)
PLANET_MU = 2000  # Gravitational parameter for planet

MOON_ORBIT_RADIUS = 150
MOON_MU = 500
MOON_ANGULAR_SPEED = 0.5  # radians per second

SHIP_THRUST = 200

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

ship_pos = Vector2(WIDTH/2 + 200, HEIGHT/2)
ship_vel = Vector2(0, -120)

moon_angle = 0.0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    thrust = Vector2(0, 0)
    if keys[pygame.K_LEFT]:
        thrust.x -= SHIP_THRUST
    if keys[pygame.K_RIGHT]:
        thrust.x += SHIP_THRUST
    if keys[pygame.K_UP]:
        thrust.y -= SHIP_THRUST
    if keys[pygame.K_DOWN]:
        thrust.y += SHIP_THRUST

    # Update moon position
    moon_angle += MOON_ANGULAR_SPEED * DT
    moon_pos = PLANET_POS + Vector2(math.cos(moon_angle), math.sin(moon_angle)) * MOON_ORBIT_RADIUS

    # Gravitational acceleration from planet and moon
    def gravitational_acc(pos, body_pos, mu):
        r = body_pos - pos
        dist3 = (r.length() + 1e-5) ** 3
        return mu * r / dist3

    acc = gravitational_acc(ship_pos, PLANET_POS, PLANET_MU)
    acc += gravitational_acc(ship_pos, moon_pos, MOON_MU)
    acc += thrust

    ship_vel += acc * DT
    ship_pos += ship_vel * DT

    # Orbit prediction
    pred_pos = ship_pos.copy()
    pred_vel = ship_vel.copy()
    pred_points = []
    moon_angle_pred = moon_angle
    for _ in range(300):
        moon_angle_pred += MOON_ANGULAR_SPEED * DT
        moon_pred = PLANET_POS + Vector2(math.cos(moon_angle_pred), math.sin(moon_angle_pred)) * MOON_ORBIT_RADIUS
        acc_pred = gravitational_acc(pred_pos, PLANET_POS, PLANET_MU)
        acc_pred += gravitational_acc(pred_pos, moon_pred, MOON_MU)
        pred_vel += acc_pred * DT
        pred_pos += pred_vel * DT
        pred_points.append(pred_pos.copy())

    # Drawing
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (100, 100, 255), PLANET_POS, 20)
    pygame.draw.circle(screen, (200, 200, 200), moon_pos, 8)
    pygame.draw.circle(screen, (255, 0, 0), ship_pos, 5)

    if len(pred_points) > 1:
        pygame.draw.lines(screen, (0, 255, 0), False, pred_points, 1)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
