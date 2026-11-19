"""
Simple Cycling Game (pygame)

"""
import math
import random
import sys

import pygame

WIDTH, HEIGHT = 800, 400
GROUND_Y = 320
FPS = 60

SKY = (135, 206, 235)
GRASS = (88, 160, 70)
ROAD = (70, 70, 75)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (220, 60, 60)
GOLD = (255, 205, 40)
GRAY = (120, 120, 120)


class Cyclist:
    WHEEL_R = 20
    X = 120

    def __init__(self):
        self.y = GROUND_Y - self.WHEEL_R  # wheel-center height
        self.vy = 0.0
        self.angle = 0.0
        self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.vy = -13.5
            self.on_ground = False

    def update(self, speed):
        self.vy += 0.7  # gravity
        self.y += self.vy
        floor = GROUND_Y - self.WHEEL_R
        if self.y >= floor:
            self.y = floor
            self.vy = 0
            self.on_ground = True
        self.angle += speed * 0.05

    def rect(self):
        """Hitbox (slightly smaller than the sprite to feel fair)."""
        return pygame.Rect(self.X - 30, self.y - 45, 60, 60 + self.WHEEL_R - 15)

    def draw(self, surf):
        x, y, r = self.X, int(self.y), self.WHEEL_R
        back, front = (x - 28, y), (x + 28, y)

        # wheels + spokes
        for cx, cy in (back, front):
            pygame.draw.circle(surf, BLACK, (cx, cy), r, 3)
            for i in range(4):
                a = self.angle + i * math.pi / 2
                pygame.draw.line(
                    surf, GRAY, (cx, cy),
                    (cx + r * math.cos(a), cy + r * math.sin(a)), 1,
                )

        # frame
        seat = (x - 10, y - 30)
        pedals = (x, y)
        bars = (x + 20, y - 32)
        pygame.draw.line(surf, RED, back, pedals, 3)
        pygame.draw.line(surf, RED, back, seat, 3)
        pygame.draw.line(surf, RED, seat, pedals, 3)
        pygame.draw.line(surf, RED, seat, bars, 3)
        pygame.draw.line(surf, RED, pedals, bars, 3)
        pygame.draw.line(surf, RED, bars, front, 3)

        # rider
        hip = (seat[0], seat[1] - 3)
        shoulder = (x + 2, y - 55)
        pygame.draw.line(surf, (40, 60, 160), hip, shoulder, 5)        # torso
        pygame.draw.line(surf, (40, 60, 160), shoulder, bars, 3)       # arm
        foot_a = self.angle * 2
        foot = (x + 8 * math.cos(foot_a), y + 8 * math.sin(foot_a))
        pygame.draw.line(surf, (30, 30, 30), hip, foot, 4)             # leg
        pygame.draw.circle(surf, (255, 220, 180), (shoulder[0] + 3, shoulder[1] - 9), 8)  # head
        pygame.draw.arc(surf, RED, (shoulder[0] - 5, shoulder[1] - 19, 16, 14), 0, math.pi, 4)  # helmet


class Rock:
    def __init__(self, x):
        self.w = random.randint(28, 44)
        self.h = random.randint(24, 40)
        self.x = x

    def update(self, speed):
        self.x -= speed

    def rect(self):
        return pygame.Rect(self.x + 4, GROUND_Y - self.h + 6, self.w - 8, self.h - 6)

    def draw(self, surf):
        pts = [
            (self.x, GROUND_Y),
            (self.x + self.w * 0.2, GROUND_Y - self.h * 0.8),
            (self.x + self.w * 0.55, GROUND_Y - self.h),
            (self.x + self.w, GROUND_Y - self.h * 0.3),
            (self.x + self.w, GROUND_Y),
        ]
        pygame.draw.polygon(surf, (110, 105, 100), pts)
        pygame.draw.polygon(surf, BLACK, pts, 2)


class Coin:
    def __init__(self, x):
        self.x = x
        self.y = random.choice([GROUND_Y - 40, GROUND_Y - 90, GROUND_Y - 130])
        self.r = 10

    def update(self, speed):
        self.x -= speed

    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

    def draw(self, surf, t):
        squish = abs(math.sin(t * 0.1 + self.x * 0.02))
        w = max(3, int(self.r * squish))
        pygame.draw.ellipse(surf, GOLD, (self.x - w, self.y - self.r, w * 2, self.r * 2))
        pygame.draw.ellipse(surf, BLACK, (self.x - w, self.y - self.r, w * 2, self.r * 2), 2)


class Cloud:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(20, 140)
        self.s = random.uniform(0.3, 0.8)

    def update(self, speed):
        self.x -= speed * self.s * 0.3
        if self.x < -80:
            self.x = WIDTH + random.randint(0, 100)
            self.y = random.randint(20, 140)

    def draw(self, surf):
        for dx, dy, r in ((0, 0, 18), (20, -8, 22), (42, 0, 16), (20, 6, 18)):
            pygame.draw.circle(surf, WHITE, (int(self.x + dx), int(self.y + dy)), r)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cycling Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24, bold=True)
        self.big = pygame.font.SysFont("arial", 56, bold=True)
        self.clouds = [Cloud() for _ in range(5)]
        self.best = 0
        self.reset()

    def reset(self):
        self.player = Cyclist()
        self.rocks = []
        self.coins = []
        self.speed = 6.0
        self.distance = 0.0
        self.coin_count = 0
        self.next_rock = 500
        self.next_coin = 300
        self.road_offset = 0.0
        self.tick = 0
        self.alive = True

    # ---- logic -----------------------------------------------------------
    def spawn(self):
        if self.next_rock <= 0:
            self.rocks.append(Rock(WIDTH + 20))
            # more speed -> need a bit more gap to be jumpable
            self.next_rock = random.randint(int(220 + self.speed * 18), int(420 + self.speed * 22))
        if self.next_coin <= 0:
            base = WIDTH + 20
            for i in range(random.randint(1, 4)):
                c = Coin(base + i * 35)
                if i:
                    c.y = self.coins[-1].y  # keep a row level
                self.coins.append(c)
            self.next_coin = random.randint(250, 550)

    def update(self):
        self.tick += 1
        for c in self.clouds:
            c.update(self.speed)
        if not self.alive:
            return

        self.speed = min(14.0, 6.0 + self.distance / 1500)
        self.distance += self.speed / 10
        self.road_offset = (self.road_offset + self.speed) % 40
        self.next_rock -= self.speed
        self.next_coin -= self.speed

        self.spawn()
        self.player.update(self.speed)

        for r in self.rocks:
            r.update(self.speed)
        for c in self.coins:
            c.update(self.speed)
        self.rocks = [r for r in self.rocks if r.x > -60]
        self.coins = [c for c in self.coins if c.x > -30]

        hitbox = self.player.rect()
        for c in self.coins[:]:
            if hitbox.colliderect(c.rect()):
                self.coins.remove(c)
                self.coin_count += 1
        for r in self.rocks:
            if hitbox.colliderect(r.rect()):
                self.alive = False
                self.best = max(self.best, self.score)

    @property
    def score(self):
        return int(self.distance) + self.coin_count * 10

    # ---- drawing ---------------------------------------------------------
    def draw(self):
        s = self.screen
        s.fill(SKY)
        for c in self.clouds:
            c.draw(s)

        # distant hills
        for i in range(-1, 5):
            hx = i * 220 - (self.distance * 3) % 220
            pygame.draw.circle(s, (110, 170, 100), (int(hx + 110), GROUND_Y + 60), 130)

        pygame.draw.rect(s, GRASS, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.rect(s, ROAD, (0, GROUND_Y, WIDTH, 50))
        for x in range(-40, WIDTH + 40, 40):  # moving lane dashes
            pygame.draw.rect(s, WHITE, (x - self.road_offset, GROUND_Y + 24, 20, 4))

        for r in self.rocks:
            r.draw(s)
        for c in self.coins:
            c.draw(s, self.tick)
        self.player.draw(s)

        # HUD
        s.blit(self.font.render(f"Score: {self.score}", True, BLACK), (15, 12))
        s.blit(self.font.render(f"Coins: {self.coin_count}", True, BLACK), (15, 42))
        s.blit(self.font.render(f"Best: {self.best}", True, BLACK), (WIDTH - 140, 12))

        if not self.alive:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            s.blit(overlay, (0, 0))
            t = self.big.render("CRASH!", True, WHITE)
            s.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
            t = self.font.render("Press R to ride again", True, WHITE)
            s.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

        pygame.display.flip()

    # ---- main loop -------------------------------------------------------
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if e.key in (pygame.K_SPACE, pygame.K_UP) and self.alive:
                        self.player.jump()
                    if e.key == pygame.K_r and not self.alive:
                        self.reset()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()