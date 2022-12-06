import pygame
import neat
import time
import os
import random

pygame.font.init()

winWidth = 500
winHeight = 800

birdImages = (
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("Flappy_AI/imgs", "bird1.png"))
    ),
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("Flappy_AI/imgs", "bird2.png"))
    ),
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("Flappy_AI/imgs", "bird3.png"))
    ),
)

pipeImage = pygame.transform.scale2x(
    pygame.image.load(os.path.join("Flappy_AI/imgs", "pipe.png"))
)

bgImage = pygame.transform.scale2x(
    pygame.image.load(os.path.join("Flappy_AI/imgs", "background.png"))
)

baseImage = pygame.transform.scale2x(
    pygame.image.load(os.path.join("Flappy_AI/imgs", "base.png"))
)
STAT_FONT = pygame.font.SysFont("comicsans", 40)


class Bird:
    IMGS = birdImages
    MAX_ROTATION = 25
    ROTAT_VELOCITY = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.velocity = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        displacement = self.velocity * self.tick_count + 1.5 * self.tick_count**2

        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTAT_VELOCITY

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center
        )
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VELO = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.pipeTop = pygame.transform.flip(pipeImage, False, True)
        self.pipeBottom = pipeImage

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(40, 450)
        self.top = self.height - self.pipeTop.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VELO

    def draw(self, win):
        win.blit(self.pipeTop, (self.x, self.top))
        win.blit(self.pipeBottom, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.pipeTop)
        bottom_mask = pygame.mask.from_surface(self.pipeBottom)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
        top_point = bird_mask.overlap(top_mask, top_offset)

        if top_point or bottom_point:
            return True

        return False


class Base:
    VELO = 5
    WIDTH = baseImage.get_width()
    IMG = baseImage

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VELO
        self.x2 -= self.VELO

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score):
    win.blit(bgImage, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text_score = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text_score, (winWidth - 10 - text_score.get_width(), 10))

    base.draw(win)

    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    nets = []
    gen = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        gen.append(g)

    base = Base(730)
    pipes = [Pipe(650)]
    win = pygame.display.set_mode((winWidth, winHeight))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if (
                len(pipes) > 1
                and birds[0].x > pipes[0].x + pipes[0].pipeTop.get_width()
            ):
                pipe_ind = 1
        else:
            run = True
            break

        for x, bird in enumerate(birds):
            bird.move()
            gen[x].fitness += 0.1

            output = nets[x].activate(
                (
                    bird.y,
                    abs(bird.y - pipes[pipe_ind].height),
                    abs(bird.y - pipes[pipe_ind].bottom),
                )
            )

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        remov = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    gen[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    gen.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.pipeTop.get_width() < 0:
                remov.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in gen:
                g.fitness += 5
            pipes.append(Pipe(650))

        for r in remov:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y < bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                gen.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score)


def run(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    popul = neat.Population(config)

    popul.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    popul.add_reporter(stats)

    winner = popul.run(main, 50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforwards.txt")
    run(config_path)
