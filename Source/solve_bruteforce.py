from typing import List, Dict, Tuple, Optional
import itertools
from cnf_encoder import CNFEncoder

Grid = List[List[int]]
SolutionDict = Dict[Tuple[int, int], int]

class BruteForceCNFSolver:
    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid
        self.solution: Optional[SolutionDict] = None
        self.islands = None
        self.edges = None

    def solve(self):
        enc = CNFEncoder()
        enc.encode(self.grid)
        
        self.islands = enc.islands
        self.edges = enc.edges
        edge_vars = enc.edge_vars
        clauses = enc.cnf.clauses

        edge_keys = list(edge_vars.keys())
        n_edges = len(edge_keys)

        for bridges in itertools.product([0, 1, 2], repeat=n_edges):
            
            current_assignment = {}
            temp_sol: SolutionDict = {}
            
            for idx, count in enumerate(bridges):
                edge_coord = edge_keys[idx]
                x1, x2 = edge_vars[edge_coord]
                
                if count == 0:
                    current_assignment[x1] = False
                    current_assignment[x2] = False
                elif count == 1:
                    current_assignment[x1] = True
                    current_assignment[x2] = False
                    temp_sol[edge_coord] = 1
                else:
                    current_assignment[x1] = True
                    current_assignment[x2] = True
                    temp_sol[edge_coord] = 2

            is_valid_cnf = True
            for clause in clauses:
                clause_satisfied = False
                for lit in clause:
                    val = current_assignment.get(abs(lit))
                    if val is None: 
                        continue 
                        
                    if (lit > 0 and val is True) or (lit < 0 and val is False):
                        clause_satisfied = True
                        break
                
                if not clause_satisfied:
                    is_valid_cnf = False
                    break
            
            if not is_valid_cnf:
                continue
            
            if CNFEncoder.check_connectivity(self.islands, temp_sol):
                self.solution = temp_sol
                return temp_sol, self.islands, self.edges

        self.solution = None
        return None, self.islands, self.edges