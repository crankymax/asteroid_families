import itertools
from datetime import datetime

import pandas as pd

import rebound
import numpy as np
import time
from rebound.interruptible_pool import InterruptiblePool
import warnings


def run_sim(sim_params):
    sim_file, run_length = sim_params
    results = {'file': sim_file.split('sim_')[1][:4], 'int_length': str(run_length)}
    sim = rebound.Simulation(sim_file)
    # record the number of particles
    results['n_particles'] = len(sim.particles) - sim.N_active
    # Create 1000 evenly spaced integrations
    log_time = 1000
    # Integrate for run_length years
    times = np.linspace(0, run_length * 2 * np.pi, log_time)
    start = time.time()

    x = np.zeros((sim.N, log_time))
    y = np.zeros((sim.N, log_time))

    # Capture warning messages (WHFast timestep too large)
    print(f'+{results["file"]} {run_length}')
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for ti, t in enumerate(times):
            sim.integrate(t, exact_finish_time=0)
            for i, p in enumerate(sim.particles):
                x[i][ti] = p.x
                y[i][ti] = p.y

    print(f'-{results["file"]} {run_length}: {time.time()-start}')
    results['clock_time'] = time.time()-start
    return results


if __name__ == '__main__':
    params = list(itertools.product([f'./luthera_sims/luther_sim_{sim_no:04}.bin' for sim_no in range(6)],
                               [1.e6, 2.5e6, 5.e6, 7.5e6, 1.e7]))
    pool = InterruptiblePool(processes=3)
    res = pool.map(run_sim, params)
    print(res)
    results_df = pd.DataFrame.from_dict(res)
    results_df.to_pickle(f"results_{datetime.today().strftime('%Y%m%d_%H%M')}.pkl")



