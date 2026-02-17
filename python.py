import tkinter as tk
from tkinter import messagebox
import time
import random
from queue import Queue, PriorityQueue

# --- Constants ---
ROWS, COLS = 10, 10
CELL_SIZE = 50
DELAY = 0.1  # seconds between steps
DYNAMIC_OBS_PROB = 0.05  # Probability of dynamic obstacle spawn

# Short limits for DLS/IDDFS
DLS_LIMIT = 5
IDDFS_MAX_DEPTH = 10

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
INITIAL_TEXT_COLOR = "#d3d3d3"

# --- Grid Setup ---
class Cell:
    def __init__(self, row, col, canvas_id):
        self.row = row
        self.col = col
        self.canvas_id = canvas_id
        self.type = "empty"  # empty, wall, start, target

class GridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Pathfinder - Tkinter")
        self.mode = None
        self.start = None
        self.target = None
        self.grid = []
        self.algorithm = tk.StringVar(value="BFS")
        self.dynamic_obstacles = tk.BooleanVar(value=False)
        self.stop_flag = False  # For stopping search

        # Canvas
        self.canvas = tk.Canvas(root, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE)
        self.canvas.grid(row=0, column=0, rowspan=10)
        self.canvas.bind("<Button-1>", self.cell_clicked)

        # Sidebar
        sidebar = tk.Frame(root, bg=SIDEBAR_BG)
        sidebar.grid(row=0, column=1, sticky="ns", padx=5, pady=5)
        tk.Button(sidebar, text="Set Start Node", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("start")).pack(fill="x", pady=3)
        tk.Button(sidebar, text="Set Target Node", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("target")).pack(fill="x", pady=3)
        tk.Button(sidebar, text="Place/Remove Wall", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("wall")).pack(fill="x", pady=3)
        tk.Button(sidebar, text="Clear Cell", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=lambda: self.set_mode("clear")).pack(fill="x", pady=3)
        tk.Button(sidebar, text="Clear Grid", bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                  command=self.clear_grid).pack(fill="x", pady=3)
        tk.Button(sidebar, text="Start Search", bg="#f44336", fg=BUTTON_TEXT_COLOR,
                  command=self.start_search).pack(fill="x", pady=3)
        tk.Button(sidebar, text="Stop Search", bg="#FF9800", fg=BUTTON_TEXT_COLOR,
                  command=self.stop_search).pack(fill="x", pady=3)
        tk.Checkbutton(sidebar, text="Dynamic Obstacles", variable=self.dynamic_obstacles,
                       bg=SIDEBAR_BG).pack(pady=5)
        tk.Label(sidebar, text="Select Algorithm:", bg=SIDEBAR_BG, fg=LABEL_COLOR).pack(pady=5)
        tk.OptionMenu(sidebar, self.algorithm, "BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional").pack(fill="x")

        self.create_grid()

    # --- Grid Creation ---
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

    # --- Mode ---
    def set_mode(self, mode):
        self.mode = mode

    # --- Click Handling ---
    def cell_clicked(self, event):
        col, row = event.x // CELL_SIZE, event.y // CELL_SIZE
        if row >= ROWS or col >= COLS:
            return
        cell = self.grid[row][col]
        if self.mode == "start":
            if self.start:
                self.grid[self.start[0]][self.start[1]].type = "empty"
                self.update_cell_color(self.start[0], self.start[1])
            self.start = (row, col)
            cell.type = "start"
            self.update_cell_color(row, col)
        elif self.mode == "target":
            if self.target:
                self.grid[self.target[0]][self.target[1]].type = "empty"
                self.update_cell_color(self.target[0], self.target[1])
            self.target = (row, col)
            cell.type = "target"
            self.update_cell_color(row, col)
        elif self.mode == "wall":
            cell.type = "empty" if cell.type=="wall" else "wall"
            self.update_cell_color(row, col)
        elif self.mode == "clear":
            if (row, col) == self.start:
                self.start = None
            if (row, col) == self.target:
                self.target = None
            cell.type = "empty"
            self.update_cell_color(row, col)

    # --- Coloring ---
    def update_cell_color(self, row, col, number=None):
        cell = self.grid[row][col]
        color = EMPTY_COLOR
        if cell.type=="start": color=START_COLOR
        elif cell.type=="target": color=TARGET_COLOR
        elif cell.type=="wall": color=WALL_COLOR
        elif cell.type=="explored": color=EXPLORED_COLOR
        elif cell.type=="frontier": color=FRONTIER_COLOR
        elif cell.type=="path": color=PATH_COLOR
        elif cell.type=="obstacle": color=OBSTACLE_COLOR

        self.canvas.itemconfig(cell.canvas_id, fill=color)
        self.canvas.delete(f"text_{row}_{col}")
        if number is not None:
            self.canvas.create_text(col*CELL_SIZE+CELL_SIZE//2, row*CELL_SIZE+CELL_SIZE//2,
                                    text=str(number), fill="black", tags=f"text_{row}_{col}")

    # --- Grid Utilities ---
    def clear_grid(self):
        self.start = None
        self.target = None
        self.stop_flag = True
        for row in self.grid:
            for cell in row:
                cell.type = "empty"
                self.update_cell_color(cell.row, cell.col)

    def clear_explored_path(self):
        for row in self.grid:
            for cell in row:
                if cell.type in ("explored","frontier","path"):
                    cell.type = "empty"
                    self.update_cell_color(cell.row, cell.col)

    def neighbors(self, row, col):
        # Strict clockwise order with only main diagonals
        directions = [(-1, 0),  # Up
                      (0, 1),   # Right
                      (1, 0),   # Bottom
                      (1, 1),   # Bottom-Right (main diagonal)
                      (0, -1),  # Left
                      (-1, -1)] # Top-Left (main diagonal)
        
        result = []
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                if self.grid[r][c].type not in ("wall", "obstacle"):
                    result.append((r, c))
        return result


    def spawn_dynamic_obstacle(self):
        if self.dynamic_obstacles.get() and random.random()<DYNAMIC_OBS_PROB:
            empty_cells = [cell for row in self.grid for cell in row if cell.type=="empty"]
            if empty_cells:
                cell = random.choice(empty_cells)
                cell.type="obstacle"
                self.update_cell_color(cell.row, cell.col)

    # --- Search Controls ---
    def stop_search(self):
        self.stop_flag = True

    def animate_node(self,row,col,number=None,frontier=False,explored=False):
        if self.stop_flag:
            raise StopIteration
        cell=self.grid[row][col]
        if frontier: cell.type="frontier"
        if explored: cell.type="explored"
        self.update_cell_color(row,col,number)
        self.root.update()
        time.sleep(DELAY)
        self.spawn_dynamic_obstacle()

    def reconstruct_path(self,came_from,end):
        path=[]
        current=end
        while current in came_from:
            path.append(current)
            current=came_from[current]
        path.reverse()
        for r,c in path:
            cell=self.grid[r][c]
            if cell.type not in ("start","target"):
                cell.type="path"
                self.update_cell_color(r,c)
                self.root.update()
                time.sleep(DELAY)

    # --- Search Algorithms ---
    def start_search(self):
        if not self.start or not self.target:
            messagebox.showwarning("Warning","Set both Start and Target!")
            return
        self.stop_flag=False
        algo=self.algorithm.get()
        try:
            if algo=="BFS": self.run_bfs()
            elif algo=="DFS": self.run_dfs()
            elif algo=="UCS": self.run_ucs()
            elif algo=="DLS": self.run_dls(DLS_LIMIT)
            elif algo=="IDDFS": self.run_iddfs(IDDFS_MAX_DEPTH)
            elif algo=="Bidirectional": self.run_bidirectional()
        except StopIteration:
            messagebox.showinfo("Info","Search Stopped!")

    # --- BFS ---
    def run_bfs(self):
        start,target=self.start,self.target
        queue=Queue();queue.put(start)
        came_from={};visited=set();node_number=1
        while not queue.empty():
            current=queue.get()
            if current in visited: continue
            visited.add(current)
            r,c=current
            self.animate_node(r,c,number=node_number,explored=True)
            node_number+=1
            if current==target: self.reconstruct_path(came_from,target);return
            for nr,nc in self.neighbors(r,c):
                if (nr,nc) not in visited: queue.put((nr,nc));came_from.setdefault((nr,nc),current)

    # --- DFS ---
    def run_dfs(self):
        start,target=self.start,self.target
        stack=[start];came_from={};visited=set();node_number=1
        while stack:
            current=stack.pop()
            if current in visited: continue
            visited.add(current)
            r,c=current
            self.animate_node(r,c,number=node_number,explored=True)
            node_number+=1
            if current==target: self.reconstruct_path(came_from,target);return
            for nr,nc in reversed(self.neighbors(r,c)):
                if (nr,nc) not in visited: stack.append((nr,nc));came_from.setdefault((nr,nc),current)

    # --- UCS ---
    def run_ucs(self):
        start,target=self.start,self.target
        pq=PriorityQueue();pq.put((0,start));came_from={};cost_so_far={start:0};node_number=1
        while not pq.empty():
            current_cost,current=pq.get()
            r,c=current
            self.animate_node(r,c,number=node_number,explored=True)
            node_number+=1
            if current==target: self.reconstruct_path(came_from,target);return
            for nr,nc in self.neighbors(r,c):
                new_cost=cost_so_far[current]+1
                if (nr,nc) not in cost_so_far or new_cost<cost_so_far[(nr,nc)]:
                    cost_so_far[(nr,nc)]=new_cost
                    pq.put((new_cost,(nr,nc)))
                    came_from[(nr,nc)]=current

    # --- DLS ---
    def run_dls(self,limit):
        start,target=self.start,self.target
        came_from={};visited=set();node_number_ref=[1]
        def dfs(node,depth):
            if self.stop_flag: raise StopIteration
            if depth<0: return False
            r,c=node
            if node not in visited:
                visited.add(node)
                self.animate_node(r,c,number=node_number_ref[0],explored=True)
                node_number_ref[0]+=1
            if node==target: return True
            for nr,nc in self.neighbors(r,c):
                if (nr,nc) not in visited:
                    came_from[(nr,nc)]=node
                    if dfs((nr,nc),depth-1): return True
            return False
        if dfs(start,limit): self.reconstruct_path(came_from,target)

    # --- IDDFS ---
    def run_iddfs(self,max_depth):
        start,target=self.start,self.target
        for depth in range(max_depth):
            self.clear_explored_path()
            came_from={};visited=set();node_number_ref=[1]
            def dfs(node,depth_left):
                if self.stop_flag: raise StopIteration
                if depth_left<0: return False
                r,c=node
                if node not in visited:
                    visited.add(node)
                    self.animate_node(r,c,number=node_number_ref[0],explored=True)
                    node_number_ref[0]+=1
                if node==target: return True
                for nr,nc in self.neighbors(r,c):
                    if (nr,nc) not in visited:
                        came_from[(nr,nc)]=node
                        if dfs((nr,nc),depth_left-1): return True
                return False
            if dfs(start,depth):
                self.reconstruct_path(came_from,target)
                break

    # --- Bidirectional ---
    def run_bidirectional(self):
        start,target=self.start,self.target
        frontier_start=Queue();frontier_target=Queue()
        frontier_start.put(start);frontier_target.put(target)
        came_from_start={start:None};came_from_target={target:None}
        visited_start=set([start]);visited_target=set([target])
        node_number=1;meeting_node=None
        while not frontier_start.empty() and not frontier_target.empty():
            # Start side
            current_start=frontier_start.get()
            r,c=current_start
            self.animate_node(r,c,number=node_number,explored=True)
            node_number+=1
            for nr,nc in self.neighbors(r,c):
                if (nr,nc) not in visited_start:
                    visited_start.add((nr,nc));frontier_start.put((nr,nc))
                    came_from_start[(nr,nc)]=current_start
                    if (nr,nc) in visited_target: meeting_node=(nr,nc);break
            if meeting_node: break
            # Target side
            current_target=frontier_target.get()
            r,c=current_target
            self.animate_node(r,c,number=node_number,explored=True)
            node_number+=1
            for nr,nc in self.neighbors(r,c):
                if (nr,nc) not in visited_target:
                    visited_target.add((nr,nc));frontier_target.put((nr,nc))
                    came_from_target[(nr,nc)]=current_target
                    if (nr,nc) in visited_start: meeting_node=(nr,nc);break
            if meeting_node: break
        if meeting_node:
            path_start=[];current=meeting_node
            while current: path_start.append(current);current=came_from_start[current]
            path_start.reverse()
            path_target=[];current=came_from_target[meeting_node]
            while current: path_target.append(current);current=came_from_target[current]
            full_path=path_start+path_target
            for r,c in full_path:
                if self.grid[r][c].type not in ("start","target"):
                    self.grid[r][c].type="path"
                    self.update_cell_color(r,c)
                    self.root.update()
                    time.sleep(DELAY)
        else: messagebox.showinfo("Result","No path found!")

# --- Main ---
if __name__=="__main__":
    root=tk.Tk()
    app=GridApp(root)
    root.mainloop()
