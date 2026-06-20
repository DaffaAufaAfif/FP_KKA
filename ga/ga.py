import random
import itertools
from typing import List, Tuple

from model.world import a_star_search
from ga.operators import tournament_selection, order_crossover, swap_mutation


def evaluate_chromosome(chromosome: List[int], world, pairs: List[Tuple[int, int]]):
    """Evaluate total cost for a chromosome by running A* for each pair."""
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
            total_cost += 100000.0

    return total_cost


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
        new_population.append(population[min_idx].copy())

        while len(new_population) < pop_size:
            p1 = tournament_selection(population, cost_scores)
            p2 = tournament_selection(population, cost_scores)

            child = order_crossover(p1, p2)
            swap_mutation(child, mutation_rate)
            new_population.append(child)

        population = new_population

    return best_overall_chromosome, best_overall_cost
