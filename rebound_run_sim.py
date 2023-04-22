import os
import sys

import itertools
from datetime import datetime
import h5py as h5
import pandas as pd

import rebound
import numpy as np
import time
import warnings


def run_sim(input_dir, sim_no, run_length) -> dict:
    sim_file = f'{input_dir}sim_{sim_no:05}.bin'
    sim = rebound.Simulation(sim_file)

    # setup log directory
    run_time = datetime.today().strftime('%Y%m%d_%H%M')
    log_dir = f'{input_dir}results/'
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

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
    print(f"{run_time}+{sim_no} {run_length:.1e}")
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

    sim.save(f'{log_dir}sim_{sim_no:05}_fin.bin')
    print(f"{run_time}-{sim_no} {run_length:.1e} length:{time.time()-start}")

    with h5.File(f"{log_dir}/pvals_{run_time}_{sim_no:02}.h5", 'w') as run_log:
        run_log.attrs['simulation'] = sim_no
        run_log.attrs['int_length'] = run_length
        run_log.attrs['clock_time'] = time.time() - start
        run_log.create_dataset('integration_time_values', data=times)
        run_log.create_dataset('test_particle_values', data=run_values)


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) == 4:
        sim_no = int(sys.argv[1])
        run_length = float(sys.argv[2])
        inp_dir = sys.argv[3]
        print(f' {sim_no} {run_length} {inp_dir}')
        run_sim(inp_dir, sim_no, run_length)
        exit(0)
    else:
        res = run_sim('./luthera_7p_5t_c/', 0, 1.0e5)

