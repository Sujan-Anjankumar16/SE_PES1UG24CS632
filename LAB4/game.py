import pygame
import random
import math
import time

WIDTH, HEIGHT = 900, 560
FPS = 60
BG = (30,35,25)


class ExplosiveBarrel:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 24, 32)
        self.color = (180, 100, 30)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)
        pygame.draw.circle(screen, (220, 180, 40), self.rect.center, 5)


class Zombie:
    SPEED = 1.5

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.color = (60,140,60)
        self.hp = 3
        self.wobble = random.uniform(0, 6.28)
        self.frame = 0

    def update(self, player_pos):
        px, py = player_pos
        cx, cy = self.rect.center
        dx, dy = px-cx, py-cy
        dist = (dx**2+dy**2)**0.5
        if dist:
            self.pos_x += dx/dist*self.SPEED
            self.pos_y += dy/dist*self.SPEED
            self.rect.x = int(self.pos_x)
            self.rect.y = int(self.pos_y)
        self.frame += 1

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.2)*3)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=5)
        for ex in [draw_rect.x+6, draw_rect.x+18]:
            pygame.draw.circle(screen, (200,40,40), (ex, draw_rect.y+10), 4)


class FastZombie(Zombie):
    SPEED = 2.5

    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect = pygame.Rect(x, y, 20, 20)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.color = (220,180,40)
        self.hp = 1


class TankZombie(Zombie):
    SPEED = 0.8

    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect = pygame.Rect(x, y, 45, 45)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.color = (120,60,160)
        self.hp = 6


def spawn_zombie(width, height, player_rect, margin=120, zombie_class=None):
    while True:
        if zombie_class == FastZombie:
            zombie_size = 20
        elif zombie_class == TankZombie:
            zombie_size = 45
        else:
            zombie_size = 30

        if zombie_class is None:
            zombie_type = random.random()

            if zombie_type < 0.20:
                zombie_class = FastZombie
                zombie_size = 20
            elif zombie_type < 0.35:
                zombie_class = TankZombie
                zombie_size = 45
            else:
                zombie_class = Zombie
                zombie_size = 30

        x = random.randint(0, width-zombie_size)
        y = random.randint(0, height-zombie_size)
        rect = pygame.Rect(x, y, zombie_size, zombie_size)

        if not rect.colliderect(player_rect.inflate(margin, margin)):
            return zombie_class(x, y)


SPEED = 4


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (60,160,220)
        self.bullets = []
        self.shoot_cooldown = 0
        self.hp = 3
        self.invincible_until = 0
        self.invincibility_duration = 1000
        self.max_ammo = 12
        self.ammo = self.max_ammo
        self.reload_duration = 2000
        self.reloading_until = 0

    def move(self, keys, width, height):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = SPEED
        self.rect.x = max(0, min(width-self.rect.width, self.rect.x+dx))
        self.rect.y = max(0, min(height-self.rect.height, self.rect.y+dy))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        self.update_reload()

    def shoot(self, target_pos):
        if self.is_reloading():
            return

        if self.ammo <= 0:
            self.start_reload()
            return

        if self.shoot_cooldown > 0:
            return

        cx, cy = self.rect.center
        tx, ty = target_pos
        dx, dy = tx-cx, ty-cy
        dist = (dx**2+dy**2)**0.5
        if dist == 0: return
        vx, vy = dx/dist*10, dy/dist*10
        self.bullets.append(pygame.Rect(cx-4, cy-4, 8, 8))
        self.bullets.append([cx-4, cy-4, vx, vy])
        self.bullets.pop(-2)

        self.ammo -= 1

        if self.ammo == 0:
            self.start_reload()

        self.shoot_cooldown = 15

    def take_damage(self):
        current_time = pygame.time.get_ticks()

        if current_time < self.invincible_until:
            return False

        self.hp -= 1
        self.invincible_until = current_time + self.invincibility_duration

        return True

    def is_invincible(self):
        return pygame.time.get_ticks() < self.invincible_until

    def start_reload(self):
        if self.ammo < self.max_ammo and self.reloading_until == 0:
            self.reloading_until = pygame.time.get_ticks() + self.reload_duration

    def update_reload(self):
        if self.reloading_until > 0:
            if pygame.time.get_ticks() >= self.reloading_until:
                self.ammo = self.max_ammo
                self.reloading_until = 0

    def is_reloading(self):
        return self.reloading_until > 0    

    def update_bullets(self, width, height):
        live = []
        for b in self.bullets:
            b[0] += b[2]; b[1] += b[3]
            if 0 <= b[0] <= width and 0 <= b[1] <= height:
                live.append(b)
        self.bullets = live

    def draw(self, screen):
        if self.is_invincible():
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        else:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        for b in self.bullets:
            pygame.draw.circle(screen, (255,220,60), (int(b[0]), int(b[1])), 5)


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Zombie Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24)
        self.hud_font = pygame.font.SysFont("monospace", 16)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH//2, HEIGHT//2)

        self.wave = 1
        self.kills = 0
        self.kills_to_next = 8

        self.zombies = [
            spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_class=FastZombie),
            spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_class=TankZombie)
        ]

        for _ in range(self.kills_to_next - 2):
            self.zombies.append(
                spawn_zombie(WIDTH, HEIGHT, self.player.rect)
            )

        self.barrels = [
            ExplosiveBarrel(100, 100),
            ExplosiveBarrel(300, 200),
            ExplosiveBarrel(600, 150),
            ExplosiveBarrel(700, 400)
        ]

        self.score = 0
        self.game_over = False
        self.start_time = time.time()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                self.player.shoot(event.pos)
        return True

    def update(self):
        if self.game_over: return
        keys = pygame.key.get_pressed()
        self.player.move(keys, WIDTH, HEIGHT)
        self.player.update_bullets(WIDTH, HEIGHT)
        self.score = int(time.time() - self.start_time)

        for z in self.zombies:
            z.update(self.player.rect.center)
            if z.rect.colliderect(self.player.rect):
                if self.player.take_damage():
                    if self.player.hp <= 0:
                        self.game_over = True

        dead = []
        exploded_barrels = []

        for z in self.zombies:
            for b in self.player.bullets[:]:
                bx, by = int(b[0]), int(b[1])

                if z.rect.collidepoint(bx, by):
                    if z.hit():
                        dead.append(z)

                    if b in self.player.bullets:
                        self.player.bullets.remove(b)

        for barrel in self.barrels[:]:
            for b in self.player.bullets[:]:
                bx, by = int(b[0]), int(b[1])

                if barrel.rect.collidepoint(bx, by):
                    exploded_barrels.append(barrel)

                    if b in self.player.bullets:
                        self.player.bullets.remove(b)

        for z in dead:
            if z in self.zombies:
                self.zombies.remove(z)
                self.kills += 1
                self.score += 10

        for barrel in exploded_barrels:
            if barrel in self.barrels:
                explosion_radius = 100

                for z in self.zombies[:]:
                    dx = z.rect.centerx - barrel.rect.centerx
                    dy = z.rect.centery - barrel.rect.centery
                    distance = (dx**2 + dy**2) ** 0.5

                    if distance <= explosion_radius:
                        self.zombies.remove(z)
                        self.kills += 1
                        self.score += 10

                self.barrels.remove(barrel)        

        if self.kills >= self.kills_to_next:
            self.kills = 0
            self.wave += 1
            self.kills_to_next = 8 + self.wave * 2

            self.barrels = [
                ExplosiveBarrel(100, 100),
                ExplosiveBarrel(300, 200),
                ExplosiveBarrel(600, 150),
                ExplosiveBarrel(700, 400)
            ]   

            self.zombies.append(
                spawn_zombie(
                WIDTH,
                HEIGHT,
                self.player.rect,
                zombie_class=FastZombie
            )
        )

            self.zombies.append(
                spawn_zombie(
                    WIDTH,
                    HEIGHT,
                    self.player.rect,
                    zombie_class=TankZombie
            )
        )

            for _ in range(self.kills_to_next - 2):
                self.zombies.append(
                     spawn_zombie(WIDTH, HEIGHT, self.player.rect)
                )

    def draw(self):
        self.screen.fill(BG)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, (40,45,35), (x,0), (x,HEIGHT), 1)
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, (40,45,35), (0,y), (WIDTH,y), 1)
        for z in self.zombies: z.draw(self.screen)
        for barrel in self.barrels: barrel.draw(self.screen)
        self.player.draw(self.screen)
        hud_bg = pygame.Rect(0, 0, WIDTH, 40)
        pygame.draw.rect(self.screen, (15,20,15), hud_bg)
        hud = self.hud_font.render(
            f"HP: {self.player.hp} | Ammo: {self.player.ammo}/{self.player.max_ammo} | Wave: {self.wave} Score: {self.score} Kills: {self.kills}/{self.kills_to_next}  |  WASD Move, Click Shoot, R Restart",
            True, (160,220,120))
        self.screen.blit(hud, (8, 8))
        if self.game_over:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov, (0,0))
            m = self.big_font.render("DEVOURED!", True, (180,40,40))
            s = self.font.render(f"Wave {self.wave} | Score {self.score} | Press R", True, (200,200,200))
            self.screen.blit(m, (WIDTH//2-m.get_width()//2, HEIGHT//2-40))
            self.screen.blit(s, (WIDTH//2-s.get_width()//2, HEIGHT//2+20))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()