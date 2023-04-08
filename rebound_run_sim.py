import itertools
from datetime import datetime
import h5py as h5
import pandas as pd

import rebound
import numpy as np
import time
from rebound.interruptible_pool import InterruptiblePool
import warnings


def run_sim(sim_params) -> dict:
    sim_file, run_length, run_time = sim_params
    sim_no = sim_file.split('sim_')[1][:4]
    stats = {'sim_number': sim_no}
    sim = rebound.Simulation(sim_file)
    # record the number of particles
    n_particles = len(sim.particles) - sim.N_active

    # Create evenly spaced integrations every run_length/1000
    log_time = int(run_length/1.0e3)
    vals: int = 9
    # Integrate for run_length years
    times = np.linspace(log_time, run_length * 2 * np.pi, log_time)
    start = time.time()

    run_values = np.zeros((log_time, n_particles, vals))
    # Capture warning messages (WHFast timestep too large)
    print(f'+{sim_no} {run_length}')
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for ti, t in enumerate(times):
            sim.integrate(t, exact_finish_time=0)
            for i, p in enumerate(sim.particles[sim.N_active:]):
                run_values[ti][i][0] = p.x
                run_values[ti][i][1] = p.y
                run_values[ti][i][2] = p.z
                run_values[ti][i][3] = p.vx
                run_values[ti][i][4] = p.vy
                run_values[ti][i][5] = p.vz
                run_values[ti][i][6] = p.a
                run_values[ti][i][7] = p.e
                run_values[ti][i][8] = p.inc

    sim.save(sim_file.replace(".bin", "_fin.bin"))
    print(f'-{sim_no} {run_length}: {time.time()-start}')
    stats['clock_time'] = time.time()-start
    stats['int_length'] = run_length

    with h5.File(f"./run_logs/luthera_sim_{run_time}_{sim_no}.h5", 'w') as run_log:
        run_log.attrs['simulation'] = sim_no
        run_log.attrs['int_length'] = run_length
        run_log.attrs['clock_time'] = time.time() - start
        run_log.create_dataset('integration_time_values', data=times)
        run_log.create_dataset('test_particle_values', data=run_values)

    return stats


if __name__ == '__main__':
    multi = True
    runtime = datetime.today().strftime('%Y%m%d_%H%M')
    if multi:
        ft_params = itertools.product([f'./luthera_sims/luther_sim_{sim_no:04}.bin' for sim_no in range(6)],
                                      [1.e6, 2.5e6, 5.e6, 7.5e6, 1.e7])

        params = list()
        for ptup in ft_params:
            ft_list = list(ptup)
            ft_list.append(runtime)
            params.append(ft_list)

        pool = InterruptiblePool(processes=3)
        res = pool.map(run_sim, params)
        results_df = pd.DataFrame.from_dict(res)
        results_df.to_pickle(f"./run_logs/results_{runtime}.pkl")

    else:
        res = run_sim(['./luthera_sims/luther_sim_0000.bin', 1.0e5, datetime.today().strftime('%Y%m%d_%H%M')])

