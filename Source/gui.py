import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import tracemalloc
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from utils import read_input, draw_solution, write_output
from benchmark import run_benchmark
from solve_pysat import PySatSolver
from solve_astar import AStarSolver
from solve_backtracking import BacktrackingSolver
from solve_bruteforce import BruteForceCNFSolver

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1) 
except Exception:
    pass

SOLVERS = {
    "PySAT": PySatSolver,
    "AStar": AStarSolver,
    "Backtracking": BacktrackingSolver,
    "BruteForce": BruteForceCNFSolver,
}

class HashiGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Hashi Solver Ultimate")
        window_width = 1280
        window_height = 860
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.root.resizable(False, False) 
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_solver = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_solver, text="Single Solve")
        self._init_tab_solver()

        self.tab_benchmark = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_benchmark, text="Benchmark")
        self._init_tab_benchmark()

        self.current_grid = None
        self.current_solution = None
        self.current_islands = None
        self.current_idx = None
        self.current_solver_name = None
        self.benchmark_data = None 

    def _init_tab_solver(self):
        control_frame = ttk.LabelFrame(self.tab_solver, text="Control Panel")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        ttk.Label(control_frame, text="Input Index:").pack(pady=(10, 5), anchor="w")
        self.input_entry = ttk.Entry(control_frame, width=10)
        self.input_entry.pack(pady=5)
        self.input_entry.insert(0, "1")
        self.input_entry.bind("<Return>", lambda event: self.on_load_input())

        ttk.Button(control_frame, text="Load Input", command=self.on_load_input, width=15).pack(pady=5)
        ttk.Separator(control_frame, orient='horizontal').pack(fill='x', pady=15)
        ttk.Label(control_frame, text="Thuật toán:").pack(pady=5, anchor="w")
        self.solver_name = tk.StringVar(value="PySAT")
        ttk.Combobox(control_frame, textvariable=self.solver_name, values=list(SOLVERS.keys()), state="readonly", width=18, justify="center").pack(pady=5)
        
        ttk.Button(control_frame, text="SOLVE", command=self.on_solve, width=15).pack(pady=15)
        self.lbl_info = ttk.Label(control_frame, text="Ready", foreground="blue", font=("Arial", 10), wraplength=150)
        self.lbl_info.pack(pady=10)
        self.btn_save_sol = ttk.Button(control_frame, text="Save Result", command=self.on_save_solution, state=tk.DISABLED, width=15)
        self.btn_save_sol.pack(pady=5)

        canvas_container = tk.Frame(self.tab_solver, bg="#f0f0f0")
        canvas_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas_size = 750 
        self.canvas = tk.Canvas(canvas_container, width=self.canvas_size, height=self.canvas_size, bg="white", highlightthickness=2, highlightbackground="#999")
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

    def _init_tab_benchmark(self):
        top_container = ttk.Frame(self.tab_benchmark)
        top_container.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        control_frame = ttk.LabelFrame(top_container, text="Thiết lập Benchmark")
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        input_frame = ttk.Frame(control_frame)
        input_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        ttk.Label(input_frame, text="Inputs (vd: 1, 2, 5): ").pack(side=tk.LEFT)
        self.bench_indices_entry = ttk.Entry(input_frame, width=30)
        self.bench_indices_entry.pack(side=tk.LEFT, padx=5)

        solver_frame = ttk.Frame(control_frame)
        solver_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        ttk.Label(solver_frame, text="So sánh: ").pack(side=tk.LEFT)
        
        self.solver_vars = {}
        for name in SOLVERS.keys():
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(solver_frame, text=name, variable=var)
            chk.pack(side=tk.LEFT, padx=5)
            self.solver_vars[name] = var
            
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Run", command=self.on_run_benchmark).pack(side=tk.LEFT)
        self.result_control_frame = ttk.LabelFrame(top_container, text="Kết quả")
        self.result_control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        res_inner_frame = ttk.Frame(self.result_control_frame)
        res_inner_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=15)

        ttk.Label(res_inner_frame, text="Chế độ xem: ").pack(side=tk.LEFT, padx=5)
        
        self.chart_view_var = tk.StringVar(value="Time")
        
        self.rad_time = ttk.Radiobutton(res_inner_frame, text="Time (ms)", variable=self.chart_view_var, value="Time", command=self.refresh_chart_view, state=tk.DISABLED)
        self.rad_time.pack(side=tk.LEFT, padx=5)
        
        self.rad_mem = ttk.Radiobutton(res_inner_frame, text="Memory (MB)", variable=self.chart_view_var, value="Memory", command=self.refresh_chart_view, state=tk.DISABLED)
        self.rad_mem.pack(side=tk.LEFT, padx=5)
        
        self.btn_save_chart = ttk.Button(res_inner_frame, text="Save Chart", command=self.on_save_charts, state=tk.DISABLED)
        self.btn_save_chart.pack(side=tk.LEFT, padx=20)

        self.chart_frame = ttk.Frame(self.tab_benchmark)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.fig = None

    def on_load_input(self):
        idx_str = self.input_entry.get().strip()
        try:
            idx = int(idx_str)
            path = f"Inputs/input-{idx:02d}.txt"
            grid = read_input(path)
        except Exception:
            messagebox.showerror("Lỗi", "Input không hợp lệ hoặc file không tồn tại.")
            return

        self.current_idx = idx
        self.current_grid = grid
        
        self.current_solution = None
        self.current_islands = None
        self.btn_save_sol.config(state=tk.DISABLED)

        self.draw_board(grid, is_solved=False)

    def on_solve(self):
        idx_str = self.input_entry.get().strip()
        try:
            idx = int(idx_str)
            if self.current_grid is None or self.current_idx != idx:
                self.on_load_input()
                if self.current_grid is None: return 
        except ValueError:
             messagebox.showerror("Lỗi", "Input index lỗi")
             return

        name = self.solver_name.get()
        
        grid = self.current_grid
        self.lbl_info.config(text=f"Solving with {name}...", foreground="orange")
        self.root.update()

        solver_cls = SOLVERS[name]
        tracemalloc.start()
        t0 = time.perf_counter()
        
        solver = solver_cls(grid)
        solution, islands, _ = solver.solve()
        
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mb = peak / (1024 * 1024)

        if solution:
            self.lbl_info.config(text=f"Done!\nTime: {elapsed:.4f}s\nMem: {peak_mb:.2f}MB", foreground="green")
            self.current_solver_name = name
            self.current_solution = solution
            self.current_islands = islands
            self.btn_save_sol.config(state=tk.NORMAL)
            
            char_grid = draw_solution(grid, islands, solution)
            self.draw_board(grid, char_grid=char_grid, is_solved=True)
        else:
            self.lbl_info.config(text="Fail!\nNo solution.", foreground="red")

    def on_save_solution(self):
        if self.current_solution:
            write_output(self.current_solver_name, self.current_idx, self.current_grid, self.current_islands, self.current_solution)
            messagebox.showinfo("Done", "Đã lưu kết quả.")

    def draw_board(self, grid, char_grid=None, is_solved=False):
        self.canvas.delete("all")
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        if not rows: return

        w = self.canvas_size
        h = self.canvas_size
        padding = 10 
        available_w = w - 2 * padding
        available_h = h - 2 * padding
        a = min(available_w / cols, available_h / rows)
        grid_pixel_w = cols * a
        grid_pixel_h = rows * a
        start_x = (w - grid_pixel_w) / 2
        start_y = (h - grid_pixel_h) / 2

        bridge_color = "blue"
        bridge_width = max(2, int(a * 0.1)) 
        bridge_offset = a * 0.15
        island_radius = (a / 2) * 0.9 
        font_size = int(a * 0.3)

        def get_top_left(r, c):
            return start_x + c * a, start_y + r * a

        def get_center(r, c):
            return start_x + c * a + a/2, start_y + r * a + a/2

        for r in range(rows):
            for c in range(cols):
                x, y = get_top_left(r, c)
                self.canvas.create_rectangle(x, y, x + a, y + a, outline="#e0e0e0", width=1)

        if is_solved and char_grid:
            for r in range(rows):
                for c in range(cols):
                    ch = char_grid[r][c]
                    if ch in ["-", "=", "|", "$"]:
                        cx, cy = get_center(r, c)
                        x1, y1 = get_top_left(r, c)
                        x2, y2 = x1 + a, y1 + a     

                        if ch == "-":
                            self.canvas.create_line(x1, cy, x2, cy, width=bridge_width, fill=bridge_color)
                        elif ch == "=":
                            self.canvas.create_line(x1, cy - bridge_offset, x2, cy - bridge_offset, width=bridge_width, fill=bridge_color)
                            self.canvas.create_line(x1, cy + bridge_offset, x2, cy + bridge_offset, width=bridge_width, fill=bridge_color)
                        elif ch == "|":
                            self.canvas.create_line(cx, y1, cx, y2, width=bridge_width, fill=bridge_color)
                        elif ch == "$":
                            self.canvas.create_line(cx - bridge_offset, y1, cx - bridge_offset, y2, width=bridge_width, fill=bridge_color)
                            self.canvas.create_line(cx + bridge_offset, y1, cx + bridge_offset, y2, width=bridge_width, fill=bridge_color)

        for r in range(rows):
            for c in range(cols):
                val = grid[r][c]
                if val != 0:
                    cx, cy = get_center(r, c)
                    self.canvas.create_oval(
                        cx - island_radius, cy - island_radius,
                        cx + island_radius, cy + island_radius,
                        fill="white", outline="black", width=2
                    )
                    self.canvas.create_text(
                        cx, cy,
                        text=str(val),
                        font=("Helvetica", font_size, "bold"),
                        fill="black"
                    )

    def on_run_benchmark(self):
        inp_str = self.bench_indices_entry.get().strip()
        if not inp_str:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập danh sách input (vd: 1, 2, 3)")
            return
        
        try:
            indices = [int(x) for x in inp_str.replace(",", " ").split()]
        except ValueError:
            messagebox.showerror("Lỗi", "Format input không hợp lệ.")
            return

        selected_solvers = []
        for name, var in self.solver_vars.items():
            if var.get():
                selected_solvers.append((name, SOLVERS[name]))
        
        if not selected_solvers:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn ít nhất 1 thuật toán.")
            return
        self.root.update()

        data = run_benchmark(indices, selected_solvers)
        self.benchmark_data = data 
        self.rad_time.config(state=tk.NORMAL)
        self.rad_mem.config(state=tk.NORMAL)
        self.btn_save_chart.config(state=tk.NORMAL)
        self.refresh_chart_view()

    def refresh_chart_view(self):
        if self.benchmark_data:
            self.plot_benchmark_results(self.benchmark_data)

    def plot_benchmark_results(self, data):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        indices = data["indices"]
        solvers_data = data["solvers"]
        view_mode = self.chart_view_var.get() 

        self.fig = Figure(figsize=(10, 5), dpi=100)
        ax = self.fig.add_subplot(111)
        
        if view_mode == "Time":
            ax.set_title("Benchmark Results: TIME (ms)")
            ax.set_ylabel("Time (ms)")
        else:
            ax.set_title("Benchmark Results: MEMORY (MB)")
            ax.set_ylabel("Peak RAM (MB)")
            
        ax.set_xlabel("Input Index")
        ax.set_xticks(indices)
        ax.grid(True, linestyle="--", alpha=0.5)

        markers = ['o', 's', '^', 'D']
        for i, (name, res) in enumerate(solvers_data.items()):
            m = markers[i % len(markers)]
            y_data = res["times"] if view_mode == "Time" else res["mems"]
            ax.plot(indices, y_data, marker=m, label=name, linewidth=2)

        ax.legend()
        self.fig.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self.chart_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def on_save_charts(self):
        if self.fig and self.benchmark_data:
            save_dir = os.path.join("Outputs", "Benchmark")
            os.makedirs(save_dir, exist_ok=True)
            
            solvers_keys = list(self.benchmark_data["solvers"].keys())
            solvers_str = "-".join(solvers_keys)
            
            indices = self.benchmark_data["indices"]
            indices_str = "-".join(map(str, indices[:10]))
            if len(indices) > 10: indices_str += "_etc"
            
            view_mode = self.chart_view_var.get()
            suffix = "time" if view_mode == "Time" else "memory"
            
            filename = f"{solvers_str}-inputs_{indices_str}-{suffix}.png"
            full_path = os.path.join(save_dir, filename)
            
            try:
                self.fig.savefig(full_path)
                messagebox.showinfo("Saved", f"Đã lưu biểu đồ ({view_mode}) tại:\n{full_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi lưu file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HashiGUI(root)
    root.mainloop()