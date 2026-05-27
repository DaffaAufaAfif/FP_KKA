# world.py
import random
import heapq

class WorldBuilder:
    def __init__(self, size: tuple[int, int] = (10, 10), num_nodes: int = 10, random_nodes: bool = True, de_path: float = 10.0, inp: list[tuple[int, int]] = []):
        if de_path < 0:
            raise ValueError("Default path value cant be less than zero!")
        
        self.x, self.y = size
        self.n = num_nodes
        self.de_path = float(de_path)
        
        if (self.x * self.y) < self.n:
            raise ValueError("Ukuran grid terlalu kecil untuk jumlah node tersebut.")
            
        self._map = [[self.de_path for _ in range(self.y)] for _ in range(self.x)]
        self.node_positions = {}
        
        if random_nodes:
            self._randomize()
        else:
            self._manual(inp)
            
    def _randomize(self):
        all_positions = [(i, j) for i in range(self.x) for j in range(self.y)]
        holder = random.sample(all_positions, self.n)
        
        for index, (nx, ny) in enumerate(holder):
            self._map[nx][ny] = -(index + 1)
            self.node_positions[index + 1] = (nx, ny)
            
    def _manual(self, inp):
        for index, (nx, ny) in enumerate(inp[:self.n]):
            if 0 <= nx < self.x and 0 <= ny < self.y: # Koreksi penulisan variabel koordinat batas
                self._map[nx][ny] = -(index + 1)
                self.node_positions[index + 1] = (nx, ny)


class World:
    def __init__(self, x: int, y: int, node_positions: dict, default_cost: float, threshold: int = 1, growth_rate: float = 2.0, discount_factor: float = 0.2):
        self.x = x          
        self.y = y          
        self.node_pos = node_positions  
        self.node_set = set(node_positions.values()) # Pencarian O(1) super cepat
        
        self.default_cost = default_cost        
        self.max_traf = threshold               
        self.growth_rate = growth_rate          
        self.discount_factor = discount_factor  
        
        self.road_layers = [[0 for _ in range(self.y)] for _ in range(self.x)]

    def reset_world(self):
        self.road_layers = [[0 for _ in range(self.y)] for _ in range(self.x)]

    def add_road_path(self, path: list):
        for (px, py) in path:
            if 0 <= px < self.x and 0 <= py < self.y:
                self.road_layers[px][py] += 1

    def get_cell_cost(self, x: int, y: int, target_pos: tuple) -> float:
        if not (0 <= x < self.x and 0 <= y < self.y):
            return float('inf')
            
        current_pos = (x, y)
        
        if current_pos == target_pos:
            return 0.0  
            
        if current_pos in self.node_set:
            return float('inf')

        num_layers = self.road_layers[x][y]
        if num_layers == 0:
            return self.default_cost  
        elif num_layers <= self.max_traf:
            return self.default_cost * self.discount_factor  
        else:
            excess_layers = num_layers - self.max_traf
            return self.default_cost * (self.growth_rate ** excess_layers)


def a_star_search(world: World, start_pos: tuple, target_pos: tuple):
    """Algoritma A* Versi Super Optimasi."""
    tx, ty = target_pos
    open_set = []
    
    start_h = abs(start_pos[0] - tx) + abs(start_pos[1] - ty)
    heapq.heappush(open_set, (start_h, 0.0, start_pos, [start_pos]))
    
    best_g = {start_pos: 0.0}
    
    while open_set:
        f_score, current_g, current, path = heapq.heappop(open_set)
        
        if current == target_pos:
            return path
            
        if current_g > best_g.get(current, float('inf')):
            continue
            
        cx, cy = current
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = cx + dx, cy + dy
            neighbor = (nx, ny)
            
            tentative_g = current_g + world.get_cell_cost(nx, ny, target_pos)
            
            if tentative_g < best_g.get(neighbor, float('inf')):
                best_g[neighbor] = tentative_g
                f_total = tentative_g + (abs(nx - tx) + abs(ny - ty))
                heapq.heappush(open_set, (f_total, tentative_g, neighbor, path + [neighbor]))
                
    return None
# ==========================================
# SIMULASI DENGAN VALUE CUSTOM DARI USER
# ==========================================
if __name__ == "__main__":
    # Misalkan user menginput nilai default path yang cukup besar, misal: 100.0
    USER_CUSTOM_DE_PATH = 100.0
    print(f"--- Menginisialisasi Peta (Default Cost: {USER_CUSTOM_DE_PATH}) ---")
    
    builder = WorldBuilder(size=(10, 10), num_nodes=5, random_nodes=True, de_path=USER_CUSTOM_DE_PATH)
    
    my_world = World(
        x=builder.x, 
        y=builder.y, 
        node_positions=builder.node_positions, 
        default_cost=builder.de_path, # Otomatis menggunakan input user
        threshold=1,                  # Maksimal x layer jalan bersama sebelum macet
        growth_rate=1.5,              # Naik x lipat setiap tumpukan kemacetan
        discount_factor=0.5           # Sharing path hanya dikenakan biaya x% dari default
    )
    
    # Tampilkan simulasi nilai biaya dinamisnya saat ini
    print(f"\nSimulasi perhitungan biaya pada sel jalan:")
    print(f"  0 Tumpukan (Lahan kosong)   = {my_world.get_cell_cost(-1, -1, None) if False else my_world.default_cost} cost")
    
    # Kita manipulasi layer secara manual untuk melihat kalkulasi biaya eksponensialnya
    my_world.road_layers[0][0] = 1
    print(f"  1 Tumpukan (Sharing Path)   = {my_world.get_cell_cost(0, 0, (9,9))} cost (Diskon)")
    
    my_world.road_layers[0][0] = 2
    print(f"  2 Tumpukan (Macet Layer 1)  = {my_world.get_cell_cost(0, 0, (9,9))} cost (Mulai Membengkak)")
    
    my_world.road_layers[0][0] = 3
    print(f"  3 Tumpukan (Macet Layer 2)  = {my_world.get_cell_cost(0, 0, (9,9))} cost (Eksponensial!)")
    
    # Cari Rute Nyata
    if 1 in my_world.node_pos and 2 in my_world.node_pos:
        start = my_world.node_pos[1]
        target = my_world.node_pos[2]
        print(f"\nMenjalankan A* dari Kota 1 {start} ke Kota 2 {target}...")
        route = a_star_search(my_world, start, target)
        print(f"Hasil Rute Tercepat: {route}")