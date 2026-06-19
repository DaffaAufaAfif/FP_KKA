import random


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
