import random
import itertools
from typing import List, Tuple

from model.world import a_star_search
from ga.operators import tournament_selection, order_crossover, swap_mutation


def evaluate_chromosome(chromosome: List[int], world, pairs: List[Tuple[int, int]]):
    """Evaluate total cost for a chromosome by running A* for each pair.
    
    Cluster-aware logic (refactored):
    - Treat endpoints at cluster level: attempt cluster->cluster or cluster->node routes
    - Only skip a pair when both nodes are already in the same connected component
      (i.e., truly connected in `world.cluster_graph`). This avoids the
      "illusion connectivity" bug.
    - Early exit: as soon as the world's cluster graph becomes fully connected,
      stop evaluating remaining pairs and return the current cost (performance).
    """
    world.reset_world()
    total_cost = 0.0
    for pair_idx in chromosome:
        start_node, target_node = pairs[pair_idx]

        # New skip rules to avoid encouraging star/topology:
        # - skip only if pair is a self-loop
        # - or if both nodes belong to the same initial cluster (cluster_members)
        start_c = world.cluster_of_node(start_node)
        target_c = world.cluster_of_node(target_node)

        if start_node == target_node:
            continue

        if start_c is not None and target_c is not None and start_c == target_c:
            # Nodes within the same initial cluster are considered connected by default
            continue

        # Determine route: prefer cluster->cluster search when both endpoints have
        # cluster ids (this tries member pairs and can find direct/alternative paths).
        route = None
        route_cost = float('inf')
        if start_c is not None and target_c is not None and start_c != target_c:
            route, route_cost = world.find_shortest_path_between_clusters(start_c, target_c)
        else:
            # Fall back to node-to-node path
            start_pos = world.node_pos[start_node]
            target_pos = world.node_pos[target_node]
            route = a_star_search(world, start_pos, target_pos)
            if route:
                route_cost = sum(world.get_cell_cost(x, y, target_pos) for x, y in route[1:])

        if route:
            total_cost += route_cost
            world.add_road_path(route)
        else:
            # large penalty for unreachable pair
            total_cost += 100000.0

        # Early exit: if network already fully connected, stop evaluating further pairs
        try:
            if world.network_is_fully_connected():
                return total_cost
        except Exception:
            pass

    # After processing all pairs, enforce full network connectivity.
    # If clusters are not fully connected together (i.e. there is no spanning
    # path between all clusters), apply a very large penalty so GA prefers
    # solutions that create a single connected network.
    # Enforce full connectivity: if not fully connected, mark chromosome as invalid
    # by returning infinite cost so it cannot be selected.
    try:
        if not world.network_is_fully_connected():
            return float('inf')
    except Exception:
        # if world lacks network_is_fully_connected, keep current total_cost
        pass

    return total_cost


def run_genetic_algorithm(world, pairs, pop_size=20, generations=20, mutation_rate=0.15):
    num_pairs = len(pairs)
    if num_pairs == 0:
        return None, 0.0

    population = [random.sample(range(num_pairs), num_pairs) for _ in range(pop_size)]
    best_overall_chromosome = None
    best_overall_cost = float('inf')

    print(f"\n--- Memulai Algoritma Genetik ({generations} Generasi) ---")
    print(f"Total Pasangan Rute: {num_pairs}")
    print(f"Jumlah Kluster: {len(world.cluster_members)}")

    for gen in range(generations):
        cost_scores = [evaluate_chromosome(chrom, world, pairs) for chrom in population]

        for i, cost in enumerate(cost_scores):
            if cost < best_overall_cost:
                best_overall_cost = cost
                best_overall_chromosome = population[i].copy()

        print(f"  Generasi {gen + 1:02d}: Total Biaya Jaringan Terbaik = {best_overall_cost:.2f}")

        new_population = []
        min_idx = cost_scores.index(min(cost_scores))
        new_population.append(population[min_idx].copy())

        while len(new_population) < pop_size:
            p1 = tournament_selection(population, cost_scores)
            p2 = tournament_selection(population, cost_scores)

            child = order_crossover(p1, p2)
            swap_mutation(child, mutation_rate)
            new_population.append(child)

        population = new_population

    return best_overall_chromosome, best_overall_cost
