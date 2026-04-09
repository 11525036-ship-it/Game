import pygame
import random
import sys
import time
from collections import deque

pygame.init()

WIDTH, HEIGHT = 720, 820
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MINOTAUR MAZE HUNT V8")

FONT_BIG = pygame.font.SysFont("arial", 48)
FONT_MED = pygame.font.SysFont("arial", 28)
FONT_SMALL = pygame.font.SysFont("arial", 20)

WHITE = (255, 255, 255)
GREEN = (40, 220, 80)
RED = (220, 70, 70)
YELLOW = (255, 220, 60)
BG = (15, 15, 15)
BLUE = (70, 170, 255)
PURPLE = (180, 80, 255)

LEVELS = {
    "EASY": { "cell": 38, "speed": 3.5, "hear": 10, "prediction_radius": 2}
}

def generate_maze(cols, rows):
    walls = [[{'n': True, 's': True, 'e': True, 'w': True} for _ in range(cols)] for _ in range(rows)]
    visited = [[False] * cols for _ in range(rows)]
    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        x, y = stack[-1]
        dirs = []
        if y > 0 and not visited[y-1][x]: dirs.append((x, y-1, 'n', 's'))
        if y < rows-1 and not visited[y+1][x]: dirs.append((x, y+1, 's', 'n'))
        if x > 0 and not visited[y][x-1]: dirs.append((x-1, y, 'w', 'e'))
        if x < cols-1 and not visited[y][x+1]: dirs.append((x+1, y, 'e', 'w'))
        if dirs:
            nx, ny, d, od = random.choice(dirs)
            walls[y][x][d] = False
            walls[ny][nx][od] = False
            visited[ny][nx] = True
            stack.append((nx, ny))
        else:
            stack.pop()
            
    for y in range(1, rows - 1):
        for x in range(1, cols - 1):
            if random.random() < 0.24: 
                direction = random.choice(['n', 's', 'e', 'w'])
                if direction == 'n' and walls[y][x]['n']:
                    walls[y][x]['n'] = False
                    walls[y-1][x]['s'] = False
                elif direction == 's' and walls[y][x]['s']:
                    walls[y][x]['s'] = False
                    walls[y+1][x]['n'] = False
                elif direction == 'e' and walls[y][x]['e']:
                    walls[y][x]['e'] = False
                    walls[y][x+1]['w'] = False
                elif direction == 'w' and walls[y][x]['w']:
                    walls[y][x]['w'] = False
                    walls[y][x-1]['e'] = False

    return walls

def neighbors_of(walls, x, y):
    result = []
    rows, cols = len(walls), len(walls[0])
    if y > 0 and not walls[y][x]['n']: result.append((x, y-1))
    if y < rows-1 and not walls[y][x]['s']: result.append((x, y+1))
    if x > 0 and not walls[y][x]['w']: result.append((x-1, y))
    if x < cols-1 and not walls[y][x]['e']: result.append((x+1, y))
    return result


def bfs_next_step(walls, start, goal):
    queue = deque([start])
    parent = {start: None}
    while queue:
        cur = queue.popleft()
        if cur == goal: break
        for nxt in neighbors_of(walls, cur[0], cur[1]):
            if nxt not in parent:
                parent[nxt] = cur
                queue.append(nxt)
    if goal not in parent: return start
    cur = goal
    while parent[cur] != start and parent[cur] is not None:
        cur = parent[cur]
    return cur


def can_move(walls, x, y, dx, dy):
    cell = walls[y][x]
    if dx == 1:  return not cell['e']
    if dx == -1: return not cell['w']
    if dy == 1:  return not cell['s']
    if dy == -1: return not cell['n']
    return False


def random_spawn_far(cols, rows, player, exit_pos):
    while True:
        x, y = random.randint(0, cols-1), random.randint(0, rows-1)
        if abs(x-player[0])+abs(y-player[1]) >= max(20, cols//3) and \
           abs(x-exit_pos[0])+abs(y-exit_pos[1]) >= max(6, cols//4):
            return x, y


def draw_maze(screen, walls, cs, ox, oy):
    wall = max(2, cs // 8)
    for y in range(len(walls)):
        for x in range(len(walls[0])):
            px, py = ox + x*cs, oy + y*cs
            cell = walls[y][x]
            pygame.draw.rect(screen, (20, 60, 20), (px, py, cs, cs))
            if cell['n']: pygame.draw.rect(screen, GREEN, (px, py, cs, wall))
            if cell['s']: pygame.draw.rect(screen, GREEN, (px, py+cs-wall, cs, wall))
            if cell['w']: pygame.draw.rect(screen, GREEN, (px, py, wall, cs))
            if cell['e']: pygame.draw.rect(screen, GREEN, (px+cs-wall, py, wall, cs))



def show_message(text, color):
    screen.fill(BG)
    msg = FONT_BIG.render(text, True, color)
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))
    pygame.display.flip()
    pygame.time.delay(2000)


class Minotaur:
    def __init__(self, x, y, cfg, exit_pos):
        self.x, self.y = x, y
        self.exit_pos = exit_pos
        self.speed = cfg["speed"]   
        self.hear = cfg["hear"]
        self.prediction_radius = cfg["prediction_radius"]
        self.hint_target = (x, y)
        self.last_hint_update = 0

    def line_of_sight(self, player):
        return player[0] == self.x or player[1] == self.y

    def update_hint(self, player, cols, rows):
        px, py = player
        hx = max(0, min(cols-1, px + random.randint(-self.prediction_radius, self.prediction_radius)))
        hy = max(0, min(rows-1, py + random.randint(-self.prediction_radius, self.prediction_radius)))
        self.hint_target = (hx, hy)

    def update(self, walls, player):
        now = time.time()
        px, py = player
        cols, rows = len(walls[0]), len(walls)
        
        if now - self.last_hint_update >= 5:
            self.update_hint(player, cols, rows)
            self.last_hint_update = now

        seen = self.line_of_sight(player) or abs(px-self.x)+abs(py-self.y) <= self.hear
        
        if seen:
            target = player  
        else:
            target = self.hint_target 

        walk_next = bfs_next_step(walls, (self.x, self.y), target)
        
        if walk_next != (self.x, self.y):
            self.x, self.y = walk_next


def game():
    cfg = LEVELS['EASY']
    cols = random.randint(20, 40)
    rows = random.randint(20, 40)
    cs = min(WIDTH // cols, (HEIGHT - 120) // rows)
    walls = generate_maze(cols, rows)
    ox = (WIDTH - cols*cs) // 2
    oy = 100
    player = [0, 0]
    exit_pos = (cols-1, rows-1)
    mx, my = random_spawn_far(cols, rows, player, exit_pos)
    minotaur = Minotaur(mx, my, cfg, exit_pos)
    start_time = time.time()
    last_ai = 0
    while True:
        screen.fill(BG)
        elapsed = time.time() - start_time
        draw_maze(screen, walls, cs, ox, oy)
        pygame.draw.rect(screen, RED, (ox+(cols-1)*cs+2, oy+(rows-1)*cs+2, cs-4, cs-4))
        pygame.draw.circle(screen, BLUE, (ox+player[0]*cs+cs//2, oy+player[1]*cs+cs//2), cs//2-3)
        pygame.draw.circle(screen, PURPLE, (ox+minotaur.x*cs+cs//2, oy+minotaur.y*cs+cs//2), cs//2-3)
        if time.time() - last_ai > 1/minotaur.speed:
            minotaur.update(walls, tuple(player))
            last_ai = time.time()
        if player[0] == minotaur.x and player[1] == minotaur.y:
            show_message("YOU WERE CAUGHT!", RED)
            return
        if player == [cols-1, rows-1]:
            show_message("CONGRATULATIONS!", GREEN)
            return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return
                dx, dy = 0, 0
                if event.key in (pygame.K_w, pygame.K_UP):    dy = -1
                elif event.key in (pygame.K_s, pygame.K_DOWN): dy = 1
                elif event.key in (pygame.K_a, pygame.K_LEFT): dx = -1
                elif event.key in (pygame.K_d, pygame.K_RIGHT): dx = 1
                if can_move(walls, player[0], player[1], dx, dy):
                    player[0] += dx; player[1] += dy
        pygame.display.flip()

def main():
    while True:
        game() 

if __name__ == "__main__":
    main()