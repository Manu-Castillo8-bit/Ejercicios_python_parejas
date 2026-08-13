import sys
import random
import os
import pygame

# -------------------------------------------------------------
# CONSTANTES Y CONFIGURACIÓN GENERAL
# -------------------------------------------------------------
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 650  # 600 de área de juego + 50 para el panel superior
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - 50) // GRID_SIZE
HEADER_HEIGHT = 50

# Paleta de Colores (Estilo Neón / Cyberpunk)
COLOR_BG = (10, 10, 20)           # Fondo oscuro
COLOR_GRID = (22, 22, 38)         # Líneas de cuadrícula
COLOR_HEADER = (16, 16, 28)       # Barra superior
COLOR_SNAKE_HEAD = (0, 240, 255)  # Cabeza: Cian Neón
COLOR_SNAKE_BODY = (57, 255, 136) # Cuerpo: Verde Neón
COLOR_FOOD = (255, 46, 151)       # Comida: Magenta Neón
COLOR_TEXT = (233, 233, 246)      # Texto blanco suave
COLOR_ACCENT = (255, 179, 0)      # Acento: Ámbar
COLOR_OBSTACLE = (255, 50, 50)    # NUEVO - Obstáculo: Rojo Neón

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
    """Clase que gestiona la posición, crecimiento y colisiones de la serpiente."""
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
        # Evitar giro de 180 grados instantáneo
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
    """Clase que gestiona la generación aleatoria de la comida."""
    def __init__(self):
        self.position = (0, 0)

    # NUEVO - Ahora pasamos los obstáculos para que la comida no aparezca sobre ellos
    def spawn(self, snake_body, obstacles):
        while True:
            new_pos = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
            # Asegura que la comida no aparezca sobre el cuerpo o los obstáculos
            if new_pos not in snake_body and new_pos not in obstacles:
                self.position = new_pos
                break


class Game:
    """Controlador principal del flujo del juego, gráficos y eventos."""
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Misión 3: Snake Game · INDEL 3DS")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fuentes
        self.font_ui = pygame.font.SysFont("Consolas", 18, bold=True)
        self.font_title = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_sub = pygame.font.SysFont("Consolas", 16)

        self.snake = Snake()
        self.food = Food()
        self.obstacles = [] # NUEVO - Lista para guardar los obstáculos
        self.food.spawn(self.snake.body, self.obstacles)

        self.score = 0
        self.high_score = self.load_high_score()
        self.state = STATE_MENU
        self.base_speed = 10

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

    # NUEVO - Función para generar obstáculos
    def spawn_obstacle(self):
        while True:
            new_pos = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
            # Evitamos que el obstáculo aparezca sobre la serpiente, la comida u otro obstáculo
            if (new_pos not in self.snake.body and 
                new_pos != self.food.position and 
                new_pos not in self.obstacles):
                
                self.obstacles.append(new_pos)
                break

    def reset_game(self):
        self.snake.reset()
        self.obstacles.clear() # NUEVO - Limpiar obstáculos al reiniciar
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

        # NUEVO - Detección de colisión con bordes, consigo misma, o con un OBSTÁCULO
        if (self.snake.check_wall_collision() or 
            self.snake.check_self_collision() or 
            self.snake.body[0] in self.obstacles):
            
            self.state = STATE_GAME_OVER
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            return

        # Detección de colisión con la comida
        if self.snake.body[0] == self.food.position:
            self.snake.grow = True
            self.score += 10
            
            # NUEVO - Si el puntaje es 100 o más, generamos un obstáculo nuevo cada vez que come
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
        # Fondo de la barra superior
        pygame.draw.rect(self.screen, COLOR_HEADER, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
        pygame.draw.line(self.screen, COLOR_ACCENT, (0, HEADER_HEIGHT - 2), (SCREEN_WIDTH, HEADER_HEIGHT - 2), 2)

        # Información: Score, High Score y Nivel/Velocidad
        level = 1 + (self.score // 50)
        txt_score = self.font_ui.render(f"PUNTOS: {self.score}", True, COLOR_TEXT)
        txt_high = self.font_ui.render(f"RÉCORD: {self.high_score}", True, COLOR_ACCENT)
        txt_level = self.font_ui.render(f"NIVEL: {level}", True, COLOR_SNAKE_HEAD)

        self.screen.blit(txt_score, (20, 15))
        self.screen.blit(txt_level, (SCREEN_WIDTH // 2 - 40, 15))
        self.screen.blit(txt_high, (SCREEN_WIDTH - txt_high.get_width() - 20, 15))

    def draw_elements(self):
        # 1. Dibujar Comida
        food_rect = pygame.Rect(
            self.food.position[0] * GRID_SIZE + 2,
            HEADER_HEIGHT + self.food.position[1] * GRID_SIZE + 2,
            GRID_SIZE - 4,
            GRID_SIZE - 4
        )
        pygame.draw.rect(self.screen, COLOR_FOOD, food_rect, border_radius=6)
        
        # NUEVO - 2. Dibujar Obstáculos
        for obs in self.obstacles:
            obs_rect = pygame.Rect(
                obs[0] * GRID_SIZE + 1,
                HEADER_HEIGHT + obs[1] * GRID_SIZE + 1,
                GRID_SIZE - 2,
                GRID_SIZE - 2
            )
            # Dibujamos un cuadrado sólido para el obstáculo
            pygame.draw.rect(self.screen, COLOR_OBSTACLE, obs_rect, border_radius=2)

        # 3. Dibujar Serpiente
        for index, segment in enumerate(self.snake.body):
            seg_rect = pygame.Rect(
                segment[0] * GRID_SIZE + 1,
                HEADER_HEIGHT + segment[1] * GRID_SIZE + 1,
                GRID_SIZE - 2,
                GRID_SIZE - 2
            )
            color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
            pygame.draw.rect(self.screen, color, seg_rect, border_radius=4)

    def draw_overlays(self):
        # Pantalla de Inicio / Menú
        if self.state == STATE_MENU:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 6, 12, 220))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_title.render("MISIÓN 3: SNAKE", True, COLOR_SNAKE_HEAD)
            t2 = self.font_sub.render("Controles: WASD o Flechas de Dirección", True, COLOR_TEXT)
            t3 = self.font_sub.render("Pausar: Tecla [P]", True, COLOR_TEXT)
            t4 = self.font_ui.render("Presiona [ESPACIO] para Iniciar", True, COLOR_ACCENT)

            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, 200))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 280))
            self.screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, 310))
            self.screen.blit(t4, (SCREEN_WIDTH // 2 - t4.get_width() // 2, 380))

        # Pantalla de Pausa
        elif self.state == STATE_PAUSED:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 6, 12, 180))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_title.render("JUEGO EN PAUSA", True, COLOR_ACCENT)
            t2 = self.font_sub.render("Presiona [P] para reanudar", True, COLOR_TEXT)

            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, 260))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 320))

        # Pantalla de Fin de Juego (Game Over)
        elif self.state == STATE_GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((16, 6, 12, 225))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_title.render("¡FIN DEL JUEGO!", True, COLOR_FOOD)
            t2 = self.font_ui.render(f"Puntaje Obtenido: {self.score}", True, COLOR_TEXT)
            t3 = self.font_ui.render(f"Máximo Récord: {self.high_score}", True, COLOR_ACCENT)
            t4 = self.font_sub.render("Presiona [R] o [ESPACIO] para Reiniciar", True, COLOR_SNAKE_HEAD)

            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, 200))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 270))
            self.screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, 305))
            self.screen.blit(t4, (SCREEN_WIDTH // 2 - t4.get_width() // 2, 370))

    def run(self):
        """Bucle principal (Game Loop)."""
        while True:
            self.handle_events()
            self.update()

            # Renderizado
            self.screen.fill(COLOR_BG)
            self.draw_grid()
            self.draw_elements()
            self.draw_header()
            self.draw_overlays()

            pygame.display.flip()

            # Aumento progresivo de dificultad (velocidad FPS según puntuación)
            current_speed = self.base_speed + (self.score // 40)
            self.clock.tick(min(current_speed, 26))  # Límite máximo de 26 FPS


if __name__ == "__main__":
    game = Game()
    game.run()