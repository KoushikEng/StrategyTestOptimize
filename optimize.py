import pygmo as pg
from First15minBreak import read_from_csv, run
import numpy as np
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('symbol', type=str)
args = parser.parse_args()

SYMBOL = args.symbol
data = read_from_csv(SYMBOL)

t1 = time.time()
# Define the problem class for multi-objective optimization
class BreakoutProblem:
    def fitness(self, params):
        sl_multi, tp_multi = params

        # Calculate the return (negative for pygmo's minimization approach)
        _, return_val, win_probability = run(*data, ATR_SL_MULTIPLIER=sl_multi, ATR_TP_MULTIPLIER=tp_multi)

        # Since pygmo minimizes, we return the negative of win probability
        return [-return_val, -win_probability, sl_multi, -tp_multi]

    def get_bounds(self):
        # Define bounds for SL and TP adjustments
        return ([0.7, 1.3], [3.0, 3.5])

    def get_nobj(self):
        # Specify the number of objectives (2 in this case)
        return 4

# Create a problem instance
prob = pg.problem(BreakoutProblem())

# Define the algorithm (e.g., NSGA-II for multi-objective optimization)
algo = pg.algorithm(pg.nsga2(gen=100))  # 100 generations

# Create a population
pop = pg.population(prob, size=40)  # 40 individuals

# Evolve the population
pop = algo.evolve(pop)

# Extract the Pareto front (best trade-offs)
pareto_f = pop.get_f()  # Objective values
pareto_x = pop.get_x()  # Corresponding parameters

# Display results
print("Pareto Front (Returns, Win Probability):")
for i in range(len(pareto_f)):
    print(f"Returns: {-pareto_f[i][0]:.4f}, Win Probability: {-pareto_f[i][1]:.4f}, Parameters: {pareto_x[i]}")

# Identify the best trade-offs based on preferences
# Example: Select the solution with the highest weighted sum of objectives
weights = [0.8, 1.5]  # Adjust weights to prioritize one objective over the other
best_index = np.argmax([sum(-np.array(f[:-2]) * weights) for f in pareto_f])

best_solution = pareto_x[best_index]
best_fitness = pareto_f[best_index]
print("\nBest Trade-Off Solution (Based on Weighted Preferences):")
print(f"SL multiplier: {best_solution[0]:.4f}, TP multiplier: {best_solution[1]:.4f}")
print(f"Returns: {-best_fitness[0]:.4f}, Win Probability: {-best_fitness[1]:.4f}")

t2 = time.time()
print(f"Time took: {t2 - t1:.2f} seconds")
