import random
import heapq
from typing import List, Tuple, Dict
from collections import defaultdict
from math import inf


class DSU:
    """Disjoint-set (union-find) for merging adjacent node ids into clusters."""
    def __init__(self, n: int):
        self.parent = list(range(n + 1))

    def find(self, a: int) -> int:
        while a != self.parent[a]:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


class WorldBuilder:
    """Construct a base map and cluster adjacent nodes.

    Produces:
      - `x`, `y`: grid size
      - `node_positions`: dict mapping node_id -> (x,y)
      - `pos_to_node`: dict mapping (x,y) -> node_id
      - `pos_to_cluster`: dict mapping (x,y) -> cluster_id
      - `cluster_members`: dict mapping cluster_id -> set(node_id)
      - `_map`: grid with negative cluster ids for node cells
    """

    def __init__(self, size: tuple[int, int] = (10, 10), num_nodes: int = 10, random_nodes: bool = True, de_path: float = 10.0, inp: list[tuple[int, int]] = [], tile_weights: List[List[float]] | None = None):
        if de_path < 0:
            raise ValueError("Default path value cant be less than zero!")

        self.x, self.y = size
        self.n = num_nodes
        self.de_path = float(de_path)

        if (self.x * self.y) < self.n:
            raise ValueError("Ukuran grid terlalu kecil untuk jumlah node tersebut.")

        # Initialize base map costs. If `tile_weights` is provided (not None),
        # use it as the default grid of tile weights (must match size). Otherwise
        # fill with the scalar `de_path` value.
        if tile_weights is not None:
            # basic validation of shape
            if len(tile_weights) != self.x or any(len(row) != self.y for row in tile_weights):
                raise ValueError("tile_weights must be a list of lists with dimensions matching `size`")
            # copy to internal map
            self._map = [[float(tile_weights[i][j]) for j in range(self.y)] for i in range(self.x)]
        else:
            self._map = [[self.de_path for _ in range(self.y)] for _ in range(self.x)]

        # node_id -> (x,y)
        self.node_positions: Dict[int, Tuple[int, int]] = {}
        # (x,y) -> node_id
        self.pos_to_node: Dict[Tuple[int, int], int] = {}

        if random_nodes:
            self._randomize()
        else:
            self._assign(inp)

        # after nodes placed, build clusters (union adjacent nodes)
        self._build_clusters()

    def _randomize(self):
        all_positions = [(i, j) for i in range(self.x) for j in range(self.y)]
        holder = random.sample(all_positions, self.n)
        self._assign(holder)

    def _assign(self, inp: List[Tuple[int, int]]):
        """Place nodes using first `self.n` coordinates from `inp`.

        Assign node ids starting at 1. `node_positions` maps node id -> single (x,y).
        """
        for node_id, (nx, ny) in enumerate(inp[: self.n], start=1):
            if 0 <= nx < self.x and 0 <= ny < self.y:
                self._map[nx][ny] = -(node_id)
                self.node_positions[node_id] = (nx, ny)
                self.pos_to_node[(nx, ny)] = node_id

    def _build_clusters(self):
        """Use DSU to merge orthogonally adjacent nodes into clusters.

        Produces `pos_to_cluster` and `cluster_members`. Cluster ids are the DSU root ids.
        """
        dsu = DSU(self.n)

        # union neighboring nodes
        for node_id, (x, y) in self.node_positions.items():
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nb = (x + dx, y + dy)
                if nb in self.pos_to_node:
                    dsu.union(node_id, self.pos_to_node[nb])

        # group nodes by root
        clusters: Dict[int, set] = defaultdict(set)
        for node_id in range(1, self.n + 1):
            if node_id in self.node_positions:
                root = dsu.find(node_id)
                clusters[root].add(node_id)

        # normalize cluster ids to small sequential ids (optional)
        self.cluster_members: Dict[int, set] = {}
        self.pos_to_cluster: Dict[Tuple[int, int], int] = {}
        cluster_id_map: Dict[int, int] = {}
        next_cluster_id = 1

        for root, members in clusters.items():
            cid = next_cluster_id
            next_cluster_id += 1
            cluster_id_map[root] = cid
            self.cluster_members[cid] = members
            # mark positions on map with cluster id
            for nid in members:
                pos = self.node_positions[nid]
                self.pos_to_cluster[pos] = cid
                x, y = pos
                self._map[x][y] = -cid
    
    def check_node_accessibility(self, inp: List[Tuple[int, int]]) -> bool:
        """
        Memeriksa apakah semua kota berada dalam satu wilayah yang sama menggunakan Flood-fill.
        Mengembalikan True jika semua kota saling terhubung (tidak terisolasi total oleh gunung).
        """
        if not inp:
            return True
            
        # Ambil kota pertama dari input koordinat sebagai titik awal start flood-fill
        start_node = inp[0]
        
        visited = set()
        queue = [start_node]
        visited.add(start_node)
        
        # Jalankan BFS / Flood-fill
        while queue:
            cx, cy = queue.pop(0)
            
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                neighbor = (nx, ny)
                
                # Pastikan koordinat berada di dalam batas grid
                if 0 <= nx < self.x and 0 <= ny < self.y:
                    # KUNCI: Gunakan self._map (bukan planning_terrain)
                    if self._map[nx][ny] != float('inf') and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        
        # Periksa apakah ada koordinat kota yang tidak berhasil terjangkau oleh flood-fill
        for node in inp[: self.n]:
            if node not in visited:
                return False # Ketemu kota yang terkurung/terisolasi total!
                
        return True # Aman, semua kota berada dalam satu daratan yang sama

    def __print__(self):
        """Print the grid with nodes and default costs (clusters shown by id)."""
        for i in range(self.x):
            row = ""
            for j in range(self.y):
                if self._map[i][j] < 0:
                    row += f" K{-self._map[i][j]} "
                else:
                    row += f" {self._map[i][j]:.1f} "
            print(row)


class World:
    """Runtime world used by the GA and pathfinding.

    Attributes kept compatible with existing code:
      - `node_pos`: dict node_id -> (x,y) (single position)
      - `node_set`: set of node positions for quick membership tests
    Additional cluster structures:
      - `pos_to_cluster`: (x,y) -> cluster_id
      - `cluster_members`: cluster_id -> set(node_id)
      - `connected_clusters`: set of cluster_ids already touched by roads
    """

    def __init__(self, x: int, y: int, node_positions: dict, default_cost: float, threshold: int = 1, growth_rate: float = 2.0, discount_factor: float = 0.2, pos_to_cluster: Dict[Tuple[int,int], int] = None, cluster_members: Dict[int, set] = None):
        self.x = x
        self.y = y
        self.node_pos: Dict[int, Tuple[int, int]] = node_positions
        self.node_set = set(node_positions.values())

        self.pos_to_cluster: Dict[Tuple[int, int], int] = pos_to_cluster or {}
        self.cluster_members: Dict[int, set] = cluster_members or {}

        self.default_cost = default_cost
        self.max_traf = threshold
        self.growth_rate = growth_rate
        self.discount_factor = discount_factor

        self.road_layers = [[0 for _ in range(self.y)] for _ in range(self.x)]
        # --- TAMBAHKAN INI: Wadah permanen untuk mengunci rawa/gunung ---
        self.terrain_map = [[0 for _ in range(self.y)] for _ in range(self.x)]
        
        self.connected_clusters: set = set()
        self.connected_nodes: set = set()
        self.cluster_graph: Dict[int, set] = defaultdict(set)

    def reset_world(self):
        # Kembalikan road_layers menjadi kosong 0, TANPA menghapus isi terrain_map
        self.road_layers = [[0 for _ in range(self.y)] for _ in range(self.x)]
        self.connected_clusters.clear()
        self.connected_nodes.clear()
        self.cluster_graph = defaultdict(set)

    def add_road_path(self, path: List[Tuple[int, int]]):
        """Increment road layers and mark clusters/nodes touched by the path."""
        path_clusters = []
        for (px, py) in path:
            if not (0 <= px < self.x and 0 <= py < self.y):
                continue

            # Do not build roads on node tiles themselves. Paths should not
            # contain node positions (A* avoids them). Guard anyway.
            pos = (px, py)
            if pos not in self.node_set:
                self.road_layers[px][py] += 1

            # If this road cell is adjacent to any node, mark that node's
            # cluster as connected. This allows connecting to nodes without
            # building roads on top of node tiles.
            adjacent_clusters = []
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nb = (px + dx, py + dy)
                cid = self.pos_to_cluster.get(nb)
                if cid is not None:
                    adjacent_clusters.append(cid)

            for cid in adjacent_clusters:
                if cid not in self.connected_clusters:
                    self.connected_clusters.add(cid)
                    members = self.cluster_members.get(cid, set())
                    for nid in members:
                        self.connected_nodes.add(nid)
                if not path_clusters or path_clusters[-1] != cid:
                    path_clusters.append(cid)

        # add edges between consecutive clusters encountered on this path
        for i in range(len(path_clusters) - 1):
            a = path_clusters[i]
            b = path_clusters[i + 1]
            self.cluster_graph[a].add(b)
            self.cluster_graph[b].add(a)

        # If the path directly connects two clusters (non-consecutive same cluster occurrences handled above), ensure edge
        if len(path_clusters) >= 2:
            self.cluster_graph[path_clusters[0]].add(path_clusters[-1])
            self.cluster_graph[path_clusters[-1]].add(path_clusters[0])

    def remove_road_path(self, path: List[Tuple[int, int]]):
        """Decrement road layers for the cells in the path."""
        for (px, py) in path:
            if not (0 <= px < self.x and 0 <= py < self.y):
                continue
            pos = (px, py)
            if pos not in self.node_set:
                if self.road_layers[px][py] > 0:
                    self.road_layers[px][py] -= 1

    def update_connectivity_from_path(self, path: List[Tuple[int, int]]):
        """Mark clusters/nodes and build cluster graph from a path without changing road_layers."""
        path_clusters = []
        for (px, py) in path:
            if not (0 <= px < self.x and 0 <= py < self.y):
                continue

            adjacent_clusters = []
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nb = (px + dx, py + dy)
                cid = self.pos_to_cluster.get(nb)
                if cid is not None:
                    adjacent_clusters.append(cid)

            for cid in adjacent_clusters:
                if cid not in self.connected_clusters:
                    self.connected_clusters.add(cid)
                    members = self.cluster_members.get(cid, set())
                    for nid in members:
                        self.connected_nodes.add(nid)
                if not path_clusters or path_clusters[-1] != cid:
                    path_clusters.append(cid)

        # add edges between consecutive clusters encountered on this path
        for i in range(len(path_clusters) - 1):
            a = path_clusters[i]
            b = path_clusters[i + 1]
            self.cluster_graph[a].add(b)
            self.cluster_graph[b].add(a)

        if len(path_clusters) >= 2:
            self.cluster_graph[path_clusters[0]].add(path_clusters[-1])
            self.cluster_graph[path_clusters[-1]].add(path_clusters[0])
    def is_node_connected(self, node_id: int) -> bool:
        return node_id in self.connected_nodes

    def get_cell_cost(self, x: int, y: int, target_pos: Tuple[int, int]) -> float:
        if not (0 <= x < self.x and 0 <= y < self.y):
            return float('inf')

        current_pos = (x, y)
        if current_pos == target_pos:
            return 0.0

        if current_pos in self.node_set:
            return float('inf')
        
        # --- 1. AMBIL BIAYA ALAM ASLI LANGSUNG DARI TERRAIN MAP ---
        # Nilainya otomatis berupa: 50.0 (Normal), 250.0 (Rawa), atau inf (Gunung)
        base_cost = self.terrain_map[x][y]
        
        if base_cost == float('inf'):
            return float('inf')  # Gunung mutlak dilarang ditembus!

        # --- 2. HITUNG MODIFIKASI JALAN TOL DAN MACET SEPERTI BIASA ---
        num_layers = self.road_layers[x][y]
        if num_layers == 0:
            return base_cost # Jika tanah kosong, kembalikan nilai dasar alamnya
        elif num_layers <= self.max_traf:
            # Jika dipakai bersama dan lancar, dapat diskon dari nilai dasar alamnya!
            return base_cost * self.discount_factor
        else:
            # Jika macet, dapat penalti eksponensial dari nilai dasar alamnya!
            excess_layers = num_layers - self.max_traf
            return base_cost * (self.growth_rate ** excess_layers)

    def network_is_fully_connected(self) -> bool:
        """Return True if all clusters with members are connected together by a continuous road network.

        A continuous road network is a single connected component of road cells
        that is adjacent to all clusters.
        """
        clusters = set(self.cluster_members.keys())
        if len(clusters) <= 1:
            return True

        # Find all road cells
        road_cells = set()
        for x in range(self.x):
            for y in range(self.y):
                if self.road_layers[x][y] > 0:
                    road_cells.add((x, y))

        if not road_cells:
            return False

        # Find connected components of road cells
        visited = set()
        components = []
        for cell in road_cells:
            if cell in visited:
                continue
            comp = set()
            queue = [cell]
            visited.add(cell)
            while queue:
                cx, cy = queue.pop(0)
                comp.add((cx, cy))
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = cx + dx, cy + dy
                    neighbor = (nx, ny)
                    if neighbor in road_cells and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp)

        # For each component, check which clusters it is adjacent to
        for comp in components:
            adjacent_clusters = set()
            for rx, ry in comp:
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = rx + dx, ry + dy
                    cid = self.pos_to_cluster.get((nx, ny))
                    if cid is not None:
                        adjacent_clusters.add(cid)
            
            # If this component is adjacent to all clusters, then the network is fully connected!
            if adjacent_clusters >= clusters:
                return True

        return False

    def cluster_of_node(self, node_id: int) -> int | None:
        """Return cluster id for a given node id, or None if not assigned."""
        pos = self.node_pos.get(node_id)
        if pos is None:
            return None
        return self.pos_to_cluster.get(pos)

    def nodes_in_same_component(self, node_a: int, node_b: int) -> bool:
        """Return True if two nodes belong to the same connected component
        in the `cluster_graph` (i.e., there exists a road path connecting
        their clusters). Nodes in the same raw cluster are considered
        connected as well.
        """
        ca = self.cluster_of_node(node_a)
        cb = self.cluster_of_node(node_b)
        if ca is None or cb is None:
            return False
        if ca == cb:
            return True

        # BFS from ca over cluster_graph
        seen = {ca}
        queue = [ca]
        while queue:
            c = queue.pop(0)
            for nb in self.cluster_graph.get(c, set()):
                if nb == cb:
                    return True
                if nb not in seen:
                    seen.add(nb)
                    queue.append(nb)
        return False

    def find_shortest_path_between_clusters(self, cluster_a: int, cluster_b: int):
        """Find shortest A* path between any node in `cluster_a` and any
        node in `cluster_b`. Returns (path, cost) or (None, inf).
        This does not modify world state.
        """
        best_path = None
        best_cost = inf

        members_a = self.cluster_members.get(cluster_a, set())
        members_b = self.cluster_members.get(cluster_b, set())

        for nid_a in members_a:
            start = self.node_pos.get(nid_a)
            if start is None:
                continue
            for nid_b in members_b:
                target = self.node_pos.get(nid_b)
                if target is None:
                    continue
                route = a_star_search(self, start, target)
                if route:
                    cost = sum(self.get_cell_cost(x, y, target) for x, y in route[1:])
                    if cost < best_cost:
                        best_cost = cost
                        best_path = route

        return best_path, best_cost

    def get_cluster_components(self) -> List[set]:
        """Return a list of connected components (sets of cluster_ids) in the cluster graph.

        Two clusters belong to the same component if they are connected through the road network
        without transiting through houses.
        """
        clusters = set(self.cluster_members.keys())
        
        # Find all road cells
        road_cells = set()
        for x in range(self.x):
            for y in range(self.y):
                if self.road_layers[x][y] > 0:
                    road_cells.add((x, y))

        # Find connected components of road cells
        visited_cells = set()
        road_components = []
        for cell in road_cells:
            if cell in visited_cells:
                continue
            comp = set()
            queue = [cell]
            visited_cells.add(cell)
            while queue:
                cx, cy = queue.pop(0)
                comp.add((cx, cy))
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = cx + dx, cy + dy
                    neighbor = (nx, ny)
                    if neighbor in road_cells and neighbor not in visited_cells:
                        visited_cells.add(neighbor)
                        queue.append(neighbor)
            road_components.append(comp)

        # Build a graph of clusters where two clusters are adjacent if they touch the same road component
        adj = defaultdict(set)
        for comp in road_components:
            adjacent_clusters = set()
            for rx, ry in comp:
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = rx + dx, ry + dy
                    cid = self.pos_to_cluster.get((nx, ny))
                    if cid is not None:
                        adjacent_clusters.add(cid)
            
            # Connect all these adjacent clusters together in the graph
            for c1 in adjacent_clusters:
                for c2 in adjacent_clusters:
                    if c1 != c2:
                        adj[c1].add(c2)
                        adj[c2].add(c1)

        # Find connected components of clusters in this graph
        components = []
        visited_clusters = set()
        for c in clusters:
            if c in visited_clusters:
                continue
            comp = set()
            queue = [c]
            visited_clusters.add(c)
            while queue:
                cur = queue.pop(0)
                comp.add(cur)
                for nb in adj.get(cur, set()):
                    if nb not in visited_clusters:
                        visited_clusters.add(nb)
                        queue.append(nb)
            components.append(comp)

        return components

    def find_shortest_path_between_components(self, comp_a: set, comp_b: set) -> Tuple[List[Tuple[int,int]] | None, float]:
        """Find the shortest A* path between any node in comp_a and any node in comp_b.

        Returns a tuple (path, cost). If no path exists between any pair, returns (None, inf).
        This does not modify world state (except A* reads current road layers).
        """
        best_path = None
        best_cost = inf

        for nid_a in comp_a:
            start = self.node_pos.get(nid_a)
            if start is None:
                continue
            for nid_b in comp_b:
                target = self.node_pos.get(nid_b)
                if target is None:
                    continue
                route = a_star_search(self, start, target)
                if route:
                    cost = sum(self.get_cell_cost(x, y, target) for x, y in route[1:])
                    if cost < best_cost:
                        best_cost = cost
                        best_path = route

        return best_path, best_cost

    def check_all_component_connectors(self) -> Dict[Tuple[int,int], Dict]:
        """Check shortest connectors between every pair of components.

        Returns a dict keyed by (i, j) where i<j are 1-based component indices
        in the list returned by `get_cluster_components()`. Each value is a dict
        with keys: 'clusters' (tuple of cluster ids), 'path' (list of coords or None), and 'cost' (float).
        """
        components = self.get_cluster_components()
        results: Dict[Tuple[int,int], Dict] = {}

        for i in range(len(components)):
            for j in range(i+1, len(components)):
                comp_i = components[i]
                comp_j = components[j]
                path, cost = self.find_shortest_path_between_components(comp_i, comp_j)
                results[(i+1, j+1)] = {
                    'clusters': (sorted(comp_i), sorted(comp_j)),
                    'path': path,
                    'cost': cost,
                }

        return results


def a_star_search(world: World, start_pos: Tuple[int, int], target_pos: Tuple[int, int]):
    tx, ty = target_pos

    # If target is a node tile, we cannot step onto it. Instead, the goal is
    # to reach any adjacent cell to the target node.
    target_is_node = target_pos in world.node_set

    open_set = []
    best_g = {}

    # Initialize start positions: if start is a node, begin from its neighbors
    # (we cannot build on node cells). Otherwise start at start_pos.
    start_positions = []
    if start_pos in world.node_set:
        sx, sy = start_pos
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = (sx + dx, sy + dy)
            if 0 <= nb[0] < world.x and 0 <= nb[1] < world.y:
                if nb not in world.node_set:
                    # --- TAMBAHKAN FILTER LOGIKA INI ---
                    # Jika tetangga kota awal ini ternyata adalah GUNUNG (inf), JANGAN dimasukkan!
                    if world.get_cell_cost(nb[0], nb[1], target_pos) != float('inf'):
                        start_positions.append(nb)
                    # -----------------------------------
    else:
        # Jika start_pos bukan node kota, pastikan dia juga bukan gunung
        if world.get_cell_cost(start_pos[0], start_pos[1], target_pos) != float('inf'):
            start_positions.append(start_pos)

    for sp in start_positions:
        h = abs(sp[0] - tx) + abs(sp[1] - ty)
        # Determine initial direction if starting from a node
        last_dir = None
        if start_pos in world.node_set:
            last_dir = (sp[0] - start_pos[0], sp[1] - start_pos[1])
        heapq.heappush(open_set, (h, 0.0, sp, [sp], last_dir))
        best_g[(sp, last_dir)] = 0.0

    while open_set:
        _priority_, current_g, current, path, last_dir = heapq.heappop(open_set)

        # 1. PINDAHKAN PENGECEKAN SUKSES KE BAWAH SETELAH VALIDASI COST!
        # Jangan langsung return di sini jika petak yang sedang diinjak ternyata ilegal/inf!

        if current_g > best_g.get((current, last_dir), float('inf')):
            continue

        cx, cy = current
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = cx + dx, cy + dy
            neighbor = (nx, ny)

            # Skip jika di luar batas grid
            if not (0 <= nx < world.x and 0 <= ny < world.y):
                continue

            # Skip jika menabrak bangunan kota lain
            if neighbor in world.node_set:
                continue

            # --- KUNCI UTAMA PERBAIKAN ---
            # Cek cost sel tujuan. Jika bernilai INF (Gunung), MUTLAK dilarang diinjak!
            if world.get_cell_cost(nx, ny, target_pos) == float('inf'):
                continue
            # ------------------------------

            # SEKARANG AMAN UNTUK CEK APAKAH TETANGGA INI SUDAH MENCAPAI TARGET
            if target_is_node:
                if abs(nx - tx) + abs(ny - ty) == 1:
                    return path + [neighbor] # Kembalikan jalur sukses yang valid dan legal!
            else:
                if neighbor == target_pos:
                    return path + [neighbor]

            new_dir = (dx, dy)
            turn_cost = 0.0
            if last_dir is not None and last_dir != new_dir:
                # Turn penalty to model civil engineering alignment (preferring straight lines and avoiding zig-zags)
                turn_cost = 15.0
            ph = 1.0
            if hasattr(world, 'pheromones'):
                ph = world.pheromones[nx][ny]

            tentative_g = current_g + (world.get_cell_cost(nx, ny, target_pos) / ph) + turn_cost

            if tentative_g < best_g.get((neighbor, new_dir), float('inf')):
                best_g[(neighbor, new_dir)] = tentative_g
                f_total = tentative_g + (abs(nx - tx) + abs(ny - ty))
                heapq.heappush(open_set, (f_total, tentative_g, neighbor, path + [neighbor], new_dir))

    return None


if __name__ == "__main__":
    builder = WorldBuilder(size=(10, 10), num_nodes=50, random_nodes=True, de_path=50.0)
    builder.__print__()