import pygame
import random
import sys
import numpy as np

# ---------- Configuration ----------
TILE = 28
FPS = 60
PLAYER_SPEED = 2.5
GHOST_SPEED = 2.0
LIVES = 2
TURN_TOLERANCE = 6

MAZE_MAP = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.$..#.#   #.##.#   #.#..$.#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.#####.##.#####.######",
    "     #.##          ##.#     ",
    "     #.##.###--###.##.#     ",
    "######.##.#$$$$$$#.#.##.######",
    "      .   #$$$$$$#   .      ",
    "######.##.#$$$$$$#.#.##.######",
    "     #.##.########.##.#     ",
    "     #.##..........##.#     ",
    "     #.##.########.##.#     ",
    "######.##.########.##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.$..##..............##..$.#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........P...............#",
    "############################"
]

MAZE_MAP = [row.ljust(len(MAZE_MAP[0])) for row in MAZE_MAP]

# ---------- Helper functions ----------
def load_maze():
    walls = []
    pellets = []
    player_pos = None
    ghost_positions = []
    rows = len(MAZE_MAP)
    cols = len(MAZE_MAP[0])
    for r in range(rows):
        for c in range(cols):
            ch = MAZE_MAP[r][c]
            x = c * TILE
            y = r * TILE
            if ch == '#':
                walls.append(pygame.Rect(x, y, TILE, TILE))
            elif ch in ['.', '$']:
                pellets.append((x + TILE // 2, y + TILE // 2))
            elif ch == 'P':
                player_pos = (x + TILE // 2, y + TILE // 2)
            elif ch == 'G':
                ghost_positions.append((x + TILE // 2, y + TILE // 2))
    if player_pos is None:
        player_pos = (14 * TILE + TILE // 2, 23 * TILE + TILE // 2)
    if not ghost_positions:
        ghost_positions = [
            (13 * TILE + TILE // 2, 14 * TILE + TILE // 2),
            (14 * TILE + TILE // 2, 14 * TILE + TILE // 2),
            (15 * TILE + TILE // 2, 14 * TILE + TILE // 2),
        ]
    return walls, pellets, player_pos, ghost_positions

def rect_from_center(x, y, size):
    return pygame.Rect(int(x - size // 2), int(y - size // 2), size, size)

def is_colliding_walls(rect, walls):
    for w in walls:
        if rect.colliderect(w):
            return True
    return False

# ---------- Image circle crop ----------
def circle_crop(image, size):
    # Scale image to desired size
    image = pygame.transform.scale(image, size).convert_alpha()

    # Create circular mask
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255),
                       (size[0]//2, size[1]//2), size[0]//2)

    # Apply mask
    result = pygame.Surface(size, pygame.SRCALPHA)
    result.blit(image, (0, 0))
    result.blit(mask, (0, 0), None, pygame.BLEND_RGBA_MULT)

    return result

# ---------- Sound generation ----------
def make_sound(frequency, duration=0.1, volume=0.5):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(frequency * t * 2 * np.pi)
    audio = np.array(wave * 32767, dtype=np.int16)

    stereo_audio = np.column_stack((audio, audio))  # stereo
    sound = pygame.sndarray.make_sound(stereo_audio)
    sound.set_volume(volume)
    return sound

pellet_sound = None
death_sound = None
win_sound = None

def init_sounds():
    global pellet_sound, death_sound, win_sound
    pellet_sound = make_sound(800, 0.05, 0.3)
    death_sound = make_sound(200, 0.5, 0.6)
    win_sound = make_sound(1000, 0.3, 0.5)

# ---------- Game objects ----------
class Player:
    def __init__(self, x, y, img=None):
        self.x = x
        self.y = y
        self.radius = TILE // 2 - 2
        self.dir = (0, 0)
        self.next_dir = (0, 0)
        self.speed = PLAYER_SPEED
        self.img = img

    def update(self, walls, keys):
        if keys[pygame.K_UP]:
            self.next_dir = (0, -1)
        elif keys[pygame.K_DOWN]:
            self.next_dir = (0, 1)
        elif keys[pygame.K_LEFT]:
            self.next_dir = (-1, 0)
        elif keys[pygame.K_RIGHT]:
            self.next_dir = (1, 0)

        center_x = self.x % TILE
        center_y = self.y % TILE
        tolerance = max(TURN_TOLERANCE, TILE / 4)
        can_turn = abs(center_x - TILE/2) < tolerance and abs(center_y - TILE/2) < tolerance

        if can_turn:
            new_x = self.x + self.next_dir[0] * self.speed
            new_y = self.y + self.next_dir[1] * self.speed
            rect_try = rect_from_center(new_x, new_y, self.radius * 2 - 2)
            if not is_colliding_walls(rect_try, walls):
                self.dir = self.next_dir

        new_x = self.x + self.dir[0] * self.speed
        new_y = self.y + self.dir[1] * self.speed

        if new_x < 0:
            new_x = (len(MAZE_MAP[0]) * TILE) - self.radius
        elif new_x > (len(MAZE_MAP[0]) * TILE):
            new_x = self.radius

        new_y = max(self.radius, min(new_y, (len(MAZE_MAP) * TILE) - self.radius))

        rect_try = rect_from_center(new_x, new_y, self.radius * 2 - 2)
        if not is_colliding_walls(rect_try, walls):
            self.x, self.y = new_x, new_y

    def draw(self, screen):
        if self.img:
            screen.blit(self.img, (int(self.x - TILE//2), int(self.y - TILE//2)))
        else:
            pygame.draw.circle(screen, (255, 230, 0), (int(self.x), int(self.y)), self.radius)

class Ghost:
    def __init__(self, x, y, idx=0, img=None):
        self.x = x
        self.y = y
        self.radius = TILE // 2 - 3
        self.speed = GHOST_SPEED
        self.dir = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
        self.idx = idx
        self.img = img

    def update(self, walls):
        new_x = self.x + self.dir[0] * self.speed
        new_y = self.y + self.dir[1] * self.speed
        rect_try = rect_from_center(new_x, new_y, self.radius * 2 - 2)
        if not is_colliding_walls(rect_try, walls):
            self.x = new_x
            self.y = new_y

            if self.x < 0 :
                self.x = (len(MAZE_MAP[0]) * TILE) - self.radius
            elif self.x > (len(MAZE_MAP[0]) * TILE):
                self.x = self.radius

        else:
            self.choose_new_dir(walls)

        if random.random() < 0.02:
            self.choose_new_dir(walls)

    def choose_new_dir(self, walls):
        options = []
        for d in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx = self.x + d[0] * self.speed * 2
            ny = self.y + d[1] * self.speed * 2
            if not is_colliding_walls(rect_from_center(nx, ny, self.radius * 2 - 2), walls):
                options.append(d)
        if options:
            self.dir = random.choice(options)

    def draw(self, screen):
        if self.img:
            screen.blit(self.img, (int(self.x - TILE//2), int(self.y - TILE//2)))
        else:
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)

# ---------- Code Entry Screen ----------
def code_entry_screen(screen):
    font = pygame.font.SysFont(None, 36)
    input_text = ""
    clock = pygame.time.Clock()
    error_message = ""
    error_timer = 0

    while True:
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text.lower() in ["nagasai", "rialo"]:
                        return True
                    else:
                        error_message = "Wrong Code! Try Again."
                        error_timer = pygame.time.get_ticks()
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        prompt_text = font.render("Enter Code:", True, (255, 255, 255))
        code_text = font.render(input_text, True, (255, 255, 0))
        screen.blit(prompt_text, (50, 50))
        pygame.draw.rect(screen, (255, 255, 255), (50, 90, 300, 40), 2)
        screen.blit(code_text, (55, 95))

        if error_message and pygame.time.get_ticks() - error_timer < 2000:
            error_text = font.render(error_message, True, (255, 0, 0))
            screen.blit(error_text, (50, 150))

        pygame.display.flip()
        clock.tick(30)

# ---------- Main game ----------
def main():
    pygame.init()
    init_sounds()

    walls, pellets, player_start, ghost_starts = load_maze()
    rows = len(MAZE_MAP)
    cols = len(MAZE_MAP[0])
    WIDTH = cols * TILE
    HEIGHT = rows * TILE

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mini Pac-Man")

    coin_img = pygame.image.load("rialo.png").convert_alpha()
    coin_img = pygame.transform.scale(coin_img, (TILE//2, TILE//2))

    # Load ghost images with circular crop
    ghost_imgs = [
        circle_crop(pygame.image.load("g1.png").convert_alpha(), (TILE, TILE)),
        circle_crop(pygame.image.load("g2.png").convert_alpha(), (TILE, TILE)),
        circle_crop(pygame.image.load("g3.png").convert_alpha(), (TILE, TILE)),
    ]

    # Load player image with circular crop
    player_img = circle_crop(pygame.image.load("player.png").convert_alpha(), (TILE, TILE))

    code_entry_screen(screen)

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    player = Player(*player_start, img=player_img)
    ghosts = [Ghost(x, y, idx=i, img=ghost_imgs[i % len(ghost_imgs)]) for i, (x, y) in enumerate(ghost_starts)]
    score = 0
    lives = LIVES

    pellet_set = set(pellets)
    pellet_radius = 4

    running = True
    game_over = False
    win = False

    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game_over and event.key == pygame.K_RETURN:
                    main()
                    return

        keys = pygame.key.get_pressed()
        if not game_over:
            player.update(walls, keys)
            for ghost in ghosts:
                ghost.update(walls)

            player_rect = rect_from_center(player.x, player.y, player.radius * 2 - 2)

            # Eat pellet
            for pellet in list(pellet_set):
                if pygame.Rect(pellet[0]-pellet_radius, pellet[1]-pellet_radius, pellet_radius*2, pellet_radius*2).colliderect(player_rect):
                    pellet_set.remove(pellet)
                    score += 10
                    pellet_sound.play()

            # Collide with ghost
            for ghost in ghosts:
                if rect_from_center(ghost.x, ghost.y, ghost.radius*2-2).colliderect(player_rect):
                    lives -= 1
                    death_sound.play()
                    if lives <= 0:
                        game_over = True
                    else:
                        walls, pellets, player_start, ghost_starts = load_maze()
                        player = Player(*player_start, img=player_img)
                        ghosts = [Ghost(x, y, idx=i, img=ghost_imgs[i % len(ghost_imgs)]) for i, (x, y) in enumerate(ghost_starts)]
                    break

            # Win condition
            if not pellet_set:
                win = True
                win_sound.play()
                game_over = True

        screen.fill((0,0,0))
        for w in walls:
            pygame.draw.rect(screen, (0,0,255), w)

        for pellet in pellet_set:
            screen.blit(coin_img, (pellet[0]-TILE//4, pellet[1]-TILE//4))

        player.draw(screen)
        for ghost in ghosts:
            ghost.draw(screen)

        score_text = font.render(f"Score: {score}", True, (255,255,255))
        lives_text = font.render(f"Lives: {lives}", True, (255,255,255))
        screen.blit(score_text, (10, HEIGHT-30))
        screen.blit(lives_text, (WIDTH-100, HEIGHT-30))

        if game_over:
            if win:
                # GRIALO Winning animation
                animation_frames = 60
                colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (255, 0, 255)]
                big_font = pygame.font.SysFont(None, 80)

                for frame in range(animation_frames):
                    screen.fill((0, 0, 0))
                    for w in walls:
                        pygame.draw.rect(screen, (0, 0, 255), w)

                    for pellet in pellet_set:
                        screen.blit(coin_img, (pellet[0] - TILE // 4, pellet[1] - TILE // 4))

                    # Draw player and ghosts disappearing
                    if frame < animation_frames // 2:
                        player.draw(screen)
                        for ghost in ghosts:
                            ghost.draw(screen)

                    # Animate GRIALO text
                    scale = 1 + (frame / animation_frames) * 2   # grow effect
                    text_size = int(80 * scale)
                    dynamic_font = pygame.font.SysFont(None, text_size, bold=True)
                    color = colors[frame % len(colors)]
                    win_text = dynamic_font.render("GRIALO", True, color)

                    text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                    screen.blit(win_text, text_rect)

                    pygame.display.flip()
                    pygame.time.delay(30)  # controls speed of animation
            else:
                game_text = font.render("GAME OVER Press Enter to Restart", True, (255, 0, 0))
                screen.blit(game_text, (WIDTH // 4, HEIGHT // 2))


        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
