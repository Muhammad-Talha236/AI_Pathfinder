import tkinter as tk
from tkinter import messagebox, ttk
import time
import random
import heapq
from queue import Queue

# --- Constants ---
ROWS, COLS = 10, 10
CELL_SIZE = 50
DELAY = 0.05  
DYNAMIC_OBS_PROB = 0.05  

DLS_LIMIT = 5
IDDFS_MAX_DEPTH = 15

# Colors
EMPTY_COLOR = "white"
WALL_COLOR = "black"
START_COLOR = "green"
TARGET_COLOR = "red"
FRONTIER_COLOR = "yellow"
EXPLORED_COLOR = "lightblue"
PATH_COLOR = "orange"
OBSTACLE_COLOR = "grey"

SIDEBAR_BG = "#f0f0f0"
BUTTON_COLOR = "#4CAF50"
BUTTON_TEXT_COLOR = "white"
LABEL_COLOR = "#2196F3"

# Movement Logic
MOVES = [(-1, 0), (0, 1), (1, 0), (0, -1), (1, 1), (-1, -1)]

# --- Logic Classes ---
class Node:
    def __init__(self, r, c, parent=None, cost=0):
        self.r = r
        self.c = c
        self.parent = parent
        self.cost = cost

    def get_pos(self):
        return (self.r, self.c)

class Cell:
    def __init__(self, row, col, canvas_id):
        self.row = row
        self.col = col
        self.canvas_id = canvas_id
        self.type = "empty" 

# --- Main App ---
class GridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Pathfinder - Merged Logic")
        self.mode = "wall"
        self.start_pos = None
        self.target_pos = None
        self.grid = []
        self.algorithm = tk.StringVar(value="BFS")
        self.dynamic_obstacles = tk.BooleanVar(value=False)
        self.stop_flag = False
        self.visit_count = 0

        # Canvas
        self.canvas = tk.Canvas(root, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE, bg="white")
        self.canvas.grid(row=0, column=0, rowspan=10, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.cell_clicked)
        self.canvas.bind("<B1-Motion>", self.cell_clicked)

        # Sidebar
        sidebar = tk.Frame(root, bg=SIDEBAR_BG)
        sidebar.grid(row=0, column=1, sticky="ns", padx=5, pady=5)
        
        tk.Label(sidebar, text="Node Controls", bg=SIDEBAR_BG, font=("Arial", 10, "bold")).pack(pady=5)
        tk.Button(sidebar, text="Set Start Node", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("start")).pack(fill="x", pady=2)
        tk.Button(sidebar, text="Set Target Node", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("target")).pack(fill="x", pady=2)
        tk.Button(sidebar, text="Place/Remove Wall", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("wall")).pack(fill="x", pady=2)
        tk.Button(sidebar, text="Clear Cell", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("clear")).pack(fill="x", pady=2)
        
        tk.Frame(sidebar, height=10, bg=SIDEBAR_BG).pack()
        
        tk.Button(sidebar, text="Clear Grid", bg="#9E9E9E", fg="white",
                  command=self.clear_grid).pack(fill="x", pady=2)
        tk.Button(sidebar, text="Start Search", bg="#f44336", fg=BUTTON_TEXT_COLOR,
                  command=self.start_search).pack(fill="x", pady=5)
        tk.Button(sidebar, text="Stop Search", bg="#FF9800", fg=BUTTON_TEXT_COLOR,
                  command=self.stop_search).pack(fill="x", pady=2)
        
        tk.Checkbutton(sidebar, text="Dynamic Obstacles", variable=self.dynamic_obstacles,
                       bg=SIDEBAR_BG).pack(pady=5)
        
        tk.Label(sidebar, text="Select Algorithm:", bg=SIDEBAR_BG, fg=LABEL_COLOR).pack(pady=5)
        self.algo_menu = ttk.Combobox(sidebar, textvariable=self.algorithm, state="readonly")
        self.algo_menu['values'] = ("BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional")
        self.algo_menu.pack(fill="x", padx=5)

        self.create_grid()

    def create_grid(self):
        for row in range(ROWS):
            row_cells = []
            for col in range(COLS):
                x1, y1 = col*CELL_SIZE, row*CELL_SIZE
                x2, y2 = x1+CELL_SIZE, y1+CELL_SIZE
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=EMPTY_COLOR, outline="gray")
                self.canvas.create_text(x1+CELL_SIZE//2, y1+CELL_SIZE//2, text="", fill="black", tags=f"text_{row}_{col}")
                row_cells.append(Cell(row, col, rect))
            self.grid.append(row_cells)

    def set_mode(self, mode):
        self.mode = mode

    def cell_clicked(self, event):
        col, row = event.x // CELL_SIZE, event.y // CELL_SIZE
        if not (0 <= row < ROWS and 0 <= col < COLS): return
        
        cell = self.grid[row][col]
        if self.mode == "start":
            if self.start_pos: self.update_cell_type(self.start_pos[0], self.start_pos[1], "empty")
            self.start_pos = (row, col)
            self.update_cell_type(row, col, "start")
        elif self.mode == "target":
            if self.target_pos: self.update_cell_type(self.target_pos[0], self.target_pos[1], "empty")
            self.target_pos = (row, col)
            self.update_cell_type(row, col, "target")
        elif self.mode == "wall":
            if (row, col) not in (self.start_pos, self.target_pos):
                self.update_cell_type(row, col, "wall")
        elif self.mode == "clear":
            if (row, col) == self.start_pos: self.start_pos = None
            if (row, col) == self.target_pos: self.target_pos = None
            self.update_cell_type(row, col, "empty")

    def update_cell_type(self, r, c, type_name):
        self.grid[r][c].type = type_name
        self.update_cell_color(r, c)

    def update_cell_color(self, row, col, number=None):
        cell = self.grid[row][col]
        colors = {
            "empty": EMPTY_COLOR, "wall": WALL_COLOR, "start": START_COLOR,
            "target": TARGET_COLOR, "explored": EXPLORED_COLOR, 
            "frontier": FRONTIER_COLOR, "path": PATH_COLOR, "obstacle": OBSTACLE_COLOR
        }
        color = colors.get(cell.type, EMPTY_COLOR)
        self.canvas.itemconfig(cell.canvas_id, fill=color)
        
        self.canvas.delete(f"text_{row}_{col}")
        if number is not None:
            self.canvas.create_text(row*0+col*CELL_SIZE+CELL_SIZE//2, row*CELL_SIZE+CELL_SIZE//2,
                                    text=str(number), fill="black", tags=f"text_{row}_{col}")

    def get_neighbors(self, r, c):
        neighbors = []
        for dr, dc in MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if self.grid[nr][nc].type not in ("wall", "obstacle"):
                    neighbors.append((nr, nc))
        return neighbors

    def spawn_dynamic_obstacle(self):
        if self.dynamic_obstacles.get() and random.random() < DYNAMIC_OBS_PROB:
            empty_cells = [c for r in self.grid for c in r if c.type == "empty"]
            if empty_cells:
                cell = random.choice(empty_cells)
                cell.type = "obstacle"
                self.update_cell_color(cell.row, cell.col)

    def animate_node(self, row, col, explored=True):
        if self.stop_flag: raise StopIteration
        cell = self.grid[row][col]
        if (row, col) != self.start_pos and (row, col) != self.target_pos:
            if explored: cell.type = "explored"
            self.visit_count += 1
            self.update_cell_color(row, col, number=self.visit_count)
        
        self.root.update()
        time.sleep(DELAY)
        self.spawn_dynamic_obstacle()

    def clear_grid(self):
        self.start_pos = self.target_pos = None
        self.stop_flag = True
        for row in self.grid:
            for cell in row:
                cell.type = "empty"
                self.update_cell_color(cell.row, cell.col)

    def clear_path_only(self):
        self.visit_count = 0
        for row in self.grid:
            for cell in row:
                if cell.type in ("explored", "frontier", "path"):
                    cell.type = "empty"
                    self.update_cell_color(cell.row, cell.col)

    def stop_search(self):
        self.stop_flag = True

    def reconstruct_path(self, node):
        curr = node
        while curr:
            r, c = curr.r, curr.c
            if (r, c) != self.start_pos and (r, c) != self.target_pos:
                self.grid[r][c].type = "path"
                self.update_cell_color(r, c)
                self.root.update()
                time.sleep(DELAY)
            curr = curr.parent

    # --- Search Implementations ---
    def start_search(self):
        if not self.start_pos or not self.target_pos:
            messagebox.showwarning("Warning", "Place Start and Target nodes!")
            return
        
        self.clear_path_only()
        self.stop_flag = False
        algo = self.algorithm.get()
        
        try:
            if algo == "BFS": self.run_bfs()
            elif algo == "DFS": self.run_dfs()
            elif algo == "UCS": self.run_ucs()
            elif algo == "DLS": self.run_dls(DLS_LIMIT)
            elif algo == "IDDFS": self.run_iddfs()
            elif algo == "Bidirectional": self.run_bidirectional()
        except StopIteration:
            messagebox.showinfo("Stopped", "Search was cancelled.")

    def run_bfs(self):
        start_node = Node(*self.start_pos)
        q = [start_node]
        visited = {self.start_pos}
        
        while q:
            curr = q.pop(0)
            if (curr.r, curr.c) == self.target_pos:
                self.reconstruct_path(curr.parent)
                return
            
            self.animate_node(curr.r, curr.c)
            for nr, nc in self.get_neighbors(curr.r, curr.c):
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append(Node(nr, nc, curr))

    def run_dfs(self):
        stack = [Node(*self.start_pos)]
        visited = set()
        
        while stack:
            curr = stack.pop()
            if (curr.r, curr.c) == self.target_pos:
                self.reconstruct_path(curr.parent)
                return
            
            if (curr.r, curr.c) not in visited:
                visited.add((curr.r, curr.c))
                self.animate_node(curr.r, curr.c)
                for nr, nc in reversed(self.get_neighbors(curr.r, curr.c)):
                    if (nr, nc) not in visited:
                        stack.append(Node(nr, nc, curr))

    def run_ucs(self):
        pq = []
        start_node = Node(*self.start_pos, cost=0)
        heapq.heappush(pq, (0, id(start_node), start_node))
        visited = {}

        while pq:
            cost, _, curr = heapq.heappop(pq)
            if (curr.r, curr.c) == self.target_pos:
                self.reconstruct_path(curr.parent)
                return

            if (curr.r, curr.c) in visited and visited[(curr.r, curr.c)] <= cost:
                continue
            visited[(curr.r, curr.c)] = cost

            self.animate_node(curr.r, curr.c)
            for nr, nc in self.get_neighbors(curr.r, curr.c):
                new_cost = cost + 1
                neighbor = Node(nr, nc, curr, new_cost)
                heapq.heappush(pq, (new_cost, id(neighbor), neighbor))

    def run_dls(self, limit):
        def dls_rec(curr, l, visited):
            if (curr.r, curr.c) == self.target_pos: return curr
            if l <= 0: return None
            
            visited.add((curr.r, curr.c))
            self.animate_node(curr.r, curr.c)
            
            for nr, nc in self.get_neighbors(curr.r, curr.c):
                if (nr, nc) not in visited:
                    res = dls_rec(Node(nr, nc, curr), l-1, visited)
                    if res: return res
            return None

        result = dls_rec(Node(*self.start_pos), limit, set())
        if result: self.reconstruct_path(result.parent)

    def run_iddfs(self):
        for depth in range(IDDFS_MAX_DEPTH):
            self.clear_path_only()
            res = self.run_dls(depth)
            if res or self.stop_flag: break

    def run_bidirectional(self):
        v1 = {self.start_pos: Node(*self.start_pos)}
        v2 = {self.target_pos: Node(*self.target_pos)}
        q1, q2 = [v1[self.start_pos]], [v2[self.target_pos]]

        while q1 and q2:
            # Forward
            curr_f = q1.pop(0)
            self.animate_node(curr_f.r, curr_f.c)
            if (curr_f.r, curr_f.c) in v2:
                self.merge_bidir(curr_f, v2[(curr_f.r, curr_f.c)])
                return

            for n in self.get_neighbors(curr_f.r, curr_f.c):
                if n not in v1:
                    v1[n] = Node(*n, curr_f)
                    q1.append(v1[n])

            # Backward
            curr_b = q2.pop(0)
            self.animate_node(curr_b.r, curr_b.c)
            if (curr_b.r, curr_b.c) in v1:
                self.merge_bidir(v1[(curr_b.r, curr_b.c)], curr_b)
                return

            for n in self.get_neighbors(curr_b.r, curr_b.c):
                if n not in v2:
                    v2[n] = Node(*n, curr_b)
                    q2.append(v2[n])

    def merge_bidir(self, node_f, node_b):
        self.reconstruct_path(node_f)
        self.reconstruct_path(node_b)

if __name__ == "__main__":
    root = tk.Tk()
    app = GridApp(root)
    root.mainloop()