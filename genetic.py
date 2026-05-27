# main.py
import random
import itertools
# MENGIMPOR CLASS DAN FUNGSI DARI FILE world.py YANG BERADA DI FOLDER YANG SAMA
from world import WorldBuilder, World, a_star_search

def evaluate_chromosome(chromosome, world, pairs):
    """Fungsi Fitness: Menghitung total biaya pembuatan seluruh jaringan jalan."""
    world.reset_world()
    total_cost = 0.0
    
    for pair_idx in chromosome:
        start_node, target_node = pairs[pair_idx]
        start_pos = world.node_pos[start_node]
        target_pos = world.node_pos[target_node]
        
        route = a_star_search(world, start_pos, target_pos)
        
        if route:
            route_cost = sum(world.get_cell_cost(x, y, target_pos) for x, y in route[1:])
            total_cost += route_cost
            world.add_road_path(route)
        else:
            total_cost += 100000.0  # Penalti jika rute buntu
            
    return total_cost


def tournament_selection(population, cost_scores, k=3):
    selected = random.sample(list(zip(population, cost_scores)), k)
    selected.sort(key=lambda x: x[1])
    return selected[0][0]


def order_crossover(parent1, parent2):
    size = len(parent1)
    a, b = sorted(random.sample(range(size), 2))
    
    child = [-1] * size
    child[a:b+1] = parent1[a:b+1]
    
    p2_idx = 0
    for i in range(size):
        if child[i] == -1:
            while parent2[p2_idx] in child:
                p2_idx += 1
            child[i] = parent2[p2_idx]
            
    return child


def swap_mutation(chromosome, mutation_rate=0.15):
    if random.random() < mutation_rate:
        idx1, idx2 = random.sample(range(len(chromosome)), 2)
        chromosome[idx1], chromosome[idx2] = chromosome[idx2], chromosome[idx1]


def run_genetic_algorithm(world, pairs, pop_size=20, generations=20, mutation_rate=0.15):
    num_pairs = len(pairs)
    if num_pairs == 0:
        return None, 0.0
        
    population = [random.sample(range(num_pairs), num_pairs) for _ in range(pop_size)]
    best_overall_chromosome = None
    best_overall_cost = float('inf')
    
    print(f"\n--- Memulai Algoritma Genetik ({generations} Generasi) ---")
    
    for gen in range(generations):
        cost_scores = [evaluate_chromosome(chrom, world, pairs) for chrom in population]
        
        for i, cost in enumerate(cost_scores):
            if cost < best_overall_cost:
                best_overall_cost = cost
                best_overall_chromosome = population[i].copy()
                
        print(f"  Generasi {gen + 1:02d}: Total Biaya Jaringan Terbaik = {best_overall_cost:.2f}")
        
        new_population = []
        min_idx = cost_scores.index(min(cost_scores))
        new_population.append(population[min_idx].copy()) # Elitisme
        
        while len(new_population) < pop_size:
            p1 = tournament_selection(population, cost_scores)
            p2 = tournament_selection(population, cost_scores)
            
            child = order_crossover(p1, p2)
            swap_mutation(child, mutation_rate)
            new_population.append(child)
            
        population = new_population
        
    return best_overall_chromosome, best_overall_cost


def cetak_peta_2d(world):
    """Mencetak visualisasi grid 2D yang menunjukkan kota dan intensitas jalan."""
    # Inisialisasi grid kosong dengan penanda titik '.'
    grid = [[" . " for _ in range(world.y)] for _ in range(world.x)]
    
    # 1. Plot Jalan/Edge berdasarkan jumlah layer di koordinat tersebut
    for x in range(world.x):
        for y in range(world.y):
            layers = world.road_layers[x][y]
            if layers > 0:
                if layers <= world.max_traf:
                    # Menampilkan tanda '#' diikuti jumlah layer jalan yang menumpuk aman
                    grid[x][y] = f" #{layers}" 
                else:
                    # Menampilkan tanda angka diikuti '!' jika tumpukannya sudah macet eksponensial
                    grid[x][y] = f" {layers}!" 
                    
    # 2. Plot Kota/Node di atas jalan agar tidak tertutup rute jalan
    for city_id, (nx, ny) in world.node_pos.items():
        grid[nx][ny] = f" K{city_id}"  # K = Kota / Node
        
    # 3. Tampilkan ke Terminal
    print("\n================== VISUALISASI PETA 2D ==================")
    print("Keterangan Simbol:")
    print("  K1, K2... = Posisi Kota/Node")
    print("  #1, #2    = Rute Jalan Bersama (Aman / Dapat Diskon Sharing Path)")
    print("  2!, 3!    = Jalan Macet Parah (Kena Penalti Eksponensial)")
    print("  .         = Area Kosong / Lahan Kosong\n")
    
    # Cetak Nomor Kolom (Sumbu Y)
    print("    " + "".join(f" {y:02d}" for y in range(world.y)))
    print("    " + "---" * world.y)
    
    # Cetak Baris demi Baris (Sumbu X)
    for x in range(world.x):
        baris_teks = f"{x:02d} |"
        for y in range(world.y):
            baris_teks += grid[x][y]
        print(baris_teks)
    print("=========================================================")


# ==========================================
# SIMULASI INTEGRASI UTAMA
# ==========================================
if __name__ == "__main__":
    USER_DE_PATH = 50.0  
    JUMLAH_NODE = 6       
    
    # 1. Inisialisasi Dunia
    builder = WorldBuilder(size=(10, 10), num_nodes=JUMLAH_NODE, random_nodes=True, de_path=USER_DE_PATH)
    
    my_world = World(
        x=builder.x, 
        y=builder.y, 
        node_positions=builder.node_positions, 
        default_cost=builder.de_path,
        threshold=2,       
        growth_rate=2.0,   
        discount_factor=0.01 
    )
    
    print("Posisi Koordinat Kota yang Terbentuk:")
    for city_id, pos in my_world.node_pos.items():
        print(f"  Kota {city_id} -> {pos}")
        
    # 2. Otomatisasi Jaringan Kombinasi Semua Jalur (All-to-All)
    daftar_id_kota = list(my_world.node_pos.keys())
    daftar_rute = list(itertools.combinations(daftar_id_kota, 2))
        
    # 3. Jalankan GA
    best_order, best_cost = run_genetic_algorithm(my_world, daftar_rute, pop_size=30, generations=20)
    
    # 4. TERAPKAN KROMOSOM TERBAIK KE DUNIA UNTUK VISUALISASI
    # Evaluasi ulang agar `my_world.road_layers` benar-benar berisi konfigurasi jalan terbaik
    evaluate_chromosome(best_order, my_world, daftar_rute)
    
    # 5. Cetak Hasil Teks & Visualisasi Peta
    print("\n================ HASIL OPTIMASI GA ================")
    print(f"Urutan Indeks Pembuatan Rute Terbaik: {best_order}")
    print(f"Total Biaya Seluruh Jaringan Terpilih: {best_cost:.2f}")
    
    # Memanggil fungsi gambaran 2D
    cetak_peta_2d(my_world)