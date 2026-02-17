"""
AI Pathfinder - Uninformed Search Algorithms Visualizer
Assignment 1 - AI 2002
Using Tkinter (Built-in, No Installation Required!)
Features: Interactive grid, dropdown algorithm selection, dynamic obstacles
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
from collections import deque
from queue import PriorityQueue
import time

# Constants
GRID_SIZE = 10
CELL_SIZE = 60
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800

# Colors
WHITE = "#FFFFFF"
BLACK = "#000000"
RED = "#FF0000"
GREEN = "#00FF00"
BLUE = "#0000FF"
YELLOW = "#FFFF00"
ORANGE = "#FFA500"
CYAN = "#00FFFF"
GRAY = "#808080"
LIGHT_GRAY = "#C8C8C8"
DARK_GREEN = "#006400"
PURPLE = "#800080"

class Node:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.g = float('inf')
        self.h = 0
        self.f = float('inf')
        self.parent = None
        
    def __lt__(self, other):
        return self.f < other.f
    
    def __eq__(self, other):
        return self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))

class GridEnvironment:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.start = None
        self.target = None
        self.obstacles = set()
        self.dynamic_obstacle_prob = 0.03
        
    def is_valid(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols
    
    def is_obstacle(self, row, col):
        return (row, col) in self.obstacles
    
    def add_obstacle(self, row, col):
        if (row, col) != self.start and (row, col) != self.target:
            self.obstacles.add((row, col))
    
    def remove_obstacle(self, row, col):
        self.obstacles.discard((row, col))
    
    def set_start(self, row, col):
        self.start = (row, col)
        self.obstacles.discard((row, col))
    
    def set_target(self, row, col):
        self.target = (row, col)
        self.obstacles.discard((row, col))
    
    def get_neighbors(self, row, col):
        """Returns neighbors in clockwise order with all diagonals"""
        directions = [
            (-1, 0),   # Up
            (-1, 1),   # Top-Right (diagonal)
            (0, 1),    # Right
            (1, 1),    # Bottom-Right (diagonal)
            (1, 0),    # Bottom
            (1, -1),   # Bottom-Left (diagonal)
            (0, -1),   # Left
            (-1, -1),  # Top-Left (diagonal)
        ]
        
        neighbors = []
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.is_valid(new_row, new_col) and not self.is_obstacle(new_row, new_col):
                if dr != 0 and dc != 0:  # Diagonal
                    if not self.is_obstacle(row + dr, col) and not self.is_obstacle(row, col + dc):
                        neighbors.append((new_row, new_col))
                else:
                    neighbors.append((new_row, new_col))
        
        return neighbors
    
    def spawn_dynamic_obstacle(self, frontier, explored):
        """Randomly spawn a dynamic obstacle"""
        if random.random() < self.dynamic_obstacle_prob:
            empty_cells = []
            for r in range(self.rows):
                for c in range(self.cols):
                    if ((r, c) not in self.obstacles and 
                        (r, c) != self.start and 
                        (r, c) != self.target and
                        (r, c) not in frontier and
                        (r, c) not in explored):
                        empty_cells.append((r, c))
            
            if empty_cells:
                obstacle_pos = random.choice(empty_cells)
                self.obstacles.add(obstacle_pos)
                return obstacle_pos
        return None

class PathfindingVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("GOOD PERFORMANCE TIME APP")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        
        self.env = GridEnvironment(GRID_SIZE, GRID_SIZE)
        self.mode = "set_start"
        
        self.searching = False
        self.search_complete = False
        self.frontier_set = set()
        self.explored_set = set()
        self.path = []
        self.dynamic_obstacles = []
        
        self.stats = {
            "nodes_explored": 0,
            "path_length": 0,
            "search_time": 0,
            "algorithm": ""
        }
        
        self.cells = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg=WHITE)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = tk.Frame(main_frame, bg=BLUE, height=60)
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(title_frame, text="GOOD PERFORMANCE TIME APP", 
                              font=("Arial", 20, "bold"), bg=BLUE, fg=WHITE)
        title_label.pack(pady=15)
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg=WHITE)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Grid
        grid_frame = tk.Frame(content_frame, bg="#F5F5F5", padx=30, pady=30)
        grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(grid_frame, width=GRID_SIZE*CELL_SIZE, 
                               height=GRID_SIZE*CELL_SIZE, bg=WHITE, 
                               highlightthickness=2, highlightbackground=BLACK)
        self.canvas.pack()
        
        # Draw initial grid
        self.draw_grid()
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        
        # Right side - Control Panel
        control_frame = tk.Frame(content_frame, bg=WHITE, width=400, padx=20, pady=20)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)
        
        # Title
        tk.Label(control_frame, text="🎯 AI PATHFINDER", font=("Arial", 18, "bold"), 
                bg=WHITE, fg=BLUE).pack(pady=(0, 15))
        
        # Mode display
        self.mode_label = tk.Label(control_frame, text=f"Mode: {self.mode.replace('_', ' ').title()}", 
                                  font=("Arial", 11), bg=WHITE, fg=PURPLE)
        self.mode_label.pack(pady=5)
        
        # Algorithm selection
        tk.Label(control_frame, text="Select Algorithm:", font=("Arial", 11, "bold"), 
                bg=WHITE).pack(pady=(15, 5))
        
        self.algorithm_var = tk.StringVar(value="BFS")
        algorithm_dropdown = ttk.Combobox(control_frame, textvariable=self.algorithm_var,
                                         values=["BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional"],
                                         state="readonly", font=("Arial", 11), width=30)
        algorithm_dropdown.pack(pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(control_frame, bg=WHITE)
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="Start Search", bg=GREEN, fg=WHITE,
                 font=("Arial", 11, "bold"), width=15, height=2,
                 command=self.start_search).grid(row=0, column=0, padx=5, pady=5)
        
        tk.Button(button_frame, text="Clear Path", bg=ORANGE, fg=WHITE,
                 font=("Arial", 11, "bold"), width=15, height=2,
                 command=self.clear_search_data).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(button_frame, text="Reset Grid", bg=RED, fg=WHITE,
                 font=("Arial", 11, "bold"), width=32, height=2,
                 command=self.reset_grid).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Mode buttons
        tk.Label(control_frame, text="Set Mode:", font=("Arial", 11, "bold"), 
                bg=WHITE).pack(pady=(10, 5))
        
        mode_frame = tk.Frame(control_frame, bg=WHITE)
        mode_frame.pack()
        
        tk.Button(mode_frame, text="1: Start Point", bg=GREEN, fg=WHITE,
                 font=("Arial", 9), width=15,
                 command=lambda: self.set_mode("set_start")).grid(row=0, column=0, padx=3, pady=3)
        
        tk.Button(mode_frame, text="2: Target Point", bg=RED, fg=WHITE,
                 font=("Arial", 9), width=15,
                 command=lambda: self.set_mode("set_target")).grid(row=0, column=1, padx=3, pady=3)
        
        tk.Button(mode_frame, text="3: Add Obstacles", bg=BLACK, fg=WHITE,
                 font=("Arial", 9), width=15,
                 command=lambda: self.set_mode("add_obstacle")).grid(row=1, column=0, padx=3, pady=3)
        
        tk.Button(mode_frame, text="4: Remove Obstacles", bg=GRAY, fg=WHITE,
                 font=("Arial", 9), width=15,
                 command=lambda: self.set_mode("remove_obstacle")).grid(row=1, column=1, padx=3, pady=3)
        
        # Legend
        tk.Label(control_frame, text="Legend:", font=("Arial", 11, "bold"), 
                bg=WHITE).pack(pady=(15, 5))
        
        legend_frame = tk.Frame(control_frame, bg=WHITE)
        legend_frame.pack()
        
        legends = [
            (GREEN, "Start"), (RED, "Target"), (BLACK, "Static Obstacle"),
            (ORANGE, "Dynamic Obstacle"), (CYAN, "Frontier"), 
            (LIGHT_GRAY, "Explored"), (YELLOW, "Path")
        ]
        
        for i, (color, text) in enumerate(legends):
            frame = tk.Frame(legend_frame, bg=WHITE)
            frame.grid(row=i, column=0, sticky="w", pady=2)
            
            color_box = tk.Canvas(frame, width=25, height=25, bg=color, 
                                highlightthickness=1, highlightbackground=BLACK)
            color_box.pack(side=tk.LEFT, padx=(0, 8))
            
            tk.Label(frame, text=text, font=("Arial", 9), bg=WHITE).pack(side=tk.LEFT)
        
        # Statistics
        self.stats_frame = tk.LabelFrame(control_frame, text="Statistics", 
                                        font=("Arial", 11, "bold"), bg=WHITE)
        self.stats_frame.pack(pady=15, fill=tk.X)
        
        self.stats_label = tk.Label(self.stats_frame, text="Run a search to see statistics",
                                    font=("Arial", 9), bg=WHITE, justify=tk.LEFT)
        self.stats_label.pack(pady=10, padx=10)
        
    def set_mode(self, mode):
        """Set the current mode"""
        self.mode = mode
        self.mode_label.config(text=f"Mode: {mode.replace('_', ' ').title()}")
    
    def draw_grid(self):
        """Draw the grid"""
        self.canvas.delete("all")
        self.cells.clear()
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                
                # Determine color
                color = WHITE
                if (row, col) == self.env.start:
                    color = GREEN
                elif (row, col) == self.env.target:
                    color = RED
                elif (row, col) in self.env.obstacles:
                    color = ORANGE if (row, col) in self.dynamic_obstacles else BLACK
                elif (row, col) in self.path:
                    color = YELLOW
                elif (row, col) in self.frontier_set:
                    color = CYAN
                elif (row, col) in self.explored_set:
                    color = LIGHT_GRAY
                
                # Draw cell
                cell_id = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                       fill=color, outline=GRAY, width=2)
                self.cells[(row, col)] = cell_id
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        if self.searching:
            return
        
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        
        if not self.env.is_valid(row, col):
            return
        
        self.handle_cell_action(row, col)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.searching or self.mode not in ["add_obstacle", "remove_obstacle"]:
            return
        
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        
        if not self.env.is_valid(row, col):
            return
        
        self.handle_cell_action(row, col)
    
    def handle_cell_action(self, row, col):
        """Handle action on a cell"""
        if self.mode == "set_start":
            self.env.set_start(row, col)
        elif self.mode == "set_target":
            self.env.set_target(row, col)
        elif self.mode == "add_obstacle":
            self.env.add_obstacle(row, col)
        elif self.mode == "remove_obstacle":
            self.env.remove_obstacle(row, col)
        
        self.draw_grid()
    
    def clear_search_data(self):
        """Clear search data"""
        self.frontier_set.clear()
        self.explored_set.clear()
        self.path.clear()
        self.dynamic_obstacles.clear()
        self.search_complete = False
        self.searching = False
        self.draw_grid()
        self.stats_label.config(text="Search cleared. Ready for new search.")
    
    def reset_grid(self):
        """Reset the entire grid"""
        self.env = GridEnvironment(GRID_SIZE, GRID_SIZE)
        self.clear_search_data()
        self.draw_grid()
        self.stats_label.config(text="Grid reset. Set start and target points.")
    
    def update_stats_display(self):
        """Update statistics display"""
        stats_text = f"""Algorithm: {self.stats['algorithm']}
Nodes Explored: {self.stats['nodes_explored']}
Path Length: {self.stats['path_length']}
Time: {self.stats['search_time']:.3f}s"""
        self.stats_label.config(text=stats_text)
    
    def reconstruct_path(self, parent, end_pos):
        """Reconstruct path"""
        path = []
        current = end_pos
        while current is not None:
            path.append(current)
            current = parent.get(current)
        return path[::-1]
    
    def bfs(self):
        """Breadth-First Search"""
        if not self.env.start or not self.env.target:
            messagebox.showwarning("Warning", "Please set start and target points!")
            return
        
        start_time = time.time()
        queue = deque([self.env.start])
        visited = {self.env.start}
        parent = {self.env.start: None}
        
        while queue and self.searching:
            new_obstacle = self.env.spawn_dynamic_obstacle(set(queue), visited)
            if new_obstacle:
                self.dynamic_obstacles.append(new_obstacle)
            
            current = queue.popleft()
            self.explored_set.add(current)
            
            if current == self.env.target:
                self.path = self.reconstruct_path(parent, current)
                self.stats['path_length'] = len(self.path)
                self.search_complete = True
                break
            
            for neighbor in self.env.get_neighbors(current[0], current[1]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
                    self.frontier_set.add(neighbor)
            
            self.frontier_set.discard(current)
            self.draw_grid()
            self.root.update()
            self.root.after(100)
        
        self.stats['nodes_explored'] = len(self.explored_set)
        self.stats['search_time'] = time.time() - start_time
        self.stats['algorithm'] = "BFS"
        self.searching = False
        self.update_stats_display()
    
    def dfs(self):
        """Depth-First Search"""
        if not self.env.start or not self.env.target:
            messagebox.showwarning("Warning", "Please set start and target points!")
            return
        
        start_time = time.time()
        stack = [self.env.start]
        visited = {self.env.start}
        parent = {self.env.start: None}
        
        while stack and self.searching:
            new_obstacle = self.env.spawn_dynamic_obstacle(set(stack), visited)
            if new_obstacle:
                self.dynamic_obstacles.append(new_obstacle)
            
            current = stack.pop()
            self.explored_set.add(current)
            
            if current == self.env.target:
                self.path = self.reconstruct_path(parent, current)
                self.stats['path_length'] = len(self.path)
                self.search_complete = True
                break
            
            for neighbor in self.env.get_neighbors(current[0], current[1]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    stack.append(neighbor)
                    self.frontier_set.add(neighbor)
            
            self.frontier_set.discard(current)
            self.draw_grid()
            self.root.update()
            self.root.after(100)
        
        self.stats['nodes_explored'] = len(self.explored_set)
        self.stats['search_time'] = time.time() - start_time
        self.stats['algorithm'] = "DFS"
        self.searching = False
        self.update_stats_display()
    
    def ucs(self):
        """Uniform-Cost Search"""
        if not self.env.start or not self.env.target:
            messagebox.showwarning("Warning", "Please set start and target points!")
            return
        
        start_time = time.time()
        pq = PriorityQueue()
        pq.put((0, self.env.start))
        visited = set()
        parent = {self.env.start: None}
        cost = {self.env.start: 0}
        
        while not pq.empty() and self.searching:
            current_cost, current = pq.get()
            
            if current in visited:
                continue
            
            visited.add(current)
            self.explored_set.add(current)
            
            if current == self.env.target:
                self.path = self.reconstruct_path(parent, current)
                self.stats['path_length'] = len(self.path)
                self.search_complete = True
                break
            
            for neighbor in self.env.get_neighbors(current[0], current[1]):
                dr = abs(neighbor[0] - current[0])
                dc = abs(neighbor[1] - current[1])
                move_cost = 1.414 if (dr == 1 and dc == 1) else 1.0
                
                new_cost = current_cost + move_cost
                
                if neighbor not in visited and (neighbor not in cost or new_cost < cost[neighbor]):
                    cost[neighbor] = new_cost
                    parent[neighbor] = current
                    pq.put((new_cost, neighbor))
                    self.frontier_set.add(neighbor)
            
            self.frontier_set.discard(current)
            self.draw_grid()
            self.root.update()
            self.root.after(100)
        
        self.stats['nodes_explored'] = len(self.explored_set)
        self.stats['search_time'] = time.time() - start_time
        self.stats['algorithm'] = "UCS"
        self.searching = False
        self.update_stats_display()
    
    def dls(self, depth_limit=8):
        """Depth-Limited Search"""
        if not self.env.start or not self.env.target:
            messagebox.showwarning("Warning", "Please set start and target points!")
            return
        
        start_time = time.time()
        stack = [(self.env.start, 0)]
        visited = {self.env.start}
        parent = {self.env.start: None}
        
        while stack and self.searching:
            current, depth = stack.pop()
            self.explored_set.add(current)
            
            if current == self.env.target:
                self.path = self.reconstruct_path(parent, current)
                self.stats['path_length'] = len(self.path)
                self.search_complete = True
                break
            
            if depth < depth_limit:
                for neighbor in self.env.get_neighbors(current[0], current[1]):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        parent[neighbor] = current
                        stack.append((neighbor, depth + 1))
                        self.frontier_set.add(neighbor)
            
            self.frontier_set.discard(current)
            self.draw_grid()
            self.root.update()
            self.root.after(100)
        
        self.stats['nodes_explored'] = len(self.explored_set)
        self.stats['search_time'] = time.time() - start_time
        self.stats['algorithm'] = f"DLS (limit={depth_limit})"
        self.searching = False
        self.update_stats_display()
    
    def iddfs(self):
        """Iterative Deepening DFS"""
        if not self.env.start or not self.env.target:
            messagebox.showwarning("Warning", "Please set start and target points!")
            return
        
        start_time = time.time()
        max_depth = 20
        
        for depth_limit in range(max_depth):
            if not self.searching:
                break
            
            stack = [(self.env.start, 0)]
            visited = {self.env.start}
            parent = {self.env.start: None}
            
            while stack and self.searching:
                current, depth = stack.pop()
                self.explored_set.add(current)
                
                if current == self.env.target:
                    self.path = self.reconstruct_path(parent, current)
                    self.stats['path_length'] = len(self.path)
                    self.search_complete = True
                    self.stats['nodes_explored'] = len(self.explored_set)
                    self.stats['search_time'] = time.time() - start_time
                    self.stats['algorithm'] = "IDDFS"
                    self.searching = False
                    self.update_stats_display()
                    return
                
                if depth < depth_limit:
                    for neighbor in self.env.get_neighbors(current[0], current[1]):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            parent[neighbor] = current
                            stack.append((neighbor, depth + 1))
                            self.frontier_set.add(neighbor)
                
                self.frontier_set.discard(current)
                self.draw_grid()
                self.root.update()
                self.root.after(80)
        
        self.stats['nodes_explored'] = len(self.explored_set)
        self.stats['search_time'] = time.time() - start_time
        self.stats['algorithm'] = "IDDFS"
        self.searching = False
        self.update_stats_display()
    
    def bidirectional(self):
        """Bidirectional Search"""
        if not self.env.start or not self.env.target:
            messagebox.showwarning("Warning", "Please set start and target points!")
            return
        
        start_time = time.time()
        
        queue_forward = deque([self.env.start])
        visited_forward = {self.env.start}
        parent_forward = {self.env.start: None}
        
        queue_backward = deque([self.env.target])
        visited_backward = {self.env.target}
        parent_backward = {self.env.target: None}
        
        meeting_point = None
        
        while queue_forward and queue_backward and self.searching:
            if queue_forward:
                current_forward = queue_forward.popleft()
                self.explored_set.add(current_forward)
                
                if current_forward in visited_backward:
                    meeting_point = current_forward
                    break
                
                for neighbor in self.env.get_neighbors(current_forward[0], current_forward[1]):
                    if neighbor not in visited_forward:
                        visited_forward.add(neighbor)
                        parent_forward[neighbor] = current_forward
                        queue_forward.append(neighbor)
                        self.frontier_set.add(neighbor)
                
                self.frontier_set.discard(current_forward)
            
            if queue_backward:
                current_backward = queue_backward.popleft()
                self.explored_set.add(current_backward)
                
                if current_backward in visited_forward:
                    meeting_point = current_backward
                    break
                
                for neighbor in self.env.get_neighbors(current_backward[0], current_backward[1]):
                    if neighbor not in visited_backward:
                        visited_backward.add(neighbor)
                        parent_backward[neighbor] = current_backward
                        queue_backward.append(neighbor)
                        self.frontier_set.add(neighbor)
                
                self.frontier_set.discard(current_backward)
            
            self.draw_grid()
            self.root.update()
            self.root.after(100)
        
        if meeting_point:
            path_forward = []
            current = meeting_point
            while current is not None:
                path_forward.append(current)
                current = parent_forward.get(current)
            path_forward = path_forward[::-1]
            
            path_backward = []
            current = parent_backward.get(meeting_point)
            while current is not None:
                path_backward.append(current)
                current = parent_backward.get(current)
            
            self.path = path_forward + path_backward
            self.stats['path_length'] = len(self.path)
            self.search_complete = True
        
        self.stats['nodes_explored'] = len(self.explored_set)
        self.stats['search_time'] = time.time() - start_time
        self.stats['algorithm'] = "Bidirectional"
        self.searching = False
        self.update_stats_display()
    
    def start_search(self):
        """Start search"""
        if self.searching:
            return
        
        if not self.env.start or not self.env.target:
            messagebox.showwarning("Warning", "Please set both start and target points!")
            return
        
        self.clear_search_data()
        self.searching = True
        
        algorithm = self.algorithm_var.get()
        
        # Run search in a way that allows UI updates
        if algorithm == "BFS":
            self.bfs()
        elif algorithm == "DFS":
            self.dfs()
        elif algorithm == "UCS":
            self.ucs()
        elif algorithm == "DLS":
            self.dls()
        elif algorithm == "IDDFS":
            self.iddfs()
        elif algorithm == "Bidirectional":
            self.bidirectional()
        
        self.draw_grid()

def main():
    root = tk.Tk()
    app = PathfindingVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()