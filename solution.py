"""62136"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Generator, Set, Tuple, List

from copy import deepcopy
from math import sqrt, factorial, inf
from random import randint, random, shuffle

@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def distance_to(self, other: Point) -> float:
        deltaX = self.x - other.x
        deltaY = self.y - other.y
        return sqrt(deltaX*deltaX + deltaY*deltaY)


class World:
    points: Tuple[Point, ...]

    COORDINATE_MIN = 0
    COORDINATE_MAX = 69420

    def __init__(self, points_count: int):
        points_set: Set[Point] = set()
        while len(points_set) < points_count:
            x = randint(self.COORDINATE_MIN, self.COORDINATE_MAX)
            y = randint(self.COORDINATE_MIN, self.COORDINATE_MAX)
            points_set.add(Point(x, y))
        self.points = tuple(points_set)

@dataclass(frozen=True)
class PossibleSolution:
    path: Tuple[int, ...]
    """The solution consists of a list of the points' indexes."""

    def __str__(self) -> str:
        return "->".join(map(str, self.path))

    def cost(self, world: World) -> float:
        # result = 0.0
        # for i, p1_index in enumerate(self.path[:-1]):
        #     p2_index = self.path[i + 1]
        #     p1 = world.points[p1_index]
        #     p2 = world.points[p2_index]
        #     result += p1.distance_to(p2)
        return sum(
            world.points[p1_index].distance_to(world.points[self.path[i + 1]])
            for i, p1_index in enumerate(self.path[:-1])
        )


class EvolutionMachine:
    SELECTION_FRACTION = 0.5
    MUTATION_CHANCE = 0.1
    STOP_CONDITION_SAME_COUNT = 16

    def __init__(self, world: World):
        self.world = world
        size = len(world.points)
        self.population_size = size**2 if size > 4 else factorial(size)

        # Initial population
        population_set: Set[PossibleSolution] = set()
        while len(population_set) < self.population_size:
            new_path = list(range(len(world.points)))
            shuffle(new_path)
            population_set.add(PossibleSolution(tuple(new_path)))
        self.population = list(population_set)

    def __next__(self) -> PossibleSolution:
        new_generation: List[PossibleSolution] = []
        for s1, s2 in self.__selection():
            new_generation.extend(self.__crossover(s1, s2))
        self.__mutation(new_generation)
        self.__merge_generations(new_generation)
        return self.population[0]

    def __iter__(self) -> Generator[PossibleSolution, None, None]:
        same_count = 1
        last = +inf
        while same_count < self.STOP_CONDITION_SAME_COUNT - 1:
            next_solution = next(self)
            cost = next_solution.cost(self.world)
            same_count = 0 if cost != last else same_count + 1
            last = min(cost, last)
            yield next_solution

    def __selection(self) -> List[Tuple[PossibleSolution, PossibleSolution]]:
        """https://en.wikipedia.org/wiki/Fitness_proportionate_selection"""
        selection_count = int(self.population_size * self.SELECTION_FRACTION)
        if selection_count % 2 == 1:
            selection_count += 1

        self.population.sort(key=lambda s: self.__fitness(s))
        fitnesses = [self.__fitness(s) for s in self.population]
        total_fitness = sum(fitnesses)
        prev_probability = 0.0
        probabilites: List[float] = []
        for i in range(self.population_size):
            new_probability = prev_probability + (fitnesses[i] / total_fitness)
            probabilites.append(new_probability)
            prev_probability = new_probability

        selected: List[PossibleSolution] = []
        for _ in range(selection_count):
            p = random()
            selected_index = 0
            while p > probabilites[selected_index] and selected_index < selection_count - 2:
                selected_index += 1
            selected.append(self.population[selected_index])
        return list(zip(selected[:selection_count//2], selected[selection_count//2:]))

    def __crossover(
        self, s1: PossibleSolution, s2: PossibleSolution
    ) -> Tuple[PossibleSolution, PossibleSolution]:
        """https://en.wikipedia.org/wiki/Crossover_(genetic_algorithm)#Single-point_crossover"""
        i = randint(1, len(self.world.points)-1)
        i1, i2 = i, i
        first = s1.path[:i]
        second = s2.path[:i]
        specimen_len = len(self.world.points)
        while len(first) < specimen_len:
            current_chromosome = s2.path[i1 % specimen_len]
            if current_chromosome not in first:
                first = first + (current_chromosome,)
            i1 += 1
        while len(second) < specimen_len:
            current_chromosome = s1.path[i2 % specimen_len]
            if current_chromosome not in second:
                second = second + (current_chromosome,)
            i2 += 1
        assert len(first) == len(set(first)), "Crossover not valid!"
        assert len(second) == len(set(second)), "Crossover not valid!"
        return PossibleSolution(first), PossibleSolution(second)

    def __mutation(self, new_generation: List[PossibleSolution]):
        """Implementation uses inversion mutation type."""
        new_gen_copy = deepcopy(new_generation)
        for i, specimen in enumerate(new_gen_copy):
            if random() > self.MUTATION_CHANCE:
                continue

            chromosomes = list(specimen.path)
            size = len(chromosomes)
            subpath_start_index= randint(0, size-2)
            subpath_end_index = randint(subpath_start_index+1, size-1)
            inverted_subpath = list(reversed(chromosomes[subpath_start_index:subpath_end_index+1]))
            new_chromosomes = chromosomes[:subpath_start_index] + inverted_subpath + chromosomes[subpath_end_index+1:]
            assert len(new_chromosomes) == size, "Mutation not valid: size of specimen not correct"
            assert len(new_chromosomes) == len(set(new_chromosomes)), "Mutation produced an invalid specimen"
            new_generation[i] = PossibleSolution(tuple(new_chromosomes))


    def __merge_generations(self, children: List[PossibleSolution]):
        self.population.extend(children)
        self.__sort_population()
        self.population = self.population[:self.population_size]

    def __sort_population(self):
        self.population.sort(key=lambda s: s.cost(self.world))

    def __fitness(self, s: PossibleSolution) -> float:
        """Fitness function used in the selection process."""
        return sqrt(2) * len(self.world.points) - s.cost(self.world)


if __name__ == '__main__':
    from sys import argv
    if len(argv) >= 2:
        n = int(argv[1])
    else:
        n = int(input())

    world = World(n)
    machine = EvolutionMachine(world)

    iteration = 1
    last_cost = +inf
    for solution in machine:
        curr_cost = solution.cost(world)

        if curr_cost != last_cost:
            print(f"\nGeneration {iteration} -> Cost {curr_cost}")
        else:
            print(".", end="", flush=True)

        last_cost = curr_cost
        iteration+=1

    print(f"\nFinal generation ({iteration}) -> Cost {last_cost}")