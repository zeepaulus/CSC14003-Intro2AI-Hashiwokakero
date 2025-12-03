import time
import tracemalloc
from typing import List, Dict, Tuple, Type
from utils import read_input
from solve_pysat import PySatSolver
from solve_astar import AStarSolver
from solve_backtracking import BacktrackingSolver
from solve_bruteforce import BruteForceCNFSolver

Grid = List[List[int]]

def run_and_profile(solver_cls: Type, grid: Grid) -> tuple[float, float, bool]:
    tracemalloc.start()
    t0 = time.perf_counter()
    solver = solver_cls(grid)
    try:
        solution, _, _ = solver.solve()
        success = solution is not None
    except Exception:
        success = False
    
    elapsed = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak / (1024 * 1024)
    return elapsed, peak_mb, success

def run_benchmark(indices: List[int], solver_subset: List[Tuple[str, Type]] = None) -> Dict:
    if solver_subset is None:
        solvers = [
            ("PySAT", PySatSolver),
            ("A*", AStarSolver),
            ("Backtracking", BacktrackingSolver),
            ("Brute force", BruteForceCNFSolver),
        ]
    else:
        solvers = solver_subset

    results = {
        "indices": indices,
        "solvers": {}
    }

    for name, cls in solvers:
        times: List[float] = []
        mems: List[float] = []
        
        for idx in indices:
            path = f"Inputs/input-{idx:02d}.txt"
            try:
                grid = read_input(path)
                t, mem, success = run_and_profile(cls, grid)
                if not success:
                    times.append(0) 
                    mems.append(0)
                else:
                    # Chuyển đổi giây (s) sang mili-giây (ms)
                    times.append(t * 1000)
                    mems.append(mem)
            except FileNotFoundError:
                times.append(0)
                mems.append(0)
        
        results["solvers"][name] = {
            "times": times,
            "mems": mems
        }
    
    return results