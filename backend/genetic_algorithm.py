import numpy as np


class GeneticAlgorithm:
    """
    Simple continuous Genetic Algorithm for OptiAgent.

    The optimizer minimizes the supplied objective function.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        population_size=30,
        generations=50,
        mutation_rate=0.1,
        crossover_rate=0.8,
        mutation_scale=0.1,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)

        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.mutation_scale = mutation_scale

        self.population = self._initialize_population()

        self.personal_best_positions = self.population.copy()
        self.personal_best_scores = np.array(
            [self.objective_function(x) for x in self.population]
        )

        best_index = np.argmin(self.personal_best_scores)

        self.global_best_position = (
            self.personal_best_positions[best_index].copy()
        )
        self.global_best_score = float(
            self.personal_best_scores[best_index]
        )

        self.history = [self.global_best_score]

    def _initialize_population(self):
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]

        return np.random.uniform(
            lower,
            upper,
            size=(self.population_size, self.dimensions),
        )

    def _select_parent(self):
        """
        Tournament selection.
        """
        i, j = np.random.randint(0, self.population_size, size=2)

        if self.personal_best_scores[i] < self.personal_best_scores[j]:
            return self.population[i].copy()

        return self.population[j].copy()

    def _crossover(self, parent1, parent2):
        if np.random.random() > self.crossover_rate:
            return parent1.copy()

        mask = np.random.random(self.dimensions) < 0.5

        child = np.where(mask, parent1, parent2)

        return child

    def _mutate(self, individual):
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]

        search_range = upper - lower

        for i in range(self.dimensions):
            if np.random.random() < self.mutation_rate:
                individual[i] += np.random.normal(
                    0,
                    self.mutation_scale * search_range[i],
                )

        return np.clip(individual, lower, upper)

    def _update_best(self):
        scores = np.array(
            [self.objective_function(x) for x in self.population]
        )

        improved = scores < self.personal_best_scores

        self.personal_best_scores[improved] = scores[improved]
        self.personal_best_positions[improved] = self.population[improved]

        best_index = np.argmin(self.personal_best_scores)

        if (
            self.personal_best_scores[best_index]
            < self.global_best_score
        ):
            self.global_best_score = float(
                self.personal_best_scores[best_index]
            )

            self.global_best_position = (
                self.personal_best_positions[best_index].copy()
            )

    def optimize(self):
        for generation in range(self.generations):

            new_population = []

            # Preserve the best individual (elitism)
            elite_index = np.argmin(self.personal_best_scores)

            new_population.append(
                self.personal_best_positions[elite_index].copy()
            )

            while len(new_population) < self.population_size:

                parent1 = self._select_parent()
                parent2 = self._select_parent()

                child = self._crossover(parent1, parent2)
                child = self._mutate(child)

                new_population.append(child)

            self.population = np.array(new_population)

            self._update_best()

            self.history.append(self.global_best_score)

        return {
            "best_position": self.global_best_position.copy(),
            "best_score": self.global_best_score,
            "history": self.history.copy(),
            "algorithm": "Genetic Algorithm",
        }