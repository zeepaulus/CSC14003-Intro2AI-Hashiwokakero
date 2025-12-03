import heapq
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
# Import Class CNFEncoder để dùng hàm check_connectivity static
from cnf_encoder import build_cnf_from_grid, CNFEncoder 

Grid = List[List[int]]
IslandInfo = Tuple[int, int, int]
EdgeInfo = Tuple[int, int, Tuple]
SolutionDict = Dict[Tuple[int, int], int]

class AStarSolver:
    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid
        self.solution: Optional[SolutionDict] = None
        self.islands: Dict[int, IslandInfo] = {}
        self.edges: List[EdgeInfo] = []

    def _count_unsatisfied_clauses(self, clauses: List[List[int]], assignment: List[Optional[bool]]) -> int:
        """
        Heuristic h(n): Đếm số lượng clause CHƯA được thỏa mãn.
        - Trả về float('inf') nếu phát hiện conflict (clause sai hoàn toàn).
        """
        unsat_count = 0
        for clause in clauses:
            is_satisfied = False
            unassigned_count = 0
            
            for lit in clause:
                val = assignment[abs(lit)]
                if val is None:
                    unassigned_count += 1
                elif (lit > 0 and val is True) or (lit < 0 and val is False):
                    is_satisfied = True
                    break # Clause này đã thỏa, không cần xét tiếp
            
            if not is_satisfied:
                # Nếu không còn biến nào chưa gán mà clause vẫn chưa thỏa -> Conflict (Dead end)
                if unassigned_count == 0:
                    return float('inf')
                unsat_count += 1
                
        return unsat_count

    def solve(self) -> Tuple[Optional[SolutionDict], Dict[int, IslandInfo], List[EdgeInfo]]:
        # 1. Build CNF
        cnf, vpool, islands, edges, edge_vars = build_cnf_from_grid(self.grid)
        self.islands, self.edges = islands, edges
        clauses = [list(c) for c in cnf.clauses]
        
        # Xác định số lượng biến tối đa
        max_var = vpool.top

        # 2. Variable Ordering (Quan trọng)
        # Chỉ quan tâm đến các biến cạnh (Decision Variables)
        decision_vars = set()
        for (x1, x2) in edge_vars.values():
            decision_vars.add(x1)
            decision_vars.add(x2)
        
        # Đếm tần suất biến để ưu tiên gán biến quan trọng trước
        var_freq = Counter()
        for clause in clauses:
            for lit in clause:
                v = abs(lit)
                if v in decision_vars:
                    var_freq[v] += 1
        
        # Danh sách biến cần gán, sắp xếp theo tần suất giảm dần
        ordered_vars = sorted(list(decision_vars), key=lambda v: -var_freq[v])

        # 3. Khởi tạo A*
        # Assignment: List[Optional[bool]]. Index 0 bỏ qua.
        init_assignment = [None] * (max_var + 1)
        
        # Priority Queue lưu tuple: (h, -g, assignment)
        # - h: Số clause chưa thỏa mãn (Min heap -> ưu tiên nhỏ nhất)
        # - -g: Độ sâu âm (Min heap -> ưu tiên g lớn nhất -> DFS behavior)
        h0 = self._count_unsatisfied_clauses(clauses, init_assignment)
        pq = []
        heapq.heappush(pq, (h0, 0, init_assignment))
        
        # Nút visited có thể tốn bộ nhớ với map lớn, 
        # nhưng với Variable Ordering cố định, ta ít khi gặp lặp trạng thái.
        # Có thể bỏ qua visited hoặc chỉ hash các decision vars.

        while pq:
            h, neg_g, assignment = heapq.heappop(pq)
            g = -neg_g

            # 4. Chọn biến tiếp theo để gán
            # Chỉ chọn trong danh sách ordered_vars chưa được gán
            var_to_assign = None
            for v in ordered_vars:
                if assignment[v] is None:
                    var_to_assign = v
                    break
            
            # 5. Goal Test (Nếu đã gán hết các biến quan trọng)
            if var_to_assign is None:
                # Nếu heuristic = 0 nghĩa là thỏa mãn mọi ràng buộc logic
                if h == 0:
                    # Decode solution
                    temp_sol: SolutionDict = {}
                    for (i, j), (x1, x2) in edge_vars.items():
                        cnt = 0
                        if assignment[x1]: cnt = 1
                        if assignment[x2]: cnt = 2
                        if cnt > 0: temp_sol[(i, j)] = cnt
                    
                    # [QUAN TRỌNG] Kiểm tra tính liên thông
                    if CNFEncoder.check_connectivity(islands, temp_sol):
                        self.solution = temp_sol
                        return temp_sol, islands, edges
                    else:
                        continue # Logic đúng nhưng đồ thị ngắt quãng -> Bỏ qua nhánh này
                else:
                    continue # Đã gán hết biến nhưng vẫn còn clause chưa thỏa -> Sai

            # 6. Branching (Phân nhánh)
            # Thử gán True/False cho biến được chọn
            # Mẹo: Thử True trước để ưu tiên tạo cầu (giúp heuristic giảm nhanh hơn với các clause check degree)
            for value in [True, False]:
                new_assignment = assignment[:] # Shallow copy (nhanh hơn deepcopy)
                new_assignment[var_to_assign] = value
                
                # Tính heuristic mới
                new_h = self._count_unsatisfied_clauses(clauses, new_assignment)
                
                # Pruning: Nếu nhánh gây conflict (inf), cắt bỏ ngay
                if new_h == float('inf'):
                    continue
                
                new_g = g + 1
                heapq.heappush(pq, (new_h, -new_g, new_assignment))

        self.solution = None
        return None, islands, edges