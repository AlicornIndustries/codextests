import math
import random
from dataclasses import dataclass

import pygame
from pygame.math import Vector2

# Constants
WIDTH, HEIGHT = 960, 720
DT = 1 / 60
FPS = 60

PLANET_POS = Vector2(WIDTH / 2, HEIGHT / 2)
PLANET_RADIUS = 26
PLANET_MU = 5200  # Gravitational parameter for planet
PLANET_MAX_HEALTH = 100

SHIP_RADIUS = 6
SHIP_THRUST = 220
SHIP_TURN_SPEED = 3.5
SHIP_MAX_SPEED = 450

RAILGUN_SPEED = 650
RAILGUN_RECOIL = 80
RAILGUN_COOLDOWN = 0.35
RAILGUN_DAMAGE = 18

MISSILE_SPEED = 300
MISSILE_TURN_RATE = 4.0
MISSILE_DAMAGE = 45
MISSILE_COOLDOWN = 0.8

ALIEN_SPEED_BASE = 60
ALIEN_RADIUS = 10

UPGRADE_OPTIONS = [
    "Reinforce railgun (faster fire, +damage)",
    "Refill missile racks (+2 missiles)",
    "Boost thrusters (+thrust)",
]


@dataclass
class Projectile:
    pos: Vector2
    vel: Vector2
    damage: int
    radius: int = 3
    ttl: float = 3.0


@dataclass
class Missile:
    pos: Vector2
    vel: Vector2
    target: "Alien | None"
    damage: int
    radius: int = 4
    ttl: float = 6.0


@dataclass
class Alien:
    pos: Vector2
    vel: Vector2
    health: int
    radius: int = ALIEN_RADIUS

    def update(self, dt: float):
        self.pos += self.vel * dt


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orbital Defense")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 28)
large_font = pygame.font.Font(None, 48)

ship_pos = Vector2(WIDTH / 2 + 240, HEIGHT / 2)
ship_vel = Vector2(0, -160)
ship_angle = math.pi / 2

railgun_timer = 0.0
missile_timer = 0.0

railgun_damage = RAILGUN_DAMAGE
railgun_cooldown = RAILGUN_COOLDOWN
ship_thrust = SHIP_THRUST
missiles_available = 4

projectiles: list[Projectile] = []
missiles: list[Missile] = []
aliens: list[Alien] = []

wave = 1
planet_health = PLANET_MAX_HEALTH
state = "wave"  # wave, upgrade, game_over


def gravitational_acc(pos: Vector2, body_pos: Vector2, mu: float) -> Vector2:
    r = body_pos - pos
    dist3 = (r.length() + 1e-5) ** 3
    return mu * r / dist3



def spawn_wave(count: int):
    spawned = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        distance = random.uniform(320, 400)
        pos = PLANET_POS + Vector2(math.cos(angle), math.sin(angle)) * distance
        to_planet = (PLANET_POS - pos).normalize()
        speed = ALIEN_SPEED_BASE + wave * 8 + random.uniform(-10, 20)
        vel = to_planet * speed
        spawned.append(Alien(pos=pos, vel=vel, health=40 + wave * 6))
    return spawned


aliens = spawn_wave(4 + wave)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and state == "upgrade":
            if event.key in (pygame.K_1, pygame.K_KP1):
                railgun_cooldown = max(0.12, railgun_cooldown - 0.06)
                railgun_damage += 6
                state = "wave"
            elif event.key in (pygame.K_2, pygame.K_KP2):
                missiles_available += 2
                state = "wave"
            elif event.key in (pygame.K_3, pygame.K_KP3):
                ship_thrust += 40
                state = "wave"

    keys = pygame.key.get_pressed()
    mouse_pressed = pygame.mouse.get_pressed()
    mouse_pos = Vector2(pygame.mouse.get_pos())

    if state == "wave":
        if keys[pygame.K_a]:
            ship_angle -= SHIP_TURN_SPEED * DT
        if keys[pygame.K_d]:
            ship_angle += SHIP_TURN_SPEED * DT

        thrust_force = Vector2(0, 0)
        forward = Vector2(math.cos(ship_angle), math.sin(ship_angle))
        if keys[pygame.K_w]:
            thrust_force += forward * ship_thrust
        if keys[pygame.K_s]:
            thrust_force -= forward * ship_thrust * 0.6

        railgun_timer = max(0.0, railgun_timer - DT)
        missile_timer = max(0.0, missile_timer - DT)

        if (mouse_pressed[0] or keys[pygame.K_SPACE]) and railgun_timer == 0.0:
            shot_vel = forward * RAILGUN_SPEED + ship_vel
            projectiles.append(
                Projectile(pos=ship_pos + forward * 12, vel=shot_vel, damage=railgun_damage)
            )
            ship_vel -= forward * RAILGUN_RECOIL
            railgun_timer = railgun_cooldown

        if mouse_pressed[2] and missile_timer == 0.0 and missiles_available > 0:
            target = None
            if aliens:
                target = min(aliens, key=lambda a: a.pos.distance_to(ship_pos))
            missiles.append(
                Missile(
                    pos=ship_pos + forward * 10,
                    vel=forward * MISSILE_SPEED + ship_vel,
                    target=target,
                    damage=MISSILE_DAMAGE,
                )
            )
            missiles_available -= 1
            missile_timer = MISSILE_COOLDOWN

        acc = gravitational_acc(ship_pos, PLANET_POS, PLANET_MU)
        acc += thrust_force
        ship_vel += acc * DT
        if ship_vel.length() > SHIP_MAX_SPEED:
            ship_vel.scale_to_length(SHIP_MAX_SPEED)
        ship_pos += ship_vel * DT

        for projectile in projectiles[:]:
            projectile.pos += projectile.vel * DT
            projectile.ttl -= DT
            if projectile.ttl <= 0:
                projectiles.remove(projectile)

        for missile in missiles[:]:
            missile.ttl -= DT
            if missile.ttl <= 0:
                missiles.remove(missile)
                continue
            if missile.target and missile.target in aliens:
                desired = (missile.target.pos - missile.pos).normalize()
                current = missile.vel.normalize() if missile.vel.length() > 1 else desired
                steer = desired - current
                missile.vel += steer * MISSILE_TURN_RATE * MISSILE_SPEED * DT
            missile.pos += missile.vel * DT

        for alien in aliens[:]:
            alien.update(DT)
            if alien.pos.distance_to(PLANET_POS) <= PLANET_RADIUS:
                planet_health -= 10
                aliens.remove(alien)
                continue

            for projectile in projectiles[:]:
                if alien.pos.distance_to(projectile.pos) <= alien.radius + projectile.radius:
                    alien.health -= projectile.damage
                    projectiles.remove(projectile)
                    break

            for missile in missiles[:]:
                if alien.pos.distance_to(missile.pos) <= alien.radius + missile.radius:
                    alien.health -= missile.damage
                    missiles.remove(missile)
                    break

            if alien.health <= 0:
                aliens.remove(alien)

        if planet_health <= 0:
            state = "game_over"

        if not aliens and state == "wave":
            wave += 1
            state = "upgrade"
            missiles_available += 1
            aliens = spawn_wave(4 + wave)

    screen.fill((5, 8, 18))

    # Stars
    for i in range(4):
        pygame.draw.circle(
            screen,
            (80, 80, 110),
            ((i * 211 + 40) % WIDTH, (i * 163 + 90) % HEIGHT),
            2,
        )

    pygame.draw.circle(screen, (80, 120, 220), PLANET_POS, PLANET_RADIUS)
    pygame.draw.circle(screen, (40, 70, 140), PLANET_POS, PLANET_RADIUS - 8)

    for alien in aliens:
        pygame.draw.circle(screen, (120, 255, 140), alien.pos, alien.radius)
        pygame.draw.circle(screen, (30, 80, 40), alien.pos, alien.radius, 2)

    for projectile in projectiles:
        pygame.draw.circle(screen, (255, 220, 150), projectile.pos, projectile.radius)

    for missile in missiles:
        pygame.draw.circle(screen, (255, 120, 120), missile.pos, missile.radius)

    # Draw ship
    ship_tip = ship_pos + Vector2(math.cos(ship_angle), math.sin(ship_angle)) * 14
    ship_left = ship_pos + Vector2(math.cos(ship_angle + 2.4), math.sin(ship_angle + 2.4)) * 10
    ship_right = ship_pos + Vector2(math.cos(ship_angle - 2.4), math.sin(ship_angle - 2.4)) * 10
    pygame.draw.polygon(screen, (240, 240, 255), [ship_tip, ship_left, ship_right])

    # HUD
    hud_lines = [
        f"Wave: {wave}",
        f"Planet HP: {planet_health}/{PLANET_MAX_HEALTH}",
        f"Missiles: {missiles_available}",
    ]
    for i, line in enumerate(hud_lines):
        text = font.render(line, True, (220, 220, 240))
        screen.blit(text, (16, 16 + i * 22))

    if state == "upgrade":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        title = large_font.render("Upgrade Phase", True, (255, 255, 255))
        screen.blit(title, (WIDTH / 2 - title.get_width() / 2, HEIGHT / 2 - 120))
        for idx, option in enumerate(UPGRADE_OPTIONS, start=1):
            option_text = font.render(f"{idx}. {option}", True, (220, 220, 240))
            screen.blit(option_text, (WIDTH / 2 - option_text.get_width() / 2, HEIGHT / 2 - 60 + idx * 28))
        hint = font.render("Choose upgrade with 1-3", True, (180, 180, 200))
        screen.blit(hint, (WIDTH / 2 - hint.get_width() / 2, HEIGHT / 2 + 60))

    if state == "game_over":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        text = large_font.render("Planet Lost", True, (255, 80, 80))
        screen.blit(text, (WIDTH / 2 - text.get_width() / 2, HEIGHT / 2 - 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
