import os
import sys
import random
import time
import pygame


screen_width = 1024 // 2
screen_height = 1536 // 2



class Status:
    Main = 0
    Game = 1
    Over = 2

class Bird:
    def __init__(self, name: str, surface: pygame.Surface, img_path: str = "", sound: str = "owo",mass=5,speed=3,has_item=False,has_item_effect=True):
        self.x = 120
        self.y = screen_height / 2
        self.sound = sound
        self.yspeed = 0
        self.g = 20.0
        self.rotate = 0
        self.name = name
        self.surface = surface
        self.img = None
        self.is_flying = False
        self.fly_cooldown = 0.1
        self.fly_duration = 0.5
        self.flying_time = 0
        self.fly_cooling = 0
        self.mass = mass
        self.speed = speed
        self.has_item = has_item
        self.has_item_effect = has_item_effect
        # self.is_actable = speed > 0 이 방법도 있음
        try:
            p = os.path.join("assets", img_path) if img_path else None
            if p and os.path.exists(p):
                self.img = pygame.image.load(p)
                self.img = pygame.transform.scale(self.img, (50, 50))
        except Exception as e:
            print(f"no image found : {img_path} ({e})")
        if self.img is None:
            self.img = pygame.Surface((50, 50), pygame.SRCALPHA)
            self.img.fill((255, 200, 0))

    def update(self, dt: float):
        if self.is_flying:
            self.flying_time -= dt
            if self.flying_time < 0:
                self.is_flying = False
        else:
            self.yspeed += self.g * dt * self.mass / 5
            self.fly_cooling += dt
        self.rotate = max(-30, min(30, self.yspeed * -2))
        self.y += self.yspeed

    def draw(self, screen: pygame.Surface):
        r_img = pygame.transform.rotate(self.img, self.rotate)
        self.rect = pygame.Rect(int(self.x), int(self.y), 50, 50)
        screen.blit(r_img, (self.x, self.y))

    def bird_sound(self):
        print(f"{self.name} : {self.sound}")
        if self.yspeed > 0:
            self.yspeed = 0
        self.yspeed -= 5 * (1 + self.speed / 8)
        self.is_flying = False
    def bird_running(self):
        if self.speed > 0:
            print(f"속도 : {self.mass * self.speed * (1 + int(self.has_item and self.has_item_effect) * 1)}")
            if self.has_item:
                print("아이템으로 속도가 빨라졌다.")
        else:
            print("달릴 수 없다")
    def fly(self):
        if self.speed > 0:
            print(f"{self.name} : 날고있습니다")
            if self.fly_cooldown < self.fly_cooling:
                self.yspeed = 0.5
                self.flying_time = self.fly_duration
                self.fly_cooling = 0
                self.is_flying = True
        else:
            print("날 수 없다")

class PipePair:
    def __init__(self, x: float, gap_y: int, gap_h: int):
        self.x = x
        self.gap_y = gap_y
        self.gap_h = gap_h
        self.w = 80
        self.color = (0, 0, 0)
        self.scored = False

    def update(self, dt: float, speed: float):
        self.x -= speed * dt

    def offscreen(self) -> bool:
        return self.x + self.w < 0

    def rects(self):
        top_h = max(0, self.gap_y - self.gap_h // 2)
        bot_y = self.gap_y + self.gap_h // 2
        bot_h = max(0, screen_height - bot_y - 30)
        top_rect = pygame.Rect(int(self.x), 0, self.w, int(top_h))
        bot_rect = pygame.Rect(int(self.x), int(bot_y), self.w, int(bot_h))
        return top_rect, bot_rect

    def collides(self, rect: pygame.Rect) -> bool:
        a, b = self.rects()
        return rect.colliderect(a) or rect.colliderect(b)

    def draw(self, screen: pygame.Surface):
        a, b = self.rects()
        pygame.draw.rect(screen, self.color, a)
        pygame.draw.rect(screen, self.color, b)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("새소리")
        self.clock = pygame.time.Clock()
        self.running = True
        self.status = Status.Main
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 64)

        self.birds = self.make_birds()
        self.selected_idx = 0
        self.bird = self.birds[self.selected_idx]

        self.reset()

        self.high_score = self.load_high_score()

    def make_birds(self):
        return [
            Bird('Parrot', self.screen, "parrot.png","안녕하세요",5,3,has_item=True),
            Bird('Sparrow', self.screen, "sparrow.png","짹짹",5,2,has_item=True),
            Bird('Pigeon', self.screen, "pigeon.png","푸드득푸드득",5,4,has_item=True),
            Bird('Chicken', self.screen, "chicken.png","꽉끼오",5,1,has_item_effect=False),
            Bird('RubberDuck', self.screen, "rubberduck.png","꽉",5,0,has_item_effect=False),
        ]

    def reset(self):
        self.bird.x = 120
        self.bird.y = screen_height / 2
        self.bird.yspeed = 0
        self.score = 0
        self.pipes: list[PipePair] = []
        self.spawn_timer = 0.0
        self.spawn_interval = 1.5
        self.pipe_speed = 180
        self.gap = 180
        self.ground_y = screen_height - 30

    def load_high_score(self) -> int:
        path = os.path.join(os.path.dirname(__file__), 'highscore.txt')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return int(f.read().strip() or 0)
        except Exception:
            return 0

    def save_high_score(self):
        path = os.path.join(os.path.dirname(__file__), 'highscore.txt')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if self.status == Status.Main:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.selected_idx = (self.selected_idx - 1) % len(self.birds)
                        self.bird = self.birds[self.selected_idx]
                        self.reset()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.selected_idx = (self.selected_idx + 1) % len(self.birds)
                        self.bird = self.birds[self.selected_idx]
                        self.reset()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.status = Status.Game
                        self.reset()
                elif self.status == Status.Game:
                    if event.key == pygame.K_SPACE:
                        self.bird.bird_running()
                elif self.status == Status.Over:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.status = Status.Game
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        self.status = Status.Main
                        self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.status == Status.Game:
                    if event.button == 1:
                        self.bird.bird_sound()
                    elif event.button == 3:
                        self.bird.fly()
                elif self.status == Status.Main:
                    self.status = Status.Game
                    self.reset()

    def update(self, dt: float):
        if self.status == Status.Main:
            return
        if self.status == Status.Over:
            return

        self.bird.update(dt)

        if self.bird.y < 0:
            self.bird.y = 0
            self.bird.yspeed = 0
        if self.bird.y + 50 > self.ground_y:
            self.bird.y = self.ground_y - 50
            self.game_over()
            return

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            gap_y = random.randint(120, screen_height - 120)
            self.pipes.append(PipePair(screen_width + 60, gap_y, self.gap))

        for p in self.pipes:
            p.update(dt, self.pipe_speed)

        self.pipes = [p for p in self.pipes if not p.offscreen()]

        bird_rect = pygame.Rect(int(self.bird.x), int(self.bird.y), 50, 50)
        for p in self.pipes:
            if p.collides(bird_rect):
                self.game_over()
                return
            if not p.scored and p.x + p.w < self.bird.x:
                p.scored = True
                self.score += 1

    def draw(self):

        self.screen.fill((135, 206, 235))

        if self.status == Status.Main:
            self.draw_menu()
        elif self.status == Status.Game:
            self.draw_game()
        elif self.status == Status.Over:
            self.draw_game()
            self.draw_game_over()

        pygame.display.flip()

    def draw_menu(self):
        title = self.big_font.render("Choose Bird", True, (0, 0, 0))
        self.screen.blit(title, (screen_width // 2 - title.get_width() // 2, 80))

        spacing = 100
        start_x = screen_width // 2 - (len(self.birds) - 1) * spacing // 2
        y = screen_height // 2 - 60
        for i, b in enumerate(self.birds):
            x = start_x + i * spacing
            self.screen.blit(b.img, (x - 25, y))
            name_surf = self.font.render(b.name, True, (0, 0, 0))
            self.screen.blit(name_surf, (x - name_surf.get_width() // 2, y + 70))
            if i == self.selected_idx:
                pygame.draw.rect(self.screen, (255, 0, 0), pygame.Rect(x - 30, y - 5, 60, 60), 3)

        hint = self.font.render("Arrow keys to choose, Enter/click to start", True, (0, 0, 0))
        how_to_play = self.font.render("LeftClick = Jump , RightClick = Fly", True, (0, 0, 0))
        self.screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, screen_height - 120))
        self.screen.blit(how_to_play, (screen_width // 2 - how_to_play.get_width() // 2, screen_height - 150))

    def draw_game(self):
        pygame.draw.rect(self.screen, (222, 184, 135), pygame.Rect(0, screen_height - 30, screen_width, 30))

        for p in self.pipes:
            p.draw(self.screen)

        self.bird.draw(self.screen)

        score_surf = self.big_font.render(str(self.score), True, (255, 255, 255))
        self.screen.blit(score_surf, (screen_width // 2 - score_surf.get_width() // 2, 20))

        hs = self.font.render(f"Best: {self.high_score}", True, (0, 0, 0))
        self.screen.blit(hs, (10, 10))

    def draw_game_over(self):
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        msg = self.big_font.render("Game Over", True, (255, 255, 255))
        self.screen.blit(msg, (screen_width // 2 - msg.get_width() // 2, screen_height // 2 - 120))

        score_line = self.font.render(f"Score: {self.score}   Best: {self.high_score}", True, (255, 255, 255))
        self.screen.blit(score_line, (screen_width // 2 - score_line.get_width() // 2, screen_height // 2 - 50))

        retry = self.font.render("Enter/Space: Retry   Esc: Menu", True, (255, 255, 255))
        self.screen.blit(retry, (screen_width // 2 - retry.get_width() // 2, screen_height // 2 + 10))

    def game_over(self):
        self.status = Status.Over
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = Game()
    game.run()

