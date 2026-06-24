import random
from typing import List, Tuple
from model.world import a_star_search

# Module-level history of generations: list of tuples (best_chromosome, best_cost, best_paths)
gens_history: list[tuple] = []

def evaluate_chromosome(chromosome: List[int], world, pairs: List[Tuple[int, int]], return_paths: bool = False):
    """Evaluate total cost for a chromosome (routing order) by running A* for each pair.
    
    This sequential routing is guided by pheromone levels on the world grid.
    """
    world.reset_world()
    routed_info = []
    extra_count = 0

    for pair_idx in chromosome:
        start_node, target_node = pairs[pair_idx]
        start_c = world.cluster_of_node(start_node)
        target_c = world.cluster_of_node(target_node)

        if start_node == target_node:
            continue

        if start_c is not None and target_c is not None and start_c == target_c:
            continue

        route = None
        if start_c is not None and target_c is not None and start_c != target_c:
            route, _ = world.find_shortest_path_between_clusters(start_c, target_c)
        else:
            start_pos = world.node_pos[start_node]
            target_pos = world.node_pos[target_node]
            route = a_star_search(world, start_pos, target_pos)

        if route:
            world.add_road_path(route)
            routed_info.append((target_node, route))

        # Early exit check: route 5 extra pairs for redundancy, then stop
        try:
            if world.network_is_fully_connected():
                if extra_count >= 5:
                    break
                extra_count += 1
        except Exception:
            pass

    # Enforce full connectivity
    try:
        if not world.network_is_fully_connected():
            if return_paths:
                return float('inf'), []
            return float('inf')
    except Exception:
        pass

    # Calculate total cost based on physical road cost
    total_cost = 0.0
    for target_node, route in routed_info:
        target_pos = world.node_pos[target_node]
        route_cost = sum(world.get_cell_cost(x, y, target_pos) for x, y in route[1:])
        total_cost += route_cost

    # Cycle/Hamiltonian bonus
    road_cells = set()
    for x in range(world.x):
        for y in range(world.y):
            if world.road_layers[x][y] > 0:
                road_cells.add((x, y))

    if len(road_cells) > 0:
        E_road = 0
        for rx, ry in road_cells:
            for dx, dy in ((1, 0), (0, 1)):
                nx, ny = rx + dx, ry + dy
                if (nx, ny) in road_cells:
                    E_road += 1
        V_road = len(road_cells)
        num_cycles = E_road - V_road + 1
        if num_cycles >= 1:
            total_cost -= 1000.0

    if return_paths:
        # Mengambil kumpulan list koordinat [(x1,y1), (x2,y2), ...] dari rute yang dibangun
        all_paths = [route for _, route in routed_info]
        return total_cost, all_paths

    return total_cost


def run_genetic_algorithm(world, pairs, pop_size=20, generations=20, mutation_rate=0.15):
    """Run Ant Colony Optimization (ACO) to find the optimal road layout.
    
    Keeps the function name and signature for compatibility with the UI.
    """
    num_pairs = len(pairs)
    if num_pairs == 0:
        return None, 0.0

    # Initialize pheromone grid
    world.pheromones = [[1.0 for _ in range(world.y)] for _ in range(world.x)]
    
    best_overall_chromosome = None
    best_overall_cost = float('inf')
    
    # ACO Parameters
    evaporation_rate = 0.1
    Q = 5000.0  # Pheromone deposit factor

    print(f"\n--- Memulai Ant Colony Optimization ({generations} Iterasi) ---")
    print(f"Total Pasangan Rute: {num_pairs}")
    print(f"Jumlah Kluster: {len(world.cluster_members)}")

    # reset module-level generation history for this run
    gens_history.clear()
    for gen in range(generations):
        # Spawn colony of ants
        ants_chromosomes = []
        if best_overall_chromosome is not None:
            # Elitism: keep best solution
            ants_chromosomes.append(best_overall_chromosome.copy())
            
        while len(ants_chromosomes) < pop_size:
            # Each ant explores a different routing order
            chrom = random.sample(range(num_pairs), num_pairs)
            ants_chromosomes.append(chrom)

        # Evaluate each ant's solution
        cost_scores = []
        for chrom in ants_chromosomes:
            cost = evaluate_chromosome(chrom, world, pairs)
            cost_scores.append(cost)

        # Find the best ant of this generation
        best_gen_cost = float('inf')
        best_gen_chrom = None
        for i, cost in enumerate(cost_scores):
            if cost < best_gen_cost:
                best_gen_cost = cost
                best_gen_chrom = ants_chromosomes[i]

        if best_gen_cost < best_overall_cost:
            best_overall_cost = best_gen_cost
            best_overall_chromosome = best_gen_chrom.copy()

        print(f"  Iterasi {gen + 1:02d}: Total Biaya Jaringan Terbaik = {best_overall_cost:.2f}")

        # Evaporate pheromones
        for x in range(world.x):
            for y in range(world.y):
                world.pheromones[x][y] = max(1.0, world.pheromones[x][y] * (1.0 - evaporation_rate))

        # Deposit pheromones for the best solution of this generation
        best_gen_paths = []
        if best_gen_chrom is not None and best_gen_cost != float('inf'):
            # Rebuild roads of the best generation ant to see its paths and extract them
            _, best_gen_paths = evaluate_chromosome(best_gen_chrom, world, pairs, return_paths=True)
            for x in range(world.x):
                for y in range(world.y):
                    if world.road_layers[x][y] > 0:
                        world.pheromones[x][y] += Q / best_gen_cost
                        
        # store the best chromosome, its generation cost, and its generated path sequences
        gens_history.append((best_gen_chrom, best_gen_cost, best_gen_paths))

    return best_overall_chromosome, best_overall_cost


def get_gen(i: int):
    """Return (chromosome, cost, paths) for generation index `i` (0-based).

    Returns (None, None, None) if index out of range.
    """
    if not isinstance(i, int):
        raise TypeError("generation index must be an integer")
    if i < 0 or i >= len(gens_history):
        return None, None, None
    return gens_history[i]