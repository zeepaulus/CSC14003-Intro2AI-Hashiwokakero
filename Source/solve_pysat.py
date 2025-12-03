from typing import List, Dict, Tuple, Optional
from pysat.solvers import Solver
from cnf_encoder import build_cnf_from_grid, CNFEncoder

Grid = List[List[int]]
IslandInfo = Tuple[int, int, int]
EdgeInfo = Tuple[int, int, Tuple]
SolutionDict = Dict[Tuple[int, int], int]

class PySatSolver:
    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid
        self.solution: Optional[SolutionDict] = None
        self.islands: Dict[int, IslandInfo] = {}
        self.edges: List[EdgeInfo] = []

    def solve(self) -> Tuple[Optional[SolutionDict], Dict[int, IslandInfo], List[EdgeInfo]]:
        cnf, vpool, islands, edges, edge_vars = build_cnf_from_grid(self.grid)
        self.islands, self.edges = islands, edges
        decision_vars = set()
        for (x1, x2) in edge_vars.values():
            decision_vars.add(x1)
            decision_vars.add(x2)

        solution: Optional[SolutionDict] = None
        
        with Solver(name="g4") as solver:
            solver.append_formula(cnf.clauses)
            while solver.solve():
                model = solver.get_model()
                current_solution: SolutionDict = {}
                for (i, j), (x1, x2) in edge_vars.items():
                    val_x1 = model[x1 - 1] > 0 
                    val_x2 = model[x2 - 1] > 0
                    
                    if val_x1:
                        count = 1
                        if val_x2:
                            count = 2
                        current_solution[(i, j)] = count
                
                if CNFEncoder.check_connectivity(islands, current_solution):
                    solution = current_solution
                    break
                else:
                    blocking_clause = []
                    for lit in model:
                        if abs(lit) in decision_vars:
                            blocking_clause.append(-lit)
                    solver.add_clause(blocking_clause)

        self.solution = solution
        return solution, islands, edges