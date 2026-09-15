import sys
import time
import random
import gzip


# parse clause string like "0.5 2 1 -3 -4 0" into list of literals
# first value is the weight (skip it), stop at the terminating 0
def parse_clause(clause_str):
    parts = clause_str.strip().split()
    literals = []
    for p in parts[1:]:
        val = int(p)
        if val == 0:
            break
        literals.append(val)
    return literals


# check if a single clause is satisfied by the given assignment
# positive literal e.g. 3 means variable 3 must be 1
# negative literal e.g. -3 means variable 3 must be 0
def check_clause(literals, assignment):
    for lit in literals:
        if lit > 0:
            if assignment[lit - 1] == '1':
                return True
        else:
            if assignment[abs(lit) - 1] == '0':
                return True
    return False


def exercise1(clause_str, assignment):
    literals = parse_clause(clause_str)
    if check_clause(literals, assignment):
        print(1)
    else:
        print(0)


# read a WDIMACS file (plain .wcnf or gzip-compressed .wcnf.gz)
# returns number of variables and a list of clause literal lists
def parse_wdimacs(filename):
    clauses = []
    n_vars = 0

    if filename.endswith('.gz'):
        fh = gzip.open(filename, 'rt', encoding='utf-8')
    else:
        fh = open(filename, 'r')

    with fh as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                # header: p wcnf <n_vars> <n_clauses> [<top>]
                parts = line.split()
                n_vars = int(parts[2])
                continue
            # clause line: <weight> <lit1> <lit2> ... 0
            parts = line.split()
            literals = []
            for p in parts[1:]:
                val = int(p)
                if val == 0:
                    break
                literals.append(val)
            if literals:
                clauses.append(literals)

    return n_vars, clauses


# count how many clauses in the formula are satisfied by assignment
def count_satisfied(clauses, assignment):
    count = 0
    for clause in clauses:
        if check_clause(clause, assignment):
            count += 1
    return count


def exercise2(wdimacs_file, assignment):
    n_vars, clauses = parse_wdimacs(wdimacs_file)
    print(count_satisfied(clauses, assignment))


# k-tournament selection: sample k individuals, return the fittest one
def tournament_select(population, fitness, k):
    indices = random.sample(range(len(population)), k)
    best = indices[0]
    for idx in indices[1:]:
        if fitness[idx] > fitness[best]:
            best = idx
    return population[best]


# uniform crossover: each bit is independently drawn from one of the two parents
def crossover(parent1, parent2):
    child = []
    for i in range(len(parent1)):
        if random.random() < 0.5:
            child.append(parent1[i])
        else:
            child.append(parent2[i])
    return ''.join(child)


# per-bit mutation: flip each bit independently with probability rate
def mutate(individual, rate):
    bits = list(individual)
    for i in range(len(bits)):
        if random.random() < rate:
            bits[i] = '0' if bits[i] == '1' else '1'
    return ''.join(bits)


def exercise3(wdimacs_file, time_budget, repetitions):
    n_vars, clauses = parse_wdimacs(wdimacs_file)

    # EA parameters
    pop_size = 100
    k = 3                    # tournament size 
    mut_rate = 1.0 / n_vars  # standard per-bit mutation rate
    cx_prob = 0.8            # probability of applying crossover to two parents

    for rep in range(repetitions):
        # randomly initialise the population before each repetition
        population = [''.join(random.choice('01') for _ in range(n_vars))
                      for _ in range(pop_size)]
        fitness = [count_satisfied(clauses, ind) for ind in population]

        best_idx = fitness.index(max(fitness))
        best_fitness = fitness[best_idx]
        best_solution = population[best_idx]

        # generation counter - initial population counts as generation 1
        gens = 1
        start = time.time()

        while time.time() - start < time_budget:
            # 1-elitism: seed the next generation with the current best
            next_pop = [best_solution]
            next_fit = [best_fitness]

            for _ in range(pop_size - 1):
                p1 = tournament_select(population, fitness, k)
                p2 = tournament_select(population, fitness, k)

                # crossover with probability cx_prob, otherwise pass p1 through
                if random.random() < cx_prob:
                    child = crossover(p1, p2)
                else:
                    child = p1

                child = mutate(child, mut_rate)
                cf = count_satisfied(clauses, child)

                next_pop.append(child)
                next_fit.append(cf)

                if cf > best_fitness:
                    best_fitness = cf
                    best_solution = child

            population = next_pop
            fitness = next_fit
            gens += 1

        print(f"{gens * pop_size}\t{best_fitness}\t{best_solution}")


# parse command-line arguments and dispatch to the correct exercise
if __name__ == '__main__':
    args = sys.argv[1:]

    # build a dict from "-key value" pairs
    arg_dict = {}
    i = 0
    while i < len(args):
        key = args[i].lstrip('-')
        if i + 1 < len(args) and not args[i + 1].startswith('-'):
            arg_dict[key] = args[i + 1]
            i += 2
        else:
            arg_dict[key] = True
            i += 1

    question = int(arg_dict.get('question', 0))

    if question == 1:
        exercise1(arg_dict['clause'], arg_dict['assignment'])

    elif question == 2:
        exercise2(arg_dict['wdimacs'], arg_dict['assignment'])

    elif question == 3:
        exercise3(
            arg_dict['wdimacs'],
            float(arg_dict['time_budget']),
            int(arg_dict['repetitions'])
        )

    else:
        print("Usage: python sae324.py -question [1|2|3] ...")
