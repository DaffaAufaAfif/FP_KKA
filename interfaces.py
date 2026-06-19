from dataclasses import dataclass
from typing import List, Tuple

RoutePair = Tuple[Tuple[int, int], Tuple[int, int]]
Path = List[Tuple[int, int]]


@dataclass
class Chromosome:
    genes: List[int]


@dataclass
class GAConfig:
    pop_size: int = 20
    generations: int = 20
    mutation_rate: float = 0.15


@dataclass
class GAResult:
    best_chromosome: Chromosome | None
    best_score: float
    history: List[float]
