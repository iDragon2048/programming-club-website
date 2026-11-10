import pygame
import asyncio

# --- Constants ---
WIDTH, HEIGHT = 800, 400
FPS = 60
TILE_SIZE = 40

# Colors
BG_COLOR = (25, 35, 55)
BLOCK_COLOR = (45, 55, 75)
BLOCK_OUTLINE = (100, 150, 200)
SPIKE_COLOR = (255, 80, 80)
GRID_COLOR = (40, 50, 70)
UI_COLOR = (200, 200, 220)
CURSOR_COLOR = (255, 255, 50) # Bright yellow for the editor cursor

# Mode Colors
COLOR_CUBE = (0, 255, 150)
COLOR_SHIP = (255, 100, 200)
COLOR_BALL = (255, 150, 50)
COLOR_WAVE = (50, 200, 255)

# --- Maps ---
LEVEL_MAP_1 = [
    "                                                                                                                                                                        ",
    "                                                                                                                                                                        ",
    "                                                                                                                                                                        ",
    "                                           #############################################################################################################                ",
    "                                                  ^                       ^                                          ^                                                  ",
    "                                                                                                                                                                        ",
    "                                   >                      O                                                  W                                                          ",
    "                                                                                                                                                                        ",
    "            ###            ###       ^             ^^                    ###                                          ^^                       ^^                       ",
    "########################################################################################################################################################################"
]

LEVEL_MAP_2 = [
    "                                                                                                                                                                                                                ",
    "                                                                                                                                                                                                                ",
    "                                          #########################################                                                                     ###################                                     ",
    "                                                     ^                     ^                                                       ######################                                                       ",
    "                                     O                           W                    <           ^^^                          >           ^                   ^               O                              ",
    "                                                                                                                                                                                                              ",
    "                                                ^^                      ^^                                        #                                                                                           ",
    "                                 ^^                                                                             # #                             ^^                ^^                                          ",
    "           ^      ^^      ^             ^                                                  ^            ^     # # #       ^                                                          ^^             ^^^     ",
    "################################################################################################################################################################################################################"
]

class Player:
    def __init__(self):
        self.rect = pygame.Rect(100, HEIGHT // 2, 30, 30)
        self.true_y = float(self.rect.y)
        self.y_vel = 0
        self.mode = 'cube'
        self.gravity_dir = 1
        self.is_grounded = False

    def update(self, keys, space_pressed_this_frame, level_objects, scroll_x, speed):
        # Apply Physics
        if self.mode == 'cube':
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.is_grounded:
                self.y_vel = -11.5
                self.is_grounded = False
            self.y_vel += 0.9
            self.y_vel = min(self.y_vel, 12)

        elif self.mode == 'ship':
            if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                self.y_vel -= 0.8
            else:
                self.y_vel += 0.8
            self.y_vel = max(-8, min(self.y_vel, 8))

        elif self.mode == 'ball':
            if space_pressed_this_frame and self.is_grounded:
                self.gravity_dir *= -1
                self.is_grounded = False
            self.y_vel += 0.9 * self.gravity_dir
            self.y_vel = max(-12, min(self.y_vel, 12))

        elif self.mode == 'wave':
            if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                self.y_vel = -speed
            else:
                self.y_vel = speed

        # Move Y
        self.true_y += self.y_vel
        self.rect.y = int(self.true_y)
        self.is_grounded = False
        crashed = False

        # Y-Axis Collisions & Portals
        for obs in level_objects:
            screen_x = obs.rect.x - scroll_x
            if 'portal' in obs.obj_type and -TILE_SIZE < screen_x < WIDTH:
                portal_hitbox = pygame.Rect(screen_x, 0, TILE_SIZE, HEIGHT)
                if self.rect.colliderect(portal_hitbox):
                    if obs.obj_type == 'portal_ship' and self.mode != 'ship':
                        self.mode = 'ship'; self.gravity_dir = 1
                    elif obs.obj_type == 'portal_cube' and self.mode != 'cube':
                        self.mode = 'cube'; self.gravity_dir = 1
                    elif obs.obj_type == 'portal_ball' and self.mode != 'ball':
                        self.mode = 'ball'
                    elif obs.obj_type == 'portal_wave' and self.mode != 'wave':
                        self.mode = 'wave'; self.gravity_dir = 1

            if obs.obj_type == 'block' and -TILE_SIZE < screen_x < WIDTH:
                obs_rect = pygame.Rect(screen_x, obs.rect.y, TILE_SIZE, TILE_SIZE)
                if self.rect.colliderect(obs_rect):
                    if self.y_vel > 0 and self.rect.bottom <= obs_rect.top + 20:
                        self.rect.bottom = obs_rect.top
                        self.true_y = float(self.rect.y)
                        self.y_vel = 0
                        self.is_grounded = True
                    elif self.y_vel < 0 and self.rect.top >= obs_rect.bottom - 20:
                        self.rect.top = obs_rect.bottom
                        self.true_y = float(self.rect.y)
                        self.y_vel = 0
                        if self.mode == 'ball': self.is_grounded = True

        # Screen Boundaries
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.true_y = float(self.rect.y)
            if self.y_vel > 0: self.y_vel = 0
            if self.mode in ['cube', 'ball']: self.is_grounded = True

        if self.rect.top <= 0:
            self.rect.top = 0
            self.true_y = float(self.rect.y)
            if self.y_vel < 0: self.y_vel = 0
            if self.mode == 'ball' and self.gravity_dir == -1: self.is_grounded = True

        # Grounding Check
        check_rect = self.rect.move(0, 1 if self.gravity_dir == 1 else -1)
        for obs in level_objects:
            screen_x = obs.rect.x - scroll_x
            if obs.obj_type == 'block' and -TILE_SIZE < screen_x < WIDTH:
                if check_rect.colliderect(pygame.Rect(screen_x, obs.rect.y, TILE_SIZE, TILE_SIZE)):
                    self.is_grounded = True

        # X-Axis Collisions (Crashes)
        player_x_rect = self.rect.inflate(-4, -8)
        for obs in level_objects:
            screen_x = obs.rect.x - (scroll_x + speed)
            if -TILE_SIZE < screen_x < WIDTH:
                obs_rect = pygame.Rect(screen_x, obs.rect.y, TILE_SIZE, TILE_SIZE)
                if obs.obj_type == 'block' and player_x_rect.colliderect(obs_rect):
                    crashed = True
                elif obs.obj_type == 'spike' and self.rect.colliderect(obs_rect.inflate(-16, -16)):
                    crashed = True

        return crashed

class Obstacle:
    def __init__(self, x, y, obj_type):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.obj_type = obj_type

def draw_player(screen, player):
    if player.mode == 'cube':
        pygame.draw.rect(screen, COLOR_CUBE, player.rect)
        pygame.draw.rect(screen, (255, 255, 255), player.rect, 2)
    elif player.mode == 'ship':
        points = [(player.rect.left, player.rect.top), (player.rect.right, player.rect.centery), (player.rect.left, player.rect.bottom)]
        pygame.draw.polygon(screen, COLOR_SHIP, points)
    elif player.mode == 'ball':
        pygame.draw.circle(screen, COLOR_BALL, player.rect.center, 15)
        pygame.draw.circle(screen, (255, 255, 255), player.rect.center, 5)
    elif player.mode == 'wave':
        if player.y_vel < 0 or (player.y_vel == 0 and player.gravity_dir == 1):
            points = [(player.rect.left, player.rect.bottom), (player.rect.centerx, player.rect.top), (player.rect.right, player.rect.bottom)]
        else:
            points = [(player.rect.left, player.rect.top), (player.rect.centerx, player.rect.bottom), (player.rect.right, player.rect.top)]
        pygame.draw.polygon(screen, COLOR_WAVE, points)

def parse_map(level_map):
    objects = []
    width = len(level_map[0]) * TILE_SIZE
    for row_idx, row in enumerate(level_map):
        for col_idx, col in enumerate(row):
            x, y = col_idx * TILE_SIZE, row_idx * TILE_SIZE
            if col == '#': objects.append(Obstacle(x, y, 'block'))
            elif col == '^': objects.append(Obstacle(x, y, 'spike'))
            elif col == '>': objects.append(Obstacle(x, y, 'portal_ship'))
            elif col == '<': objects.append(Obstacle(x, y, 'portal_cube'))
            elif col == 'O': objects.append(Obstacle(x, y, 'portal_ball'))
            elif col == 'W': objects.append(Obstacle(x, y, 'portal_wave'))
    return objects, width

def draw_text(screen, text, x, y, size=36, color=UI_COLOR):
    font = pygame.font.SysFont(None, size)
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(x, y))
    screen.blit(surface, rect)
    return rect

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Geometry Clone: Advanced")
    clock = pygame.time.Clock()

    state = "MENU"  # States: MENU, PLAYING, EDITOR
    current_level_map = LEVEL_MAP_1

    # Gameplay Vars
    player = Player()
    scroll_x = 0
    speed = 7
    game_over = False
    death_timer = 0
    level_objects = []
    max_width = 0

    # Menu Vars
    menu_idx = 0
    menu_options = ["PLAY LEVEL 1", "PLAY LEVEL 2", "LEVEL EDITOR"]
    menu_colors = [COLOR_CUBE, COLOR_SHIP, COLOR_WAVE]

    # Editor Vars
    # Start the editor with 9 rows of air and 1 bottom row of solid blocks
    editor_map = [list(" " * 100) for _ in range(9)] + [list("#" * 100)]
    editor_scroll = 0

    # New Keyboard Cursor coordinates (Grid space, not pixels)
    cursor_x, cursor_y = 0, 8

    tools = ['#', '^', '>', '<', 'O', 'W']
    tool_names = ['Block', 'Spike', 'Ship Portal', 'Cube Portal', 'Ball Portal', 'Wave Portal']
    current_tool_idx = 0

    running = True
    while running:
        space_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Capture jump only for gameplay
                if state == "PLAYING" and event.key in (pygame.K_SPACE, pygame.K_UP):
                    space_pressed = True

                # Global Escape key
                if event.key == pygame.K_ESCAPE:
                    state = "MENU"

                # --- MAIN MENU INPUT ---
                if state == "MENU":
                    if event.key == pygame.K_UP:
                        menu_idx = (menu_idx - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        menu_idx = (menu_idx + 1) % len(menu_options)
                    elif event.key == pygame.K_RETURN:
                        if menu_idx == 0:
                            state = "PLAYING"
                            current_level_map = LEVEL_MAP_1
                            level_objects, max_width = parse_map(current_level_map)
                            scroll_x = 0; player = Player(); game_over = False
                        elif menu_idx == 1:
                            state = "PLAYING"
                            current_level_map = LEVEL_MAP_2
                            level_objects, max_width = parse_map(current_level_map)
                            scroll_x = 0; player = Player(); game_over = False
                        elif menu_idx == 2:
                            state = "EDITOR"

                # --- LEVEL EDITOR INPUT (Crucial fix: 'elif' prevents double-triggering) ---
                elif state == "EDITOR":
                    if pygame.K_1 <= event.key <= pygame.K_6:
                        current_tool_idx = event.key - pygame.K_1
                    elif event.key == pygame.K_RETURN:  # Playtest custom level
                        state = "PLAYING"
                        current_level_map = ["".join(row) for row in editor_map]
                        level_objects, max_width = parse_map(current_level_map)
                        scroll_x = 0
                        player = Player()

                    # Keyboard Cursor Movement
                    elif event.key == pygame.K_UP:
                        cursor_y = max(0, cursor_y - 1)
                    elif event.key == pygame.K_DOWN:
                        cursor_y = min(9, cursor_y + 1)
                    elif event.key == pygame.K_LEFT:
                        cursor_x = max(0, cursor_x - 1)
                    elif event.key == pygame.K_RIGHT:
                        cursor_x = min(99, cursor_x + 1)

                    # Block Placing / Erasing
                    elif event.key == pygame.K_SPACE:
                        editor_map[cursor_y][cursor_x] = tools[current_tool_idx]
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        editor_map[cursor_y][cursor_x] = ' '

        keys = pygame.key.get_pressed()
        screen.fill(BG_COLOR)

        # ================= MAIN MENU =================
        if state == "MENU":
            draw_text(screen, "GEOMETRY CLONE", WIDTH//2, 80, 60, (255, 255, 255))
            draw_text(screen, "Use Up/Down Arrows and ENTER to select", WIDTH//2, 120, 24, (150, 160, 180))

            for i, option in enumerate(menu_options):
                y_pos = 180 + (i * 60)
                if i == menu_idx:
                    text = f">  [ {option} ]  <"
                    color = (255, 255, 255) # Highlight bright white
                else:
                    text = f"[ {option} ]"
                    color = menu_colors[i]

                draw_text(screen, text, WIDTH//2, y_pos, 40, color)

        # ================= LEVEL EDITOR =================
        elif state == "EDITOR":
            # Auto-scroll camera to keep the cursor on screen
            cursor_pixel_x = cursor_x * TILE_SIZE
            if cursor_pixel_x < editor_scroll:
                editor_scroll = cursor_pixel_x
            elif cursor_pixel_x >= editor_scroll + WIDTH - TILE_SIZE:
                editor_scroll = cursor_pixel_x - WIDTH + TILE_SIZE

            # Draw Grid
            for x in range(-editor_scroll % TILE_SIZE, WIDTH, TILE_SIZE):
                pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
            for y in range(0, HEIGHT, TILE_SIZE):
                pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

            # Draw Blocks
            for r in range(10):
                for c in range(100):
                    char = editor_map[r][c]
                    sx = c * TILE_SIZE - editor_scroll
                    if -TILE_SIZE < sx < WIDTH and char != ' ':
                        if char == '#': pygame.draw.rect(screen, BLOCK_COLOR, (sx, r*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                        elif char == '^': pygame.draw.polygon(screen, SPIKE_COLOR, [(sx, r*TILE_SIZE+TILE_SIZE), (sx+TILE_SIZE, r*TILE_SIZE+TILE_SIZE), (sx+TILE_SIZE//2, r*TILE_SIZE)])
                        elif char in ['>', '<', 'O', 'W']:
                            col = COLOR_SHIP if char=='>' else COLOR_CUBE if char=='<' else COLOR_BALL if char=='O' else COLOR_WAVE
                            pygame.draw.ellipse(screen, col, (sx+10, r*TILE_SIZE-10, 20, 60), 4)

            # Draw Keyboard Cursor
            pygame.draw.rect(screen, CURSOR_COLOR, (cursor_pixel_x - editor_scroll, cursor_y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)

            # UI Overlay
            pygame.draw.rect(screen, (10, 10, 10), (0, 0, WIDTH, 40))
            draw_text(screen, f"Holding (1-6): {tool_names[current_tool_idx]}", 160, 20, 22)
            draw_text(screen, "ARROWS: Move | SPACE: Place | BKSP: Erase | ENTER: Test", WIDTH - 270, 20, 22)

        # ================= PLAYING GAME =================
        elif state == "PLAYING":
            if not game_over:
                crashed = player.update(keys, space_pressed, level_objects, scroll_x, speed)
                if crashed:
                    game_over = True
                    death_timer = 0
                else:
                    scroll_x += speed
                if scroll_x > max_width - WIDTH:
                    state = "MENU" # Level Beaten
            else:
                death_timer += 1
                if death_timer > 30:
                    game_over = False
                    scroll_x = 0
                    player = Player()

            # Draw Level
            for obs in level_objects:
                sx = obs.rect.x - scroll_x
                if -TILE_SIZE < sx < WIDTH:
                    if obs.obj_type == 'spike':
                        points = [(sx, obs.rect.bottom), (sx + TILE_SIZE, obs.rect.bottom), (sx + TILE_SIZE//2, obs.rect.top)]
                        if obs.rect.y <= HEIGHT // 2: # Ceiling spike pointing down
                            points = [(sx, obs.rect.top), (sx + TILE_SIZE, obs.rect.top), (sx + TILE_SIZE//2, obs.rect.bottom)]
                        pygame.draw.polygon(screen, SPIKE_COLOR, points)
                    elif obs.obj_type == 'block':
                        pygame.draw.rect(screen, BLOCK_COLOR, (sx, obs.rect.y, TILE_SIZE, TILE_SIZE))
                        pygame.draw.rect(screen, BLOCK_OUTLINE, (sx, obs.rect.y, TILE_SIZE, TILE_SIZE), 1)
                    elif 'portal' in obs.obj_type:
                        col = COLOR_CUBE
                        if 'ship' in obs.obj_type: col = COLOR_SHIP
                        if 'ball' in obs.obj_type: col = COLOR_BALL
                        if 'wave' in obs.obj_type: col = COLOR_WAVE
                        pygame.draw.ellipse(screen, col, (sx+10, obs.rect.y-10, 20, 60), 4)

            # Draw Player
            if not game_over:
                draw_player(screen, player)

            # Progress/UI
            draw_text(screen, "ESC: Quit to Menu", 80, 20, 24)

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

await main()