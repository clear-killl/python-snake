import random
import tkinter as tk
from collections import deque


BACKGROUND = "#ffffff"
PANEL = "#f1f3f4"
GRID_COLOR = "#dfe3e8"
TEXT_COLOR = "#202124"
MUTED_COLOR = "#5f6368"
ACCENT = "#34a853"
PINK = "#ea4335"
YELLOW = "#fbbc04"
BLUE = "#4285f4"
MINES_CLOSED = "#4285f4"
MINES_HOVER = "#3367d6"
MINES_OPEN = "#e8f0fe"
MINES_TEXT = "#202124"
MINES_MINE = "#ea4335"
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SNAKE_WIN_SCORE = 10
MATCH_WIN_SCORE = 700
THEMES = {
    "light": {
        "background": "#ffffff",
        "panel": "#f1f3f4",
        "grid": "#dfe3e8",
        "text": "#202124",
        "muted": "#5f6368",
    },
    "dark": {
        "background": "#202124",
        "panel": "#303134",
        "grid": "#5f6368",
        "text": "#f8f9fa",
        "muted": "#bdc1c6",
    },
}


def make_button(parent, text, command, **kwargs):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=kwargs.pop("bg", PANEL),
        fg=kwargs.pop("fg", TEXT_COLOR),
        activebackground=kwargs.pop("activebackground", GRID_COLOR),
        activeforeground=TEXT_COLOR,
        font=kwargs.pop("font", ("Segoe UI", 10, "bold")),
        relief="flat",
        bd=0,
        padx=12,
        pady=7,
        cursor="hand2",
        **kwargs,
    )


def is_restart_key(event):
    values = {
        str(getattr(event, "char", "")).lower(),
        str(getattr(event, "keysym", "")).lower(),
        str(getattr(event, "keysym_num", "")).lower(),
    }
    restart_names = {"r", "к", "р", "cyrillic_ka", "cyrillic_er"}
    return bool(values & restart_names) or getattr(event, "keycode", None) in (72, 82)


def set_theme(theme_name):
    global BACKGROUND, PANEL, GRID_COLOR, TEXT_COLOR, MUTED_COLOR
    theme = THEMES[theme_name]
    BACKGROUND = theme["background"]
    PANEL = theme["panel"]
    GRID_COLOR = theme["grid"]
    TEXT_COLOR = theme["text"]
    MUTED_COLOR = theme["muted"]

class VictoryAnimation:
    COLORS = ("#4285f4", "#ea4335", "#fbbc04", "#34a853")

    def __init__(self, parent):
        self.parent = parent
        self.overlay = tk.Frame(parent, bg=BACKGROUND, bd=0)
        self.overlay.place(relx=0.5, rely=0.5, relwidth=0.7, relheight=0.42, anchor="center")
        self.title = tk.Label(
            self.overlay,
            text="ПОБЕДА!",
            bg=BACKGROUND,
            fg="#4285f4",
            font=("Segoe UI", 30, "bold"),
        )
        self.title.place(relx=0.5, rely=0.5, anchor="center")
        self.particles = []
        for index in range(18):
            particle = tk.Label(
                self.overlay,
                text="●",
                bg=BACKGROUND,
                fg=self.COLORS[index % len(self.COLORS)],
                font=("Segoe UI", 18, "bold"),
            )
            particle.place(x=(index * 37) % 260, y=(index * 23) % 120)
            self.particles.append(particle)
        self.step = 0
        self.job = self.parent.after(80, self.animate)

    def animate(self):
        self.step += 1
        width = max(self.overlay.winfo_width(), 280)
        height = max(self.overlay.winfo_height(), 150)
        for index, particle in enumerate(self.particles):
            x = (index * 47 + self.step * (2 + index % 3)) % max(width - 20, 1)
            y = (index * 29 + self.step * (3 + index % 4)) % max(height - 20, 1)
            particle.place(x=x, y=y)
        self.job = self.parent.after(80, self.animate)

    def destroy(self):
        if hasattr(self, "job"):
            self.parent.after_cancel(self.job)
        self.overlay.destroy()


class SnakeGame:
    CELL_SIZE = 24
    GRID_WIDTH = 26
    GRID_HEIGHT = 20
    TICK_MS = 105

    def __init__(self, parent):
        self.parent = parent
        self.canvas = tk.Canvas(
            parent,
            width=self.CELL_SIZE * self.GRID_WIDTH,
            height=self.CELL_SIZE * self.GRID_HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=14)
        self.canvas.bind("<Configure>", lambda _: self.draw())
        self.info = tk.Label(parent, bg=BACKGROUND, fg=MUTED_COLOR, font=("Segoe UI", 10))
        self.info.pack(pady=(8, 10))
        self.reset()

    def reset(self):
        if hasattr(self, "tick_job"):
            self.parent.after_cancel(self.tick_job)
        if hasattr(self, "victory"):
            self.victory.destroy()
        center = (self.GRID_WIDTH // 2, self.GRID_HEIGHT // 2)
        self.snake = deque([center, (center[0] - 1, center[1]), (center[0] - 2, center[1])])
        self.direction = (1, 0)
        self.next_direction = self.direction
        self.score = 0
        self.paused = False
        self.game_over = False
        self.won = False
        self.food = self.new_food()
        self.info.config(text=f"Счет: 0/{SNAKE_WIN_SCORE} | Стрелки/WASD | Пробел: пауза | R, К или Р: заново")
        self.draw()
        self.schedule_tick()

    def new_food(self):
        free = [
            (x, y)
            for x in range(self.GRID_WIDTH)
            for y in range(self.GRID_HEIGHT)
            if (x, y) not in self.snake
        ]
        return random.choice(free)

    def handle_key(self, event):
        key = event.keysym.lower()
        if is_restart_key(event):
            self.reset()
            return
        if key == "space" and not self.game_over:
            self.paused = not self.paused
            self.info.config(
                text="ПАУЗА | Пробел: продолжить"
                if self.paused
                else f"Счет: {self.score}/{SNAKE_WIN_SCORE} | Стрелки/WASD | Пробел: пауза | R, К или Р: заново"
            )
            return
        directions = {
            "up": (0, -1), "w": (0, -1), "ц": (0, -1),
            "down": (0, 1), "s": (0, 1), "ы": (0, 1),
            "left": (-1, 0), "a": (-1, 0), "ф": (-1, 0),
            "right": (1, 0), "d": (1, 0), "в": (1, 0),
        }
        if key in directions and directions[key] != (-self.direction[0], -self.direction[1]):
            self.next_direction = directions[key]

    def schedule_tick(self):
        self.tick_job = self.parent.after(self.TICK_MS, self.tick)

    def destroy(self):
        if hasattr(self, "tick_job"):
            self.parent.after_cancel(self.tick_job)
        if hasattr(self, "victory"):
            self.victory.destroy()

    def tick(self):
        if not self.paused and not self.game_over:
            self.direction = self.next_direction
            head_x, head_y = self.snake[0]
            new_head = (head_x + self.direction[0], head_y + self.direction[1])
            eating = new_head == self.food
            body = self.snake if eating else list(self.snake)[:-1]
            hit_wall = not (
                0 <= new_head[0] < self.GRID_WIDTH
                and 0 <= new_head[1] < self.GRID_HEIGHT
            )
            if hit_wall or new_head in body:
                self.game_over = True
                self.info.config(text="ИГРА ОКОНЧЕНА | R, К или Р: заново")
            else:
                self.snake.appendleft(new_head)
                if eating:
                    self.score += 1
                    self.food = self.new_food()
                    if self.score >= SNAKE_WIN_SCORE:
                        self.won = True
                        self.paused = True
                        self.info.config(text=f"ПОБЕДА! Ты набрал {SNAKE_WIN_SCORE} очков | R, К или Р: заново")
                        self.victory = VictoryAnimation(self.parent)
                else:
                    self.snake.pop()
            if not self.game_over and not self.won:
                self.info.config(text=f"Счет: {self.score}/{SNAKE_WIN_SCORE} | Стрелки/WASD | R, К или Р: заново")
            self.draw()
        self.schedule_tick()

    def draw(self):
        self.canvas.delete("all")
        canvas_width = max(self.canvas.winfo_width(), self.CELL_SIZE * self.GRID_WIDTH)
        canvas_height = max(self.canvas.winfo_height(), self.CELL_SIZE * self.GRID_HEIGHT)
        cell_size = min(canvas_width / self.GRID_WIDTH, canvas_height / self.GRID_HEIGHT)
        width = cell_size * self.GRID_WIDTH
        height = cell_size * self.GRID_HEIGHT
        offset_x = (canvas_width - width) / 2
        offset_y = (canvas_height - height) / 2
        for x in range(self.GRID_WIDTH + 1):
            self.canvas.create_line(
                offset_x + x * cell_size,
                offset_y,
                offset_x + x * cell_size,
                offset_y + height,
                fill=GRID_COLOR,
            )
        for y in range(self.GRID_HEIGHT + 1):
            self.canvas.create_line(
                offset_x,
                offset_y + y * cell_size,
                offset_x + width,
                offset_y + y * cell_size,
                fill=GRID_COLOR,
            )
        food_x, food_y = self.food
        self.canvas.create_oval(
            offset_x + food_x * cell_size + cell_size * 0.2,
            offset_y + food_y * cell_size + cell_size * 0.2,
            offset_x + (food_x + 1) * cell_size - cell_size * 0.2,
            offset_y + (food_y + 1) * cell_size - cell_size * 0.2,
            fill=PINK,
            outline="",
        )
        for index, (x, y) in enumerate(self.snake):
            padding = cell_size * (0.08 if index == 0 else 0.16)
            self.canvas.create_rectangle(
                offset_x + x * cell_size + padding,
                offset_y + y * cell_size + padding,
                offset_x + (x + 1) * cell_size - padding,
                offset_y + (y + 1) * cell_size - padding,
                fill=ACCENT if index == 0 else "#35c98b",
                outline="",
            )
        if self.game_over:
            self.canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="GAME OVER",
                fill=TEXT_COLOR,
                font=("Segoe UI", 26, "bold"),
            )


class MinesweeperGame:
    DIFFICULTIES = {
        "Малое 9 x 9": (9, 9, 10),
        "Среднее 16 x 16": (16, 16, 40),
        "Большое 30 x 16": (30, 16, 99),
    }

    def __init__(self, parent):
        self.parent = parent
        controls = tk.Frame(parent, bg=BACKGROUND)
        controls.pack(pady=(0, 8))
        self.difficulty = tk.StringVar(value="Малое 9 x 9")
        menu = tk.OptionMenu(controls, self.difficulty, *self.DIFFICULTIES)
        menu.config(
            bg=MINES_CLOSED,
            fg=TEXT_COLOR,
            activebackground=MINES_HOVER,
            highlightthickness=0,
            font=("Segoe UI", 10),
        )
        menu.pack(side="left", padx=5)
        make_button(controls, "Новая игра", self.reset).pack(side="left", padx=5)
        self.info = tk.Label(parent, bg=BACKGROUND, fg=MUTED_COLOR, font=("Segoe UI", 10))
        self.info.pack(pady=(0, 6))
        self.board = tk.Frame(parent, bg=BACKGROUND)
        self.board.pack(fill="both", expand=True)
        self.board.bind("<Configure>", lambda _: self.update_cell_font())
        self.reset()

    def reset(self):
        if hasattr(self, "explosion_job"):
            self.parent.after_cancel(self.explosion_job)
        if hasattr(self, "victory"):
            self.victory.destroy()
        if hasattr(self, "buttons"):
            for row in self.buttons:
                for cell in row:
                    cell.destroy()
        self.width, self.height, self.mine_count = self.DIFFICULTIES[self.difficulty.get()]
        cells = [(x, y) for x in range(self.width) for y in range(self.height)]
        self.mines = set(random.sample(cells, self.mine_count))
        self.revealed = set()
        self.flags = set()
        self.finished = False
        self.first_move = True
        self.buttons = []
        for column in range(self.width):
            self.board.grid_columnconfigure(column, weight=1, uniform="mines-column")
        for row in range(self.height):
            self.board.grid_rowconfigure(row, weight=1, uniform="mines-row")
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = tk.Button(
                    self.board,
                    text="",
                    width=2,
                    height=1,
                    bg=MINES_CLOSED,
                    fg=TEXT_COLOR,
                    activebackground=MINES_HOVER,
                    relief="flat",
                    bd=0,
                    font=("Segoe UI Emoji", 10, "bold"),
                )
                cell.grid(row=y, column=x, sticky="nsew", padx=1, pady=1)
                cell.bind("<Button-1>", lambda _, cx=x, cy=y: self.reveal(cx, cy))
                cell.bind("<Button-3>", lambda _, cx=x, cy=y: self.toggle_flag(cx, cy))
                row.append(cell)
            self.buttons.append(row)
        self.info.config(
            text=f"Мины: {self.mine_count} | Левая кнопка: открыть, правая: флаг | R, К или Р: заново"
        )
        self.update_cell_font()

    def update_cell_font(self):
        if not getattr(self, "buttons", None) or not self.width or not self.height:
            return
        cell_width = self.board.winfo_width() / self.width
        cell_height = self.board.winfo_height() / self.height
        font_size = max(8, min(30, int(min(cell_width, cell_height) * 0.42)))
        cell_font = ("Segoe UI Emoji", font_size, "bold")
        for row in self.buttons:
            for cell in row:
                cell.config(font=cell_font)

    def handle_key(self, event):
        if is_restart_key(event):
            self.reset()

    def destroy(self):
        if hasattr(self, "explosion_job"):
            self.parent.after_cancel(self.explosion_job)
        if hasattr(self, "victory"):
            self.victory.destroy()

    def neighbors(self, x, y):
        return [
            (nx, ny)
            for nx in range(max(0, x - 1), min(self.width, x + 2))
            for ny in range(max(0, y - 1), min(self.height, y + 2))
            if (nx, ny) != (x, y)
        ]

    def mine_count_at(self, x, y):
        return sum(cell in self.mines for cell in self.neighbors(x, y))

    def reveal(self, x, y):
        if self.finished or (x, y) in self.flags or (x, y) in self.revealed:
            return
        if self.first_move:
            self.first_move = False
            if (x, y) in self.mines:
                free_cells = [
                    (cell_x, cell_y)
                    for cell_x in range(self.width)
                    for cell_y in range(self.height)
                    if (cell_x, cell_y) not in self.mines and (cell_x, cell_y) != (x, y)
                ]
                self.mines.remove((x, y))
                self.mines.add(random.choice(free_cells))
        if (x, y) in self.mines:
            self.finished = True
            self.explosion_cells = list(self.mines)
            for mine_x, mine_y in self.explosion_cells:
                self.buttons[mine_y][mine_x].config(text="💣", bg=YELLOW, fg=MINES_TEXT)
            self.info.config(text="Бум! R, К или Р: новая игра")
            self.explosion_job = self.parent.after(350, self.animate_explosion, 0)
            return
        queue = deque([(x, y)])
        while queue:
            cell = queue.popleft()
            if cell in self.revealed or cell in self.flags:
                continue
            self.revealed.add(cell)
            cell_x, cell_y = cell
            count = self.mine_count_at(cell_x, cell_y)
            colors = {1: "#1967d2", 2: "#188038", 3: "#d93025", 4: "#b06000"}
            self.buttons[cell_y][cell_x].config(
                text=str(count) if count else " ",
                relief="sunken",
                bg=MINES_OPEN,
                fg=colors.get(count, MINES_TEXT),
            )
            if count == 0:
                queue.extend(
                    neighbor
                    for neighbor in self.neighbors(cell_x, cell_y)
                    if neighbor not in self.revealed
                )
        if len(self.revealed) == self.width * self.height - self.mine_count:
            self.finished = True
            self.info.config(text="Победа! R, К или Р: новая игра")
            self.victory = VictoryAnimation(self.parent)
        elif not self.finished:
            self.info.config(
                text=f"Очки: {len(self.revealed)}/{self.width * self.height - self.mine_count} | Мины: {self.mine_count} | R, К или Р: заново"
            )

    def animate_explosion(self, index):
        if index >= len(self.explosion_cells):
            return
        mine_x, mine_y = self.explosion_cells[index]
        self.buttons[mine_y][mine_x].config(text="💥", bg=MINES_MINE, fg=TEXT_COLOR)
        self.explosion_job = self.parent.after(120, self.animate_explosion, index + 1)

    def toggle_flag(self, x, y):
        if self.finished or (x, y) in self.revealed:
            return
        if (x, y) in self.flags:
            self.flags.remove((x, y))
            self.buttons[y][x].config(text="")
        else:
            self.flags.add((x, y))
            self.buttons[y][x].config(text="F", fg=YELLOW)


class MatchThreeGame:
    ROWS = 8
    COLS = 8
    COLORS = ["#ff5c8a", "#ffd166", "#6cb6ff", "#7bf1a8", "#b58cff", "#ff9f68"]

    def __init__(self, parent):
        self.parent = parent
        self.info = tk.Label(parent, bg=BACKGROUND, fg=MUTED_COLOR, font=("Segoe UI", 10))
        self.info.pack(pady=(0, 8))
        self.board = tk.Frame(parent, bg=BACKGROUND)
        self.board.pack(fill="both", expand=True)
        self.reset()

    def reset(self):
        if hasattr(self, "animation_job") and self.animation_job is not None:
            self.parent.after_cancel(self.animation_job)
        if hasattr(self, "victory"):
            self.victory.destroy()
        self.score = 0
        self.selected = None
        self.dragging = False
        self.drag_target = None
        self.flash_cells = set()
        self.flash_visible = False
        self.animating = False
        self.won = False
        self.animation_job = None
        self.tiles = []
        while not self.tiles or self.find_matches():
            self.tiles = [
                [random.randrange(len(self.COLORS)) for _ in range(self.COLS)]
                for _ in range(self.ROWS)
            ]
        self.draw()

    def handle_key(self, event):
        if is_restart_key(event):
            self.reset()

    def destroy(self):
        if self.animation_job is not None:
            self.parent.after_cancel(self.animation_job)
        if hasattr(self, "victory"):
            self.victory.destroy()

    def draw(self):
        for child in self.board.winfo_children():
            child.destroy()
        self.buttons = []
        for column in range(self.COLS):
            self.board.grid_columnconfigure(column, weight=1, uniform="match-column")
        for row in range(self.ROWS):
            self.board.grid_rowconfigure(row, weight=1, uniform="match-row")
        for y in range(self.ROWS):
            row_buttons = []
            for x in range(self.COLS):
                border = 3 if self.selected == (x, y) else 1
                color = "#ffffff" if (x, y) in self.flash_cells and self.flash_visible else self.COLORS[self.tiles[y][x]]
                cell = tk.Button(
                    self.board,
                    bg=color,
                    activebackground=color,
                    width=1,
                    height=1,
                    relief="sunken" if border > 1 else "flat",
                    bd=border,
                    cursor="hand2",
                )
                cell.grid(row=y, column=x, sticky="nsew", padx=2, pady=2)
                cell.bind("<Button-1>", lambda _, cx=x, cy=y: self.start_drag(cx, cy))
                row_buttons.append(cell)
            self.buttons.append(row_buttons)
        self.info.config(text=f"Счет: {self.score}/{MATCH_WIN_SCORE} | Зажми ЛКМ и проведи на соседнюю клетку | R, К или Р: заново")

    def update_selection_visual(self):
        for y, row in enumerate(self.buttons):
            for x, cell in enumerate(row):
                cell.config(relief="sunken" if self.selected == (x, y) else "flat", bd=3 if self.selected == (x, y) else 1)

    def start_drag(self, x, y):
        if self.animating or self.won:
            return
        self.dragging = True
        self.drag_target = None
        if self.selected is None:
            self.selected = (x, y)
            self.update_selection_visual()
            return
        first_x, first_y = self.selected
        if abs(first_x - x) + abs(first_y - y) != 1:
            self.selected = (x, y)
            self.update_selection_visual()
            return
        self.drag_target = (x, y)
        self.update_selection_visual()

    def drag_motion_event(self, event):
        if not self.dragging or self.animating or self.selected is None:
            return
        board_x = event.x_root - self.board.winfo_rootx()
        board_y = event.y_root - self.board.winfo_rooty()
        cell_width = self.board.winfo_width() / self.COLS
        cell_height = self.board.winfo_height() / self.ROWS
        x = int(board_x / cell_width) if cell_width else -1
        y = int(board_y / cell_height) if cell_height else -1
        if 0 <= x < self.COLS and 0 <= y < self.ROWS:
            first_x, first_y = self.selected
            if abs(first_x - x) + abs(first_y - y) == 1:
                self.drag_target = (x, y)
            else:
                self.drag_target = None
            self.update_selection_visual()

    def end_drag(self, _):
        if self.dragging and self.drag_target is not None and not self.animating:
            target_x, target_y = self.drag_target
            self.swap_selected(target_x, target_y)
        self.dragging = False
        self.drag_target = None

    def select(self, x, y):
        self.start_drag(x, y)
        self.end_drag(None)

    def swap_selected(self, x, y):
        first_x, first_y = self.selected
        self.selected = None
        self.tiles[first_y][first_x], self.tiles[y][x] = self.tiles[y][x], self.tiles[first_y][first_x]
        matches = self.find_matches()
        if not matches:
            self.tiles[first_y][first_x], self.tiles[y][x] = self.tiles[y][x], self.tiles[first_y][first_x]
        else:
            self.animating = True
            self.flash_cells = matches
            self.flash_visible = True
            self.update_flash_visual()
            self.animation_job = self.parent.after(220, self.animate_match)
            return
        self.draw()

    def animate_match(self):
        self.finish_match()

    def update_flash_visual(self):
        for y, row in enumerate(self.buttons):
            for x, cell in enumerate(row):
                if (x, y) in self.flash_cells:
                    color = "#e8f0fe"
                    cell.config(bg=color, activebackground=color)

    def finish_match(self):
        self.flash_cells = set()
        self.flash_visible = False
        self.resolve_matches()
        self.animating = False
        self.animation_job = None
        if self.score >= MATCH_WIN_SCORE and not self.won:
            self.won = True
            self.info.config(text=f"ПОБЕДА! {MATCH_WIN_SCORE} очков | R, К или Р: заново")
            self.victory = VictoryAnimation(self.parent)
        self.draw()

    def resolve_matches(self):
        while True:
            matches = self.find_matches()
            if not matches:
                return
            self.score += len(matches) * 10
            for x in range(self.COLS):
                remaining = [
                    self.tiles[y][x]
                    for y in range(self.ROWS - 1, -1, -1)
                    if (x, y) not in matches
                ]
                while len(remaining) < self.ROWS:
                    remaining.append(random.randrange(len(self.COLORS)))
                for y in range(self.ROWS):
                    self.tiles[y][x] = remaining[self.ROWS - 1 - y]

    def find_matches(self):
        matches = set()
        for y in range(self.ROWS):
            for x in range(self.COLS - 2):
                if self.tiles[y][x] == self.tiles[y][x + 1] == self.tiles[y][x + 2]:
                    matches.update((x + offset, y) for offset in range(3))
        for x in range(self.COLS):
            for y in range(self.ROWS - 2):
                if self.tiles[y][x] == self.tiles[y + 1][x] == self.tiles[y + 2][x]:
                    matches.update((x, y + offset) for offset in range(3))
        return matches


class TwentyFortyEightGame:
    SIZES = {"Малое 3 x 3": 3, "Классическое 4 x 4": 4, "Большое 5 x 5": 5}
    TILE_COLORS = {
        0: ("#dfe3e8", "#5f6368"),
        2: ("#f1f3f4", "#202124"),
        4: ("#e8f0fe", "#202124"),
        8: ("#fbbc04", "#ffffff"),
        16: ("#f9ab00", "#ffffff"),
        32: ("#ea4335", "#ffffff"),
        64: ("#d93025", "#ffffff"),
        128: ("#34a853", "#ffffff"),
        256: ("#188038", "#ffffff"),
        512: ("#4285f4", "#ffffff"),
        1024: ("#1967d2", "#ffffff"),
        2048: ("#7b1fa2", "#ffffff"),
    }

    def __init__(self, parent):
        self.parent = parent
        controls = tk.Frame(parent, bg=BACKGROUND)
        controls.pack(pady=(0, 8))
        self.size_name = tk.StringVar(value="Классическое 4 x 4")
        size_menu = tk.OptionMenu(controls, self.size_name, *self.SIZES, command=lambda _: self.reset())
        size_menu.config(
            bg=BLUE,
            fg=TEXT_COLOR,
            activebackground="#3367d6",
            highlightthickness=0,
            font=("Segoe UI", 10),
        )
        size_menu.pack(side="left", padx=5)
        make_button(controls, "Новая игра", self.reset).pack(side="left", padx=5)
        self.info = tk.Label(parent, bg=BACKGROUND, fg=MUTED_COLOR, font=("Segoe UI", 11, "bold"))
        self.info.pack(pady=(0, 8))
        self.board = tk.Frame(parent, bg=BACKGROUND)
        self.board.pack(fill="both", expand=True)
        self.board.bind("<Configure>", lambda _: self.update_font())
        self.reset()

    def reset(self):
        if hasattr(self, "victory"):
            self.victory.destroy()
        self.size = self.SIZES[self.size_name.get()]
        self.score = 0
        self.finished = False
        self.won = False
        self.tiles = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.add_tile()
        self.add_tile()
        self.draw()

    def add_tile(self):
        empty = [
            (x, y)
            for y in range(self.size)
            for x in range(self.size)
            if self.tiles[y][x] == 0
        ]
        if empty:
            x, y = random.choice(empty)
            self.tiles[y][x] = 4 if random.random() < 0.1 else 2

    def handle_key(self, event):
        if is_restart_key(event):
            self.reset()
            return
        directions = {
            "left": "left", "a": "left", "ф": "left",
            "right": "right", "d": "right", "в": "right",
            "up": "up", "w": "up", "ц": "up",
            "down": "down", "s": "down", "ы": "down",
        }
        direction = directions.get(event.keysym.lower())
        if direction and not self.finished:
            self.move(direction)

    def slide_line(self, line):
        compact = [value for value in line if value]
        result = []
        index = 0
        while index < len(compact):
            if index + 1 < len(compact) and compact[index] == compact[index + 1]:
                merged = compact[index] * 2
                result.append(merged)
                self.score += merged
                index += 2
            else:
                result.append(compact[index])
                index += 1
        return result + [0] * (self.size - len(result))

    def move(self, direction):
        old_tiles = [row[:] for row in self.tiles]
        if direction in ("left", "right"):
            for y in range(self.size):
                line = self.tiles[y][:]
                if direction == "right":
                    line.reverse()
                line = self.slide_line(line)
                if direction == "right":
                    line.reverse()
                self.tiles[y] = line
        else:
            for x in range(self.size):
                line = [self.tiles[y][x] for y in range(self.size)]
                if direction == "down":
                    line.reverse()
                line = self.slide_line(line)
                if direction == "down":
                    line.reverse()
                for y in range(self.size):
                    self.tiles[y][x] = line[y]
        if self.tiles == old_tiles:
            return
        self.add_tile()
        if any(2048 in row for row in self.tiles) and not self.won:
            self.won = True
            self.victory = VictoryAnimation(self.parent)
        if not self.has_moves():
            self.finished = True
        self.draw()

    def has_moves(self):
        if any(0 in row for row in self.tiles):
            return True
        for y in range(self.size):
            for x in range(self.size):
                if x < self.size - 1 and self.tiles[y][x] == self.tiles[y][x + 1]:
                    return True
                if y < self.size - 1 and self.tiles[y][x] == self.tiles[y + 1][x]:
                    return True
        return False

    def draw(self):
        for child in self.board.winfo_children():
            child.destroy()
        self.buttons = []
        for column in range(self.size):
            self.board.grid_columnconfigure(column, weight=1, uniform="2048-column")
        for row in range(self.size):
            self.board.grid_rowconfigure(row, weight=1, uniform="2048-row")
        for y in range(self.size):
            row_buttons = []
            for x in range(self.size):
                value = self.tiles[y][x]
                background, foreground = self.TILE_COLORS.get(value, ("#7b1fa2", "#ffffff"))
                tile = tk.Label(
                    self.board,
                    text=str(value) if value else "",
                    bg=background,
                    fg=foreground,
                    relief="flat",
                    bd=0,
                    font=("Segoe UI", 20, "bold"),
                )
                tile.grid(row=y, column=x, sticky="nsew", padx=4, pady=4)
                row_buttons.append(tile)
            self.buttons.append(row_buttons)
        if self.won:
            status = f"Победа! Счет: {self.score} | Продолжай или R, К, Р: заново"
        elif self.finished:
            status = f"Игра окончена | Счет: {self.score} | R, К, Р: заново"
        else:
            status = f"Счет: {self.score} | Стрелки/WASD | R, К или Р: заново"
        self.info.config(text=status)
        self.update_font()

    def update_font(self):
        if not getattr(self, "buttons", None):
            return
        font_size = max(14, min(52, int(min(self.board.winfo_width(), self.board.winfo_height()) / 12)))
        for row in self.buttons:
            for tile in row:
                tile.config(font=("Segoe UI", font_size, "bold"))

    def destroy(self):
        if hasattr(self, "victory"):
            self.victory.destroy()


class PacmanGame:
    MAP = (
        "#################",
        "#........#......#",
        "#.###.##.#.##.#.#",
        "#.#.....#....#..#",
        "#.###.#####.###.#",
        "#.....#...#.....#",
        "#####.#.#.#.#####",
        "#.......#.......#",
        "#.#####.#.#####.#",
        "#.#...........#.#",
        "#.###.#####.###.#",
        "#.....#...#.....#",
        "#.#####.#.#####.#",
        "#...............#",
        "#################",
    )
    TICK_MS = 150
    GHOST_COLORS = ("#ea4335", "#4285f4", "#fbbc04")

    def __init__(self, parent):
        self.parent = parent
        self.info = tk.Label(parent, bg=BACKGROUND, fg=MUTED_COLOR, font=("Segoe UI", 11, "bold"))
        self.info.pack(pady=(0, 8))
        self.canvas = tk.Canvas(parent, bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14)
        self.canvas.bind("<Configure>", lambda _: self.draw())
        self.reset()

    def reset(self):
        if hasattr(self, "tick_job"):
            self.parent.after_cancel(self.tick_job)
        if hasattr(self, "victory"):
            self.victory.destroy()
        self.rows = len(self.MAP)
        self.columns = len(self.MAP[0])
        self.walls = {
            (x, y)
            for y, row in enumerate(self.MAP)
            for x, value in enumerate(row)
            if value == "#"
        }
        self.pellets = {
            (x, y)
            for y, row in enumerate(self.MAP)
            for x, value in enumerate(row)
            if value == "."
        }
        self.player = (1, 1)
        self.direction = (0, 0)
        self.next_direction = self.direction
        self.ghosts = [(15, 1), (8, 7), (1, 13)]
        self.score = 0
        self.finished = False
        self.won = False
        self.info.config(text=f"Счет: {self.score} | Точек: {len(self.pellets)} | Стрелки/WASD | R, К или Р: заново")
        self.draw()
        self.schedule_tick()

    def handle_key(self, event):
        if is_restart_key(event):
            self.reset()
            return
        directions = {
            "up": (0, -1), "w": (0, -1), "ц": (0, -1),
            "down": (0, 1), "s": (0, 1), "ы": (0, 1),
            "left": (-1, 0), "a": (-1, 0), "ф": (-1, 0),
            "right": (1, 0), "d": (1, 0), "в": (1, 0),
        }
        direction = directions.get(event.keysym.lower())
        if direction:
            self.next_direction = direction

    def schedule_tick(self):
        self.tick_job = self.parent.after(self.TICK_MS, self.tick)

    def destroy(self):
        if hasattr(self, "tick_job"):
            self.parent.after_cancel(self.tick_job)
        if hasattr(self, "victory"):
            self.victory.destroy()

    def can_move(self, position, direction):
        x, y = position
        next_position = (x + direction[0], y + direction[1])
        return next_position not in self.walls

    def tick(self):
        if self.finished:
            return
        if self.can_move(self.player, self.next_direction):
            self.direction = self.next_direction
        if self.can_move(self.player, self.direction):
            self.player = (self.player[0] + self.direction[0], self.player[1] + self.direction[1])
        if self.player in self.pellets:
            self.pellets.remove(self.player)
            self.score += 10
        moved_ghosts = []
        for ghost in self.ghosts:
            options = [
                direction
                for direction in ((0, -1), (0, 1), (-1, 0), (1, 0))
                if self.can_move(ghost, direction)
            ]
            direction = random.choice(options)
            moved_ghosts.append((ghost[0] + direction[0], ghost[1] + direction[1]))
        self.ghosts = moved_ghosts
        if self.player in self.ghosts:
            self.finished = True
            self.info.config(text=f"Пойман! Счет: {self.score} | R, К или Р: заново")
        elif not self.pellets:
            self.finished = True
            self.won = True
            self.info.config(text=f"ПОБЕДА! Счет: {self.score} | R, К или Р: заново")
            self.victory = VictoryAnimation(self.parent)
        else:
            self.info.config(text=f"Счет: {self.score} | Точек: {len(self.pellets)} | Стрелки/WASD | R, К или Р: заново")
        self.draw()
        if not self.finished:
            self.schedule_tick()

    def draw(self):
        self.canvas.delete("all")
        canvas_width = max(self.canvas.winfo_width(), 510)
        canvas_height = max(self.canvas.winfo_height(), 450)
        cell_size = min(canvas_width / self.columns, canvas_height / self.rows)
        board_width = cell_size * self.columns
        board_height = cell_size * self.rows
        offset_x = (canvas_width - board_width) / 2
        offset_y = (canvas_height - board_height) / 2
        self.canvas.create_rectangle(offset_x, offset_y, offset_x + board_width, offset_y + board_height, fill="#101820", outline="")
        for x, y in self.walls:
            self.canvas.create_rectangle(offset_x + x * cell_size, offset_y + y * cell_size, offset_x + (x + 1) * cell_size, offset_y + (y + 1) * cell_size, fill="#4285f4", outline=BACKGROUND)
        for x, y in self.pellets:
            radius = max(2, cell_size * 0.09)
            center_x = offset_x + (x + 0.5) * cell_size
            center_y = offset_y + (y + 0.5) * cell_size
            self.canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, fill="#ffffff", outline="")
        player_x, player_y = self.player
        start = {(1, 0): 25, (-1, 0): 205, (0, -1): 115, (0, 1): 295}.get(self.direction, 25)
        self.canvas.create_arc(offset_x + player_x * cell_size + 2, offset_y + player_y * cell_size + 2, offset_x + (player_x + 1) * cell_size - 2, offset_y + (player_y + 1) * cell_size - 2, start=start, extent=300, fill="#fbbc04", outline="")
        for index, (ghost_x, ghost_y) in enumerate(self.ghosts):
            color = self.GHOST_COLORS[index]
            self.canvas.create_oval(offset_x + ghost_x * cell_size + 3, offset_y + ghost_y * cell_size + 3, offset_x + (ghost_x + 1) * cell_size - 3, offset_y + (ghost_y + 1) * cell_size - 3, fill=color, outline="")
            eye_size = max(2, cell_size * 0.09)
            for eye_offset in (0.35, 0.65):
                eye_x = offset_x + (ghost_x + eye_offset) * cell_size
                eye_y = offset_y + (ghost_y + 0.43) * cell_size
                self.canvas.create_oval(eye_x - eye_size, eye_y - eye_size, eye_x + eye_size, eye_y + eye_size, fill="#ffffff", outline="")


class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Color Arcade")
        self.root.configure(bg=BACKGROUND)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(SCREEN_WIDTH, screen_width)
        window_height = min(SCREEN_HEIGHT, screen_height)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(True, True)
        self.root.bind("<F11>", lambda _: self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen")))
        self.root.bind("<Escape>", lambda _: self.root.attributes("-fullscreen", False))
        self.root.bind("<KeyPress>", self.handle_key)
        self.root.bind("<B1-Motion>", self.handle_drag_motion)
        self.root.bind("<ButtonRelease-1>", self.handle_drag_release)
        header = tk.Frame(root, bg=BACKGROUND)
        header.pack(fill="x", padx=14, pady=(14, 8))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text="COLOR ARCADE", bg=BACKGROUND, fg=TEXT_COLOR, font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")
        navigation = tk.Frame(header, bg=BACKGROUND)
        navigation.grid(row=0, column=1, sticky="e")
        make_button(navigation, "Змейка", lambda: self.show("snake")).pack(side="left", padx=2)
        make_button(navigation, "Сапёр", lambda: self.show("mines")).pack(side="left", padx=2)
        make_button(navigation, "Три в ряд", lambda: self.show("match")).pack(side="left", padx=2)
        make_button(navigation, "2048", lambda: self.show("2048")).pack(side="left", padx=2)
        make_button(navigation, "Pac-Man", lambda: self.show("pacman")).pack(side="left", padx=2)
        self.theme_button = make_button(navigation, "Тёмная тема", self.toggle_theme)
        self.theme_button.pack(side="left", padx=2)
        self.header = header
        self.navigation = navigation
        self.content = tk.Frame(root, bg=BACKGROUND)
        self.content.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.theme_name = "light"
        self.active_game = "snake"
        self.show("snake")

    def handle_key(self, event):
        if hasattr(self, "current") and hasattr(self.current, "handle_key"):
            self.current.handle_key(event)

    def handle_drag_motion(self, event):
        if hasattr(self, "current") and hasattr(self.current, "drag_motion_event"):
            self.current.drag_motion_event(event)

    def handle_drag_release(self, event):
        if hasattr(self, "current") and hasattr(self.current, "end_drag"):
            self.current.end_drag(event)

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        set_theme(self.theme_name)
        self.root.configure(bg=BACKGROUND)
        self.header.configure(bg=BACKGROUND)
        self.navigation.configure(bg=BACKGROUND)
        self.content.configure(bg=BACKGROUND)
        for child in self.navigation.winfo_children():
            child.configure(
                bg=PANEL,
                fg=TEXT_COLOR,
                activebackground=GRID_COLOR,
                activeforeground=TEXT_COLOR,
            )
        self.theme_button.configure(
            text="Светлая тема" if self.theme_name == "dark" else "Тёмная тема"
        )
        self.show(self.active_game)

    def show(self, game):
        self.active_game = game
        if hasattr(self, "current") and hasattr(self.current, "destroy"):
            self.current.destroy()
        for child in self.content.winfo_children():
            child.destroy()
        if game == "snake":
            self.current = SnakeGame(self.content)
        elif game == "mines":
            self.current = MinesweeperGame(self.content)
        elif game == "2048":
            self.current = TwentyFortyEightGame(self.content)
        elif game == "pacman":
            self.current = PacmanGame(self.content)
        else:
            self.current = MatchThreeGame(self.content)
        self.root.focus_force()


if __name__ == "__main__":
    window = tk.Tk()
    GameApp(window)
    window.mainloop()
