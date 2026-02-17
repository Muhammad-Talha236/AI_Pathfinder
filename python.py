import tkinter as tk
from tkinter import ttk, messagebox
import time
import heapq

# --- Configuration & Styling ---
GRID_SIZE = 12
CELL_SIZE = 45
DELAY = 0.07

COLORS = {
    "bg": "#1e1e2e",        # Dark background
    "sidebar": "#2b2b3b",   # Sidebar background
    "grid_line": "#444454",
    "empty": "#313244",     # Dark cell
    "wall": "#f38ba8",      # Soft Red
    "start": "#a6e3a1",     # Soft Green
    "target": "#89b4fa",    # Soft Blue
    "frontier": "#f9e2af",  # Yellowish
    "path": "#cba6f7",      # Lavender/Purple
    "text": "#cdd6f4"
}

MOVES = [(-1, 0), (0, 1), (1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]

class Node:
    def __init__(self, r, c, parent=None, cost=0):
        self.r, self.c = r, c
        self.parent = parent
        self.cost = cost
    
    def __lt__(self, other): # For Priority Queue (UCS)
        return self.cost < other.cost

class ModernPathfinder:
    def __init__(self, root):
        self.root = root
        self.root.title("A.I. Pathfinding Visualizer")
        self.root.configure(bg=COLORS["bg"])
        
        self.grid_data = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.start_pos = None
        self.target_pos = None
        self.is_running = False
        self.mode = "Wall"
        
        self.setup_layout()
        self.create_grid()

    def setup_layout(self):
        # Sidebar for controls
        self.sidebar = tk.Frame(self.root, bg=COLORS["sidebar"], width=200, padx=20, pady=20)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        title = tk.Label(self.sidebar, text="CONTROLS", fg=COLORS["text"], 
                         bg=COLORS["sidebar"], font=("Verdana", 14, "bold"))
        title.pack(pady=(0, 20))

        # Algorithm Selection
        tk.Label(self.sidebar, text="Algorithm", fg=COLORS["text"], bg=COLORS["sidebar"]).pack(anchor="w")
        self.algo_var = tk.StringVar(value="BFS")
        style = ttk.Style()
        style.theme_use('clam')
        combo = ttk.Combobox(self.sidebar, textvariable=self.algo_var, state="readonly",
                             values=("BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional"))
        combo.pack(fill=tk.X, pady=(0, 20))

        # Control Buttons
        btn_style = {"font": ("Verdana", 9), "relief": "flat", "pady": 8, "cursor": "hand2"}
        
        tk.Button(self.sidebar, text="SET START", bg=COLORS["start"], fg="#111",
                  command=lambda: self.set_mode("S"), **btn_style).pack(fill=tk.X, pady=4)
        
        tk.Button(self.sidebar, text="SET TARGET", bg=COLORS["target"], fg="#111",
                  command=lambda: self.set_mode("T"), **btn_style).pack(fill=tk.X, pady=4)
        
        tk.Button(self.sidebar, text="BUILD WALLS", bg=COLORS["wall"], fg="#111",
                  command=lambda: self.set_mode("Wall"), **btn_style).pack(fill=tk.X, pady=4)

        # Action Buttons
        tk.Frame(self.sidebar, height=40, bg=COLORS["sidebar"]).pack()
        
        tk.Button(self.sidebar, text="START SEARCH", bg="#fab387", font=("Verdana", 10, "bold"),
                  command=self.execute_search, relief="flat", pady=12).pack(fill=tk.X, pady=5)
        
        tk.Button(self.sidebar, text="RESET", bg="#585b70", fg="white",
                  command=self.reset_all, **btn_style).pack(fill=tk.X, pady=5)

        self.status_var = tk.StringVar(value="Status: Ready")
        tk.Label(self.sidebar, textvariable=self.status_var, fg="#9399b2", 
                 bg=COLORS["sidebar"], wraplength=150, pady=20).pack()

        # Canvas Area
        self.canvas = tk.Canvas(self.root, width=GRID_SIZE*CELL_SIZE, height=GRID_SIZE*CELL_SIZE,
                                bg=COLORS["bg"], highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, padx=40, pady=40)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-1>", self.paint)

    def create_grid(self):
        self.cells = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x1, y1 = c * CELL_SIZE, r * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS["empty"], 
                                                     outline=COLORS["grid_line"])
                self.cells[(r, c)] = rect

    def set_mode(self, mode):
        self.mode = mode
        self.status_var.set(f"Mode: {mode}")

    def paint(self, event):
        if self.is_running: return
        c, r = event.x // CELL_SIZE, event.y // CELL_SIZE
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            self.update_cell(r, c)

    def update_cell(self, r, c):
        if self.mode == "S":
            if self.start_pos: self.draw_cell(self.start_pos[0], self.start_pos[1], COLORS["empty"])
            self.start_pos = (r, c)
            self.draw_cell(r, c, COLORS["start"])
        elif self.mode == "T":
            if self.target_pos: self.draw_cell(self.target_pos[0], self.target_pos[1], COLORS["empty"])
            self.target_pos = (r, c)
            self.draw_cell(r, c, COLORS["target"])
        elif self.mode == "Wall":
            if (r, c) not in [self.start_pos, self.target_pos]:
                self.grid_data[r][c] = -1
                self.draw_cell(r, c, COLORS["wall"])

    def draw_cell(self, r, c, color):
        self.canvas.itemconfig(self.cells[(r, c)], fill=color)

    def reset_all(self):
        self.is_running = False
        self.grid_data = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.start_pos = self.target_pos = None
        self.status_var.set("Status: Ready")
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.draw_cell(r, c, COLORS["empty"])

    def get_neighbors(self, node):
        res = []
        for dr, dc in MOVES:
            nr, nc = node.r + dr, node.c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and self.grid_data[nr][nc] != -1:
                res.append(Node(nr, nc, node, node.cost + 1))
        return res

    def animate(self, node):
        if (node.r, node.c) not in [self.start_pos, self.target_pos]:
            self.draw_cell(node.r, node.c, COLORS["frontier"])
            self.root.update()
            time.sleep(DELAY)

    def execute_search(self):
        if not self.start_pos or not self.target_pos:
            messagebox.showwarning("Setup", "Select Start and Target first!")
            return
        
        self.is_running = True
        self.status_var.set("Searching...")
        algo = self.algo_var.get()
        
        found_node = None
        if algo == "BFS": found_node = self.algo_bfs()
        elif algo == "DFS": found_node = self.algo_dfs()
        elif algo == "UCS": found_node = self.algo_ucs()
        elif algo == "IDDFS": found_node = self.algo_iddfs()
        
        if found_node:
            self.draw_path(found_node)
            self.status_var.set("Path Found!")
        else:
            self.status_var.set("No Path Found.")
        self.is_running = False

    def algo_bfs(self):
        queue = [Node(*self.start_pos)]
        visited = {self.start_pos}
        while queue:
            curr = queue.pop(0)
            if (curr.r, curr.c) == self.target_pos: return curr
            self.animate(curr)
            for n in self.get_neighbors(curr):
                if (n.r, n.c) not in visited:
                    visited.add((n.r, n.c))
                    queue.append(n)
        return None

    def algo_ucs(self):
        pq = [(0, Node(*self.start_pos))]
        visited = {}
        while pq:
            cost, curr = heapq.heappop(pq)
            if (curr.r, curr.c) == self.target_pos: return curr
            if (curr.r, curr.c) in visited and visited[(curr.r, curr.c)] <= cost: continue
            visited[(curr.r, curr.c)] = cost
            self.animate(curr)
            for n in self.get_neighbors(curr):
                heapq.heappush(pq, (n.cost, n))
        return None

    def draw_path(self, node):
        curr = node.parent
        while curr and (curr.r, curr.c) != self.start_pos:
            self.draw_cell(curr.r, curr.c, COLORS["path"])
            curr = curr.parent
            self.root.update()
            time.sleep(DELAY)

if __name__ == "__main__":
    win = tk.Tk()
    app = ModernPathfinder(win)
    win.mainloop()