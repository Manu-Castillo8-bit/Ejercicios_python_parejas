import sys
import random
import os
import pygame

# -------------------------------------------------------------
# CONSTANTES Y CONFIGURACIÓN GENERAL
# -------------------------------------------------------------
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 650
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - 50) // GRID_SIZE
HEADER_HEIGHT = 50

# Paleta de Colores (Estilo Neón / Cyberpunk)
COLOR_BG = (10, 10, 20)
COLOR_GRID = (22, 22, 38)
COLOR_HEADER = (16, 16, 28)
COLOR_FOOD = (255, 46, 151)
COLOR_TEXT = (233, 233, 246)
COLOR_ACCENT = (255, 179, 0)
COLOR_OBSTACLE = (255, 50, 50)

# NUEVO - Paleta de colores para personalizar la serpiente
SNAKE_PALETTE = [
    (0, 240, 255),   # Cian Neón
    (57, 255, 136),  # Verde Neón
    (255, 46, 151),  # Magenta Neón
    (255, 179, 0),   # Ámbar
    (157, 0, 255),   # Púrpura Neón
    (255, 255, 255), # Blanco Puro
    (255, 50, 50)    # Rojo Neón
]

# Direcciones
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Estados del Juego
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAME_OVER = 3


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [
            (GRID_WIDTH // 2, GRID_HEIGHT // 2),
            (GRID_WIDTH // 2 - 1, GRID_HEIGHT // 2),
            (GRID_WIDTH // 2 - 2, GRID_HEIGHT // 2)
        ]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.grow = False

    def change_direction(self, new_dir):
        if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
            self.next_direction = new_dir

    def update(self):
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dir_x, dir_y = self.direction
        new_head = (head_x + dir_x, head_y + dir_y)

        self.body.insert(0, new_head)
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False

    def check_wall_collision(self):
        head_x, head_y = self.body[0]
        return not (0 <= head_x < GRID_WIDTH and 0 <= head_y < GRID_HEIGHT)

    def check_self_collision(self):
        return self.body[0] in self.body[1:]


class Food:
    def __init__(self):
        self.position = (0, 0)

    def spawn(self, snake_body, obstacles):
        while True:
            new_pos = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
            if new_pos not in snake_body and new_pos not in obstacles:
                self.position = new_pos
                break


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Misión 3: Snake Game · INDEL 3DS")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_ui = pygame.font.SysFont("Consolas", 18, bold=True)
        self.font_title = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_sub = pygame.font.SysFont("Consolas", 16)
        self.font_mini = pygame.font.SysFont("Consolas", 14) # NUEVO - Fuente pequeña

        self.snake = Snake()
        self.food = Food()
        self.obstacles = []
        self.food.spawn(self.snake.body, self.obstacles)

        self.score = 0
        self.high_score = self.load_high_score()
        self.state = STATE_MENU
        self.base_speed = 10

        # NUEVO - Variables de personalización
        self.idx_head_color = 0 # Inicia en Cian
        self.idx_body_color = 1 # Inicia en Verde
        self.color_head = SNAKE_PALETTE[self.idx_head_color]
        self.color_body = SNAKE_PALETTE[self.idx_body_color]

    def load_high_score(self):
        if os.path.exists("highscore.txt"):
            try:
                with open("highscore.txt", "r") as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def save_high_score(self):
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except Exception as e:
            print(f"No se pudo guardar el récord: {e}")

    def spawn_obstacle(self):
        while True:
            new_pos = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
            if (new_pos not in self.snake.body and 
                new_pos != self.food.position and 
                new_pos not in self.obstacles):
                self.obstacles.append(new_pos)
                break

    def reset_game(self):
        self.snake.reset()
        self.obstacles.clear()
        self.food.spawn(self.snake.body, self.obstacles)
        self.score = 0
        self.state = STATE_PLAYING

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_high_score()
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if self.state == STATE_MENU:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.reset_game()
                    
                    # NUEVO - Controles de personalización en el menú
                    elif event.key == pygame.K_LEFT:
                        self.idx_head_color = (self.idx_head_color - 1) % len(SNAKE_PALETTE)
                        self.color_head = SNAKE_PALETTE[self.idx_head_color]
                    elif event.key == pygame.K_RIGHT:
                        self.idx_head_color = (self.idx_head_color + 1) % len(SNAKE_PALETTE)
                        self.color_head = SNAKE_PALETTE[self.idx_head_color]
                    elif event.key == pygame.K_UP:
                        self.idx_body_color = (self.idx_body_color + 1) % len(SNAKE_PALETTE)
                        self.color_body = SNAKE_PALETTE[self.idx_body_color]
                    elif event.key == pygame.K_DOWN:
                        self.idx_body_color = (self.idx_body_color - 1) % len(SNAKE_PALETTE)
                        self.color_body = SNAKE_PALETTE[self.idx_body_color]

                elif self.state == STATE_PLAYING:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.snake.change_direction(UP)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.snake.change_direction(DOWN)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.snake.change_direction(LEFT)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.snake.change_direction(RIGHT)
                    elif event.key == pygame.K_p:
                        self.state = STATE_PAUSED

                elif self.state == STATE_PAUSED:
                    if event.key == pygame.K_p:
                        self.state = STATE_PLAYING

                elif self.state == STATE_GAME_OVER:
                    if event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                        self.reset_game()

    def update(self):
        if self.state != STATE_PLAYING:
            return

        self.snake.update()

        if (self.snake.check_wall_collision() or 
            self.snake.check_self_collision() or 
            self.snake.body[0] in self.obstacles):
            
            self.state = STATE_GAME_OVER
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            return

        if self.snake.body[0] == self.food.position:
            self.snake.grow = True
            self.score += 10
            
            if self.score >= 100:
                self.spawn_obstacle()
                
            if self.score > self.high_score:
                self.high_score = self.score
                
            self.food.spawn(self.snake.body, self.obstacles)

    def draw_grid(self):
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (x, HEADER_HEIGHT), (x, SCREEN_HEIGHT))
        for y in range(HEADER_HEIGHT, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (SCREEN_WIDTH, y))

    def draw_header(self):
        pygame.draw.rect(self.screen, COLOR_HEADER, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
        pygame.draw.line(self.screen, COLOR_ACCENT, (0, HEADER_HEIGHT - 2), (SCREEN_WIDTH, HEADER_HEIGHT - 2), 2)

        level = 1 + (self.score // 50)
        txt_score = self.font_ui.render(f"PUNTOS: {self.score}", True, COLOR_TEXT)
        txt_high = self.font_ui.render(f"RÉCORD: {self.high_score}", True, COLOR_ACCENT)
        # NUEVO - El texto de nivel usa el color de la cabeza actual
        txt_level = self.font_ui.render(f"NIVEL: {level}", True, self.color_head) 

        self.screen.blit(txt_score, (20, 15))
        self.screen.blit(txt_level, (SCREEN_WIDTH // 2 - 40, 15))
        self.screen.blit(txt_high, (SCREEN_WIDTH - txt_high.get_width() - 20, 15))

    def draw_elements(self):
        food_rect = pygame.Rect(
            self.food.position[0] * GRID_SIZE + 2,
            HEADER_HEIGHT + self.food.position[1] * GRID_SIZE + 2,
            GRID_SIZE - 4,
            GRID_SIZE - 4
        )
        pygame.draw.rect(self.screen, COLOR_FOOD, food_rect, border_radius=6)
        
        for obs in self.obstacles:
            obs_rect = pygame.Rect(
                obs[0] * GRID_SIZE + 1,
                HEADER_HEIGHT + obs[1] * GRID_SIZE + 1,
                GRID_SIZE - 2,
                GRID_SIZE - 2
            )
            pygame.draw.rect(self.screen, COLOR_OBSTACLE, obs_rect, border_radius=2)

        for index, segment in enumerate(self.snake.body):
            seg_rect = pygame.Rect(
                segment[0] * GRID_SIZE + 1,
                HEADER_HEIGHT + segment[1] * GRID_SIZE + 1,
                GRID_SIZE - 2,
                GRID_SIZE - 2
            )
            # NUEVO - Asignar los colores personalizados
            color = self.color_head if index == 0 else self.color_body
            pygame.draw.rect(self.screen, color, seg_rect, border_radius=4)

    def draw_overlays(self):
        if self.state == STATE_MENU:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 6, 12, 220))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_title.render("MISIÓN 3: SNAKE", True, self.color_head)
            t2 = self.font_sub.render("Controles Juego: WASD / Flechas | Pausar: [P]", True, COLOR_TEXT)
            t_start = self.font_ui.render("Presiona [ESPACIO] para Iniciar", True, COLOR_ACCENT)

            # NUEVO - Textos para la personalización
            t3 = self.font_mini.render("< / > : Cambiar color CABEZA", True, self.color_head)
            t4 = self.font_mini.render("^ / v : Cambiar color CUERPO", True, self.color_body)

            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, 150))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 220))
            self.screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, 380))
            self.screen.blit(t4, (SCREEN_WIDTH // 2 - t4.get_width() // 2, 410))
            self.screen.blit(t_start, (SCREEN_WIDTH // 2 - t_start.get_width() // 2, 500))

            # NUEVO - Vista previa de la serpiente en el menú
            preview_w = GRID_SIZE * 3
            start_x = SCREEN_WIDTH // 2 - preview_w // 2
            start_y = 300
            
            # Dibujar 3 segmentos de vista previa
            pygame.draw.rect(self.screen, self.color_body, (start_x, start_y, GRID_SIZE-2, GRID_SIZE-2), border_radius=4)
            pygame.draw.rect(self.screen, self.color_body, (start_x + GRID_SIZE, start_y, GRID_SIZE-2, GRID_SIZE-2), border_radius=4)
            pygame.draw.rect(self.screen, self.color_head, (start_x + GRID_SIZE*2, start_y, GRID_SIZE-2, GRID_SIZE-2), border_radius=4)

        elif self.state == STATE_PAUSED:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 6, 12, 180))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_title.render("JUEGO EN PAUSA", True, COLOR_ACCENT)
            t2 = self.font_sub.render("Presiona [P] para reanudar", True, COLOR_TEXT)

            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, 260))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 320))

        elif self.state == STATE_GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((16, 6, 12, 225))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_title.render("¡FIN DEL JUEGO!", True, COLOR_FOOD)
            t2 = self.font_ui.render(f"Puntaje Obtenido: {self.score}", True, COLOR_TEXT)
            t3 = self.font_ui.render(f"Máximo Récord: {self.high_score}", True, COLOR_ACCENT)
            t4 = self.font_sub.render("Presiona [R] o [ESPACIO] para Reiniciar", True, self.color_head)

            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, 200))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 270))
            self.screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, 305))
            self.screen.blit(t4, (SCREEN_WIDTH // 2 - t4.get_width() // 2, 370))

    def run(self):
        while True:
            self.handle_events()
            self.update()

            self.screen.fill(COLOR_BG)
            self.draw_grid()
            self.draw_elements()
            self.draw_header()
            self.draw_overlays()

            pygame.display.flip()

            current_speed = self.base_speed + (self.score // 40)
            self.clock.tick(min(current_speed, 26))


if __name__ == "__main__":
    game = Game()
    game.run()