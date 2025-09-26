import pygame
import random
import sys

# Game configuration
WIDTH, HEIGHT = 600, 600
GRID_SIZE = 30
ROWS, COLS = HEIGHT // GRID_SIZE, WIDTH // GRID_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Simple maze layout (1 = wall, 2 = pellet, 0 = path)
MAZE = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,1,2,2,2,1,2,2,2,1,2,2,2,2,2,2,1],
    [1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1],
    [1,2,1,2,2,2,1,2,2,2,1,2,2,2,1,2,1,2,2,1],
    [1,2,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,2,1],
    [1,2,2,2,1,2,2,2,1,2,2,2,1,2,2,2,1,2,2,1],
    [1,1,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,1],
    [1,2,2,2,2,2,1,2,2,2,1,2,2,2,1,2,2,2,2,1],
    [1,2,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,2,1],
    [1,2,2,2,1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]

# Helper function(s)
def find_pos(value):
    for r, row in enumerate(MAZE):
        for c, col in enumerate(row):
            if col == value:
                return r, c
    return 1, 1

# Classes
class Pacman:
    def __init__(self):
        self.row, self.col = 1, 1
        self.lives = 3
        self.score = 0
        self.dx = 0
        self.dy = 0
    def move(self, maze):
        if 0 <= self.row + self.dy < ROWS and 0 <= self.col + self.dx < COLS and maze[self.row+self.dy][self.col+self.dx] != 1:
            self.row += self.dy
            self.col += self.dx
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (self.col * GRID_SIZE + GRID_SIZE//2, self.row * GRID_SIZE + GRID_SIZE//2), GRID_SIZE//2-2)

class Ghost:
    def __init__(self, row, col, color=RED):
        self.row = row
        self.col = col
        self.color = color
        self.dir = random.choice([(1,0),(0,1),(-1,0),(0,-1)])
    def move(self, maze):
        dirs = [(1,0),(0,1),(-1,0),(0,-1)]
        random.shuffle(dirs)
        for d in dirs:
            nr, nc = self.row + d[0], self.col + d[1]
            if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] != 1:
                self.dir = d
                break
        self.row += self.dir[0]
        self.col += self.dir[1]
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.col * GRID_SIZE + GRID_SIZE//2, self.row * GRID_SIZE + GRID_SIZE//2), GRID_SIZE//2-2)

# Setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

pacman = Pacman()
ghosts = [Ghost(5,10)]
pellet_count = sum(row.count(2) for row in MAZE)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                pacman.dy, pacman.dx = -1, 0
            elif event.key == pygame.K_DOWN:
                pacman.dy, pacman.dx = 1, 0
            elif event.key == pygame.K_LEFT:
                pacman.dy, pacman.dx = 0, -1
            elif event.key == pygame.K_RIGHT:
                pacman.dy, pacman.dx = 0, 1
    pacman.move(MAZE)
    # Eat pellet
    if MAZE[pacman.row][pacman.col] == 2:
        pacman.score += 10
        MAZE[pacman.row][pacman.col] = 0
        pellet_count -= 1
    # Move ghosts, check collision
    for ghost in ghosts:
        ghost.move(MAZE)
        if ghost.row == pacman.row and ghost.col == pacman.col:
            pacman.lives -= 1
            pacman.row, pacman.col = 1, 1
            if pacman.lives == 0:
                running = False
    # Draw
    screen.fill(BLACK)
    for r, row in enumerate(MAZE):
        for c, col in enumerate(row):
            x, y = c * GRID_SIZE, r * GRID_SIZE
            if col == 1:
                pygame.draw.rect(screen, BLUE, (x, y, GRID_SIZE, GRID_SIZE))
            elif col == 2:
                pygame.draw.circle(screen, WHITE, (x + GRID_SIZE//2, y + GRID_SIZE//2), 4)
    pacman.draw(screen)
    for ghost in ghosts:
        ghost.draw(screen)
    score_text = font.render(f"Score: {pacman.score}   Lives: {pacman.lives}", True, WHITE)
    screen.blit(score_text, (10, 10))
    if pellet_count == 0:
        win_text = font.render("You Win!", True, YELLOW)
        screen.blit(win_text, (WIDTH//2-60, HEIGHT//2))
        pygame.display.flip()
        pygame.time.wait(3000)
        running = False
    pygame.display.flip()
    clock.tick(10)

pygame.quit()
sys.exit()
