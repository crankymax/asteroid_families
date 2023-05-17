import os
import sys

import itertools
from datetime import datetime, timedelta
import h5py as h5
import pandas as pd

import rebound
import numpy as np
import time
import warnings


def sim_particle_system(base_dir, sim_number, int_length, max_walltime=168) -> bool:
    start = time.time()
    sim_desig = f'{sim_number:05}'
    print(f"{sim_desig} {int_length:.1e}")

    sim_config = initialise_config(base_dir, int_length, sim_desig)
    sim_config['max_walltime'] = max_walltime
    stop_index = particle_simulation(sim_config)
    sim_config['clock_time'] = time.time() - start + sim_config['clock_time']

    store_config(stop_index, sim_config)

    print(f"{sim_desig} {int_length:.1e} stop_index:{stop_index} "
          f"Duration:{timedelta(seconds=time.time()-start)}")

    return stop_index == -1


def sim_base_system(base_dir, int_length, max_walltime=168) -> bool:
    start = time.time()
    print(f"actives {int_length:.1e}")

    sim_config = initialise_config(base_dir, int_length, 'actives')
    sim_config['max_walltime'] = max_walltime
    stop_index = base_simulation(sim_config)
    store_config(stop_index, sim_config)

    print(f"{sim_no} {int_length:.1e} stop_index:{stop_index} "
          f"Duration:{timedelta(seconds=time.time()-start)}")

    return stop_index == -1


def initialise_config(base_dir, int_length, sim_desig):
    sim_config = dict()

    # setup log file
    log_dir = f'{base_dir}results/'
    sim_config['log_file'] = f"{log_dir}pvals_{sim_desig}.h5"
    input_dir = f'{base_dir}inputs/'
    # Check for a current log file
    if os.path.exists(sim_config['log_file']):
        # We have a log file so crack it open
        with h5.File(sim_config['log_file'], 'r') as run_log:
            sim_config['sim_desig'] = run_log.attrs['simulation']
            sim_config['int_length'] = run_log.attrs['int_length']
            sim_config['start_index'] = run_log.attrs['start_index']
            sim_config['clock_time'] = run_log.attrs['clock_time']
            sim_config['times'] = run_log['integration_time_values'][()]
            sim_config['sim_energy_values'] = run_log['sim_energy_values'][()]
            sim_config['particle_values'] = run_log['particle_values'][()]
        sim_file = f'{log_dir}sim_{sim_desig}_fin.bin'
        sim_config['sim'] = rebound.Simulation(sim_file)
    else:
        sim_file = f'{input_dir}sim_{sim_desig}.bin'
        sim_config['sim'] = rebound.Simulation(sim_file)
        sim_config['sim_desig'] = sim_desig
        sim_config['int_length'] = int_length
        sim_config['start_index'] = 0
        sim_config['clock_time'] = 0

        # record the number of particles
        n_particles = len(sim_config['sim'].particles) - sim_config['sim'].N_active

        # Create evenly spaced integrations every run_length/1000
        log_time = int(int_length / 1.0e3)
        vals: int = 11

        # Integrate for run_length years
        sim_config['times'] = np.linspace(log_time, int_length * 2 * np.pi, log_time)
        sim_config['particle_values'] = np.zeros((log_time, n_particles, vals))
        sim_config['sim_energy_values'] = np.zeros(log_time)

    return sim_config


def store_config(stop_index, sim_config):
    with h5.File(sim_config['log_file'], 'w') as run_log:
        run_log.attrs['simulation'] = sim_config['sim_desig']
        run_log.attrs['int_length'] = sim_config['int_length']
        run_log.attrs['start_index'] = stop_index + 1  # The next timestep is where we start
        run_log.attrs['clock_time'] = sim_config['clock_time']
        run_log.create_dataset('integration_time_values', data=sim_config['times'])
        run_log.create_dataset('sim_energy_values', data=sim_config['sim_energy_values'])
        run_log.create_dataset('particle_values', data=sim_config['particle_values'])


def particle_simulation(sim_config):
    run_values = sim_config['particle_values']
    sim = sim_config['sim']
    sim_energy_values = sim_config['sim_energy_values']
    times = sim_config['times']

    walltime_start = time.time()
    walltime_cutoff = sim_config['max_walltime'] * 3600  # Convert hours to seconds
    start_index = sim_config['start_index']
    step_lengths = 0

    # Capture warning messages (e.g. WHFast timestep too large)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for ti in range(start_index, len(times)-1):
            start_step = time.time()
            sim.integrate(times[ti], exact_finish_time=0)
            sim_energy_values[ti] = sim.calculate_energy()
            step_lengths += time.time() - start_step
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
                run_values[ti][i][9] = p.omega
                run_values[ti][i][10] = p.Omega

            safety_margin = (step_lengths/(ti-start_index+1))*10
            # Check walltime
            if (time.time() - walltime_start) > (walltime_cutoff - safety_margin):
                return ti
    return -1


def base_simulation(sim_config):
    return -1


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) >= 4:
        sim_no = int(sys.argv[1])
        run_length = float(sys.argv[2])
        inp_dir = sys.argv[3]
        if len(sys.argv) == 5:
            max_walltime = int(sys.argv[4])
        else:
            max_walltime = 168
        print(f'parameters {sim_no} {run_length} {inp_dir}')
        sim_particle_system(inp_dir, sim_no, run_length, max_walltime)
        exit(0)
    else:
        print('Incorrect parameters specified.\n Required parameters are: '
              '(simulation number) (integration length) (input directory)')
        exit(1)
