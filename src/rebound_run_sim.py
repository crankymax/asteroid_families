import os
import sys

from datetime import timedelta
from math import floor, log10

import h5py as h5

import rebound
import numpy as np
import time
import warnings


def run_sim(base_dir, sim_number, int_length, max_walltime=168.0) -> bool:
    start = time.time()
    if sim_number.isdigit():
        sim_desig = f'{int(sim_number):05}'
    else:
        sim_desig = sim_number

    print(f"{sim_desig} {int_length:.1e}")

    sim_config = initialise_config(base_dir, int_length, sim_desig)
    sim_config['max_walltime'] = max_walltime
    stop_index = particle_simulation(sim_config, (sim_desig == 'actives'))
    sim_config['clock_time'] = time.time() - start + sim_config['clock_time']

    store_config(base_dir, stop_index, sim_config)

    print(f"{sim_desig} {int_length:.1e} stop_index:{stop_index} "
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
        print(f"Restarting simulation {sim_desig}")
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
        if len(sim_config['sim'].particles) - sim_config['sim'].N_active > 0:
            n_particles = len(sim_config['sim'].particles) - sim_config['sim'].N_active
        else:
            n_particles = sim_config['sim'].N_active - 1

        # Create evenly spaced integrations log times
        exp = floor(log10(int_length))
        if exp >= 6:
            log_time = int(int_length / pow(10, exp-4))
        else:
            log_time = int(int_length / 1.0e3)

        vals: int = 11

        # Integrate for run_length years
        sim_config['times'] = np.linspace(log_time, int_length * 2 * np.pi, log_time)
        sim_config['particle_values'] = np.zeros((log_time, n_particles, vals))
        sim_config['sim_energy_values'] = np.zeros(log_time)

    return sim_config


def store_config(base_dir, stop_index, sim_config):
    # setup log file
    log_dir = f'{base_dir}results/'
    sim_config['sim'].save(f"{log_dir}sim_{sim_config['sim_desig']}_fin.bin")
    with h5.File(sim_config['log_file'], 'w') as run_log:
        run_log.attrs['simulation'] = sim_config['sim_desig']
        run_log.attrs['int_length'] = sim_config['int_length']
        run_log.attrs['start_index'] = stop_index + 1  # The next timestep is where we start
        run_log.attrs['clock_time'] = sim_config['clock_time']
        run_log.create_dataset('integration_time_values', data=sim_config['times'])
        run_log.create_dataset('sim_energy_values', data=sim_config['sim_energy_values'])
        run_log.create_dataset('particle_values', data=sim_config['particle_values'])


def particle_simulation(sim_config, actives=False):
    run_values = sim_config['particle_values']
    sim = sim_config['sim']
    sim_energy_values = sim_config['sim_energy_values']
    times = sim_config['times']

    walltime_start = time.time()
    walltime_cutoff = sim_config['max_walltime'] * 3600  # Convert hours to seconds
    # Give the code 30 minutes to write out the log files and simulations
    # Tried being smart, lost 7 days due to process getting terminated as the data was written :(
    if walltime_cutoff > 3600:
        safety_margin = 3600 / 2
    else:
        safety_margin = walltime_cutoff * 0.05

    start_index = sim_config['start_index']
    if actives:
        start_particle = 1
    else:
        start_particle = sim.N_active

    # Capture warning messages (e.g. WHFast timestep too large)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for ti in range(start_index, len(times)):
            start_step = time.time()
            sim.integrate(times[ti], exact_finish_time=0)
            sim_energy_values[ti] = sim.calculate_energy()
            for i, p in enumerate(sim.particles[start_particle:]):
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

            # Check walltime
            if (time.time() - walltime_start) > (walltime_cutoff - safety_margin):
                return ti
    return -1


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) >= 4:
        if sys.argv[1] == 'actives':
            sim_no = 'actives'
        else:
            sim_no = sys.argv[1]

        run_length = float(sys.argv[2])
        inp_dir = sys.argv[3]
        if len(sys.argv) == 5:
            max_walltime = float(sys.argv[4])
        else:
            max_walltime = 168.0
        print(f'parameters {sim_no} {run_length} {inp_dir}')
        exit(run_sim(inp_dir, sim_no, run_length, max_walltime))

    else:
        print('Incorrect parameters specified.\n Required parameters are: '
              '(simulation number) (integration length) (input directory) (max wall time)')
        exit(1)
