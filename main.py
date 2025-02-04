import pygame
import random
import sys
import heapq

# Konfigürasyon sabitleri (ekran biraz büyütüldü)
CELL_SIZE = 20          # Her hücrenin boyutu (piksel)
GRID_WIDTH = 40         # Yatay hücre sayısı (önceki 30'dan arttırıldı)
GRID_HEIGHT = 25        # Dikey hücre sayısı (önceki 20'den arttırıldı)
WINDOW_WIDTH = CELL_SIZE * GRID_WIDTH
WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT
FPS = 10
NUM_SNAKES = 2          # Sadece iki yılan kullanılacak

# Renkler
BLACK = (0, 0, 0)
FOOD_COLOR = (255, 0, 0)
SNAKE_COLORS = [(0, 255, 0), (0, 0, 255)]
OBSTACLE_COLOR = (128, 128, 128)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 149, 237)
TEXT_COLOR = (255, 255, 255)

# Hareket yönleri (dx, dy)
DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0)
}

# 180° dönüşleri engellemek için ters yön eşlemesi
OPPOSITE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(start, goal, obstacles):
    """
    A* algoritması: start'tan goal'a en kısa yolu bulur.
    obstacles: (x, y) pozisyonlarını içeren küme.
    """
    obstacles = set(obstacles)
    obstacles.discard(start)
    
    open_set = []
    heapq.heappush(open_set, (manhattan(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        f, current_g, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        for d in DIRECTIONS.values():
            neighbor = (current[0] + d[0], current[1] + d[1])
            if (neighbor in obstacles) and (neighbor != goal):
                continue
            if neighbor[0] < 0 or neighbor[0] >= GRID_WIDTH or neighbor[1] < 0 or neighbor[1] >= GRID_HEIGHT:
                continue

            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + manhattan(neighbor, goal)
                heapq.heappush(open_set, (f_score, tentative_g, neighbor))
    return None

def dijkstra(start, goal, obstacles):
    """
    Dijkstra algoritması: kenar maliyeti 1 olarak kabul edilir.
    """
    obstacles = set(obstacles)
    obstacles.discard(start)
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    dist = {start: 0}
    
    while open_set:
        current_dist, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        for d in DIRECTIONS.values():
            neighbor = (current[0] + d[0], current[1] + d[1])
            if neighbor in obstacles and neighbor != goal:
                continue
            if neighbor[0] < 0 or neighbor[0] >= GRID_WIDTH or neighbor[1] < 0 or neighbor[1] >= GRID_HEIGHT:
                continue
            new_dist = dist[current] + 1
            if new_dist < dist.get(neighbor, float('inf')):
                came_from[neighbor] = current
                dist[neighbor] = new_dist
                heapq.heappush(open_set, (new_dist, neighbor))
    return None

def get_random_food_position(snakes, obstacles):
    """
    Yılanların ve engellerin kaplamadığı rastgele bir yiyecek pozisyonu üretir.
    """
    while True:
        pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        conflict = False
        for snake in snakes:
            if pos in snake.positions:
                conflict = True
                break
        if pos in obstacles:
            conflict = True
        if not conflict:
            return pos

def generate_obstacles():
    """
    Sabit konumlu engeller oluşturur.
    Örneğin, ekranın ortasında yatay bir duvar ve sol tarafta dikey bir duvar.
    """
    obstacles = []
    # Ortada yatay duvar (x:10-30, y:12)
    for x in range(10, 31):
        obstacles.append((x, 12))
    # Sol tarafta dikey duvar (x:5, y:5-14)
    for y in range(5, 15):
        obstacles.append((5, y))
    return obstacles

# Global engeller (oyun başlangıcında oluşturuluyor)
OBSTACLES = generate_obstacles()

class Snake:
    def __init__(self, color, start_pos, start_direction, algorithm="astar"):
        self.color = color
        self.positions = [start_pos]  # Yılanın başı
        self.direction = start_direction  # "UP", "DOWN", "LEFT", "RIGHT"
        self.alive = True
        self.score = 0
        self.algorithm = algorithm  # "astar" veya "dijkstra"

    def head(self):
        return self.positions[0]

    def move(self, food_pos, snakes):
        if not self.alive:
            return
        best_direction = self.choose_direction(food_pos, snakes)
        if best_direction:
            self.direction = best_direction
        dx, dy = DIRECTIONS[self.direction]
        new_head = (self.head()[0] + dx, self.head()[1] + dy)
        self.positions.insert(0, new_head)

    def choose_direction(self, food_pos, snakes):
        head_x, head_y = self.head()
        food_x, food_y = food_pos

        # Engel olarak: diğer yılanların pozisyonları ve OBSTACLES birleşimi.
        obstacles = set(OBSTACLES)
        for s in snakes:
            obstacles.update(s.positions)
        
        # Seçilen algoritmaya göre yol hesapla.
        if self.algorithm == "astar":
            path = astar(self.head(), food_pos, obstacles)
        else:
            path = dijkstra(self.head(), food_pos, obstacles)
            
        if path is not None and len(path) >= 2:
            next_step = path[1]
            dx = next_step[0] - head_x
            dy = next_step[1] - head_y
            if dx == 1:
                return "RIGHT"
            elif dx == -1:
                return "LEFT"
            elif dy == 1:
                return "DOWN"
            elif dy == -1:
                return "UP"
        
        # A* veya Dijkstra başarısız olursa: yemeğin hizasında dönüş kontrolleri.
        if self.direction in ["LEFT", "RIGHT"] and head_x == food_x:
            if head_y < food_y:
                candidate = "DOWN"
                if candidate != OPPOSITE[self.direction] and self.is_safe((head_x, head_y + 1), snakes):
                    return candidate
            elif head_y > food_y:
                candidate = "UP"
                if candidate != OPPOSITE[self.direction] and self.is_safe((head_x, head_y - 1), snakes):
                    return candidate

        if self.direction in ["UP", "DOWN"] and head_y == food_y:
            if head_x < food_x:
                candidate = "RIGHT"
                if candidate != OPPOSITE[self.direction] and self.is_safe((head_x + 1, head_y), snakes):
                    return candidate
            elif head_x > food_x:
                candidate = "LEFT"
                if candidate != OPPOSITE[self.direction] and self.is_safe((head_x - 1, head_y), snakes):
                    return candidate

        # Normal strateji: mevcut yönde devam edilebiliyorsa.
        def safe(d):
            dx, dy = DIRECTIONS[d]
            new_pos = (head_x + dx, head_y + dy)
            return self.is_safe(new_pos, snakes)
        if safe(self.direction):
            return self.direction

        relative = {
            "UP":    {"LEFT": "LEFT", "RIGHT": "RIGHT"},
            "DOWN":  {"LEFT": "RIGHT", "RIGHT": "LEFT"},
            "LEFT":  {"LEFT": "DOWN", "RIGHT": "UP"},
            "RIGHT": {"LEFT": "UP", "RIGHT": "DOWN"}
        }
        for turn in ["LEFT", "RIGHT"]:
            candidate = relative[self.direction][turn]
            if safe(candidate):
                return candidate

        safe_moves = [d for d in DIRECTIONS.keys() if d != OPPOSITE[self.direction] and safe(d)]
        if safe_moves:
            def manhattan_distance(d):
                dx, dy = DIRECTIONS[d]
                new_pos = (head_x + dx, head_y + dy)
                return abs(new_pos[0] - food_x) + abs(new_pos[1] - food_y)
            return min(safe_moves, key=manhattan_distance)

        return self.direction

    def is_safe(self, pos, snakes):
        x, y = pos
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            return False
        if pos in OBSTACLES:
            return False
        for snake in snakes:
            if pos in snake.positions:
                return False
        return True

    def check_collisions(self, snakes):
        head = self.head()
        x, y = head
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            self.alive = False
            return
        if head in self.positions[1:]:
            self.alive = False
            return
        for snake in snakes:
            if snake is not self and head in snake.positions:
                self.alive = False
                return

    def trim_tail(self, ate_food):
        if not ate_food:
            self.positions.pop()

def draw_snake(surface, snake):
    for pos in snake.positions:
        rect = pygame.Rect(pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, snake.color, rect)

def draw_food(surface, food_pos):
    rect = pygame.Rect(food_pos[0] * CELL_SIZE, food_pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, FOOD_COLOR, rect)

def draw_obstacles(surface, obstacles):
    for pos in obstacles:
        rect = pygame.Rect(pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, OBSTACLE_COLOR, rect)

def game_over_screen(screen, snakes):
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 36)
    scores_text = ""
    for idx, snake in enumerate(snakes):
        scores_text += f"Yılan {idx+1}: {snake.score}    "
    
    game_over_text = font.render("Oyun Bitti!", True, TEXT_COLOR)
    score_render = small_font.render(scores_text, True, TEXT_COLOR)
    question_text = small_font.render("Tekrar oynamak ister misiniz?", True, TEXT_COLOR)
    
    button_text = small_font.render("Tekrar Oyna", True, TEXT_COLOR)
    button_width, button_height = 200, 50
    button_rect = pygame.Rect((WINDOW_WIDTH - button_width) // 2, WINDOW_HEIGHT // 2 + 50, button_width, button_height)
    
    while True:
        screen.fill(BLACK)
        screen.blit(game_over_text, ((WINDOW_WIDTH - game_over_text.get_width()) // 2, WINDOW_HEIGHT // 2 - 150))
        screen.blit(score_render, ((WINDOW_WIDTH - score_render.get_width()) // 2, WINDOW_HEIGHT // 2 - 80))
        screen.blit(question_text, ((WINDOW_WIDTH - question_text.get_width()) // 2, WINDOW_HEIGHT // 2 - 30))
        
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER
        else:
            color = BUTTON_COLOR
        pygame.draw.rect(screen, color, button_rect)
        screen.blit(button_text, ((WINDOW_WIDTH - button_text.get_width()) // 2, WINDOW_HEIGHT // 2 + 60))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    return

def run_game(screen, clock):
    snakes = []
    # İlk yılan A* algoritması, ikinci yılan Dijkstra kullanacak.
    initial_positions = [(5, 5), (GRID_WIDTH - 6, GRID_HEIGHT - 6)]
    initial_directions = ["RIGHT", "LEFT"]
    algorithms = ["astar", "dijkstra"]
    for i in range(NUM_SNAKES):
        snakes.append(Snake(SNAKE_COLORS[i % len(SNAKE_COLORS)],
                            initial_positions[i],
                            initial_directions[i],
                            algorithm=algorithms[i]))
    
    food_pos = get_random_food_position(snakes, OBSTACLES)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        for snake in snakes:
            if snake.alive:
                snake.move(food_pos, snakes)
                
        for snake in snakes:
            if not snake.alive:
                continue
            ate_food = (snake.head() == food_pos)
            if ate_food:
                snake.score += 1
                food_pos = get_random_food_position(snakes, OBSTACLES)
            snake.trim_tail(ate_food)
            
        for snake in snakes:
            if snake.alive:
                snake.check_collisions(snakes)
                
        screen.fill(BLACK)
        draw_food(screen, food_pos)
        draw_obstacles(screen, OBSTACLES)
        for snake in snakes:
            if snake.alive:
                draw_snake(screen, snake)
        pygame.display.flip()
        
        alive_snakes = [s for s in snakes if s.alive]
        if len(alive_snakes) <= 1:
            running = False
            
    return snakes

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Otonom Yılan Yarışması (A* ve Dijkstra, Engeller)")
    clock = pygame.time.Clock()
    
    while True:
        snakes = run_game(screen, clock)
        game_over_screen(screen, snakes)

if __name__ == "__main__":
    main()
