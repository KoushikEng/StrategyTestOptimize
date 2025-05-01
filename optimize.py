import pygmo as pg
from First15minBreak import run
import numpy as np
import argparse
import time
from Utilities import read_from_csv
from ConsoleAnimator import ConsoleAnimator

anim = ConsoleAnimator()

parser = argparse.ArgumentParser()
parser.add_argument('symbol', type=str)
parser.add_argument('--trail', action='store_true')
parser.add_argument('-p', type=int, default=80, help="population size")
parser.add_argument('-g', type=int, default=200, help="Algorithm generation size")
args = parser.parse_args()

SYMBOL = args.symbol.upper()
data = read_from_csv(SYMBOL)

t1 = time.time()
# Define the problem class for multi-objective optimization
class BreakoutProblem:
    def fitness(self, params):
        ema, ema_slope, atr, avg_vol, trail_multi, vol_multi, sl_multi, tp_multi = params

        # Calculate the return (negative for pygmo's minimization approach)
        _, return_val, win_probability = run(*data, ema=ema, ema_slope=ema_slope, atr=atr, trail_multi=trail_multi, avg_vol=avg_vol, vol_multi=vol_multi, sl_multi=sl_multi, tp_multi=tp_multi, trail=args.trail)

        # Since pygmo minimizes, we return the negative of win probability
        return [-return_val, -win_probability, sl_multi, -tp_multi]

    def get_bounds(self):
        # Define bounds for SL and TP adjustments
        return ([9, 9, 9, 9, 0.4, 1.3, 0.7, 1.3], [35, 35, 35, 35, 2.0, 2.5, 3.0, 3.5])

    def get_nobj(self):
        # Specify the number of objectives (2 in this case)
        return 4

# Create a problem instance
prob = pg.problem(BreakoutProblem())

# Define the algorithm (e.g., NSGA-II for multi-objective optimization)
algo = pg.algorithm(pg.nsga2(gen=400))  # 100 generations

anim.start("Creating population...")
# Create a population
pop = pg.population(prob, size=160)  # 40 individuals
anim.done()

anim.start("Evolving the population...")
# Evolve the population
pop = algo.evolve(pop)
anim.done("optimization complete")

# Extract the Pareto front (best trade-offs)
pareto_f = pop.get_f()  # Objective values
pareto_x = pop.get_x()  # Corresponding parameters

# Display results
print(f"Pareto Front {len(pareto_f)} (Returns, Win Probability):")
for i in range(len(pareto_f)):
    print(f"Returns: {-pareto_f[i][0]:.4f}, Win Probability: {-pareto_f[i][1]:.4f}, Parameters: {pareto_x[i]}")

# Identify the best trade-offs based on preferences
# Example: Select the solution with the highest weighted sum of objectives
weights = [0.8, 1.5]  # Adjust weights to prioritize one objective over the other
best_index = np.argmax([sum(-np.array(f[:-2]) * weights) for f in pareto_f])

best_solution = pareto_x[best_index]
best_fitness = pareto_f[best_index]
print("\nBest Trade-Off Solution (Based on Weighted Preferences):")
ema, ema_slope, atr, avg_vol, trail_multi, vol_multi, sl_multi, tp_multi = best_solution
print(f"\
    EMA period: {ema:.4f}\n\
    EMA slope period: {ema_slope:.4f}\n\
    ATR period: {atr:.4f}\n\
    Avg vol (EMA) period: {avg_vol:.4f}\n\
    ATR trailing multiplier: {trail_multi:.4f}\n\
    Vol multiplier: {vol_multi:.4f}\n\
    SL multiplier: {sl_multi:.4f}\n\
    TP multiplier: {tp_multi:.4f}\n\
")
# print(f"SL multiplier: {best_solution[0]:.4f}, TP multiplier: {best_solution[1]:.4f}")
print(f"Returns: {-best_fitness[0]:.4f}, Win Probability: {-best_fitness[1]:.4f}")

print(f"\nRun to test: python main.py {SYMBOL} trail_multi={round(trail_multi, 1)} sl_multi={round(sl_multi, 1)} tp_multi={round(tp_multi, 1)} ema={round(ema)} ema_slope={round(ema_slope)} atr={round(atr)} avg_vol={round(avg_vol)} vol_multi={round(vol_multi, 1)}\n")

t2 = time.time()
print(f"Time took: {t2 - t1:.2f} seconds")
