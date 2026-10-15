import os
import sys
from pathlib import Path

from datetime import timedelta
from math import floor, log10

import h5py as h5

import rebound
import numpy as np
import time
import warnings


# This function allows the simulations to be started in a
# multiprocessing Pool on a machine that isn't using PBS.
def prun_sim(params) -> bool:
    """
    The params tuple is used when calling a function through the multiprocessing Pool
    interface. Which provides multithreading without PBS. Use mainly for testing the
    simulations on a local workstation. Create the pool with maxtasksperchild=1, REBOUND 5
    can corrupt particle names when a process loads more than one simulation file.
    :param params: Dictionary of parameters to be used in run_sim call
    :return: The value from run_sim
    """
    base_dir, sim_number, int_length, max_walltime = params
    return run_sim(base_dir, sim_number, int_length, max_walltime)


def run_sim(proj_dir, sim_number, int_length, max_walltime=168.0) -> bool:
    """
    :param proj_dir: Project directory
    :param sim_number: simulation file to run
    :param int_length: Length of integration time
    :param max_walltime: Maximum runtime allowed
    :return: Last integration time, or -1 if simulation was completed.
    """
    config_nm = proj_dir.split('/')[-2]
    start = time.time()
    if sim_number.isdigit():
        sim_desig = f'{int(sim_number):05}'
    else:
        sim_desig = sim_number

    print(f"+{config_nm} {sim_desig} {int_length:.1e}")

    sim_config = initialise_config(proj_dir, int_length, sim_desig)
    sim_config['max_walltime'] = max_walltime
    stop_index = particle_simulation(sim_config, (sim_desig == 'actives'))
    sim_config['clock_time'] = time.time() - start + sim_config['clock_time']

    store_config(proj_dir, stop_index, sim_config)

    print(f"-{config_nm} {sim_desig} {int_length:.1e} stop_index:{stop_index} "
          f"Duration:{timedelta(seconds=time.time()-start)}")

    return stop_index == -1


def initialise_config(proj_dir, int_length, sim_desig):
    """
    Check for a previous log file, then initialise based on the int_length
    and contents of log file as required.
    :param proj_dir: directory for data files
    :param int_length: Length of simulation time
    :param sim_desig: name of simulation being run
    :return: simulation configuration
    """
    # Number of values we record from the rebound simulation
    vals: int = 11

    sim_config = dict()
    # setup log file
    proj_dir = Path(proj_dir)
    log_dir = proj_dir / 'results'
    sim_config['log_file'] = log_dir / f"pvals_{sim_desig}.h5"
    input_dir = proj_dir / 'inputs'
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
            sim_config['particle_names'] = run_log['particle_names'][()]

        # Check the stop index -1 == completed sim
        if sim_config['start_index'] != 0 and sim_config['int_length'] != int_length:
            # We have an unfinished simulation and an extension of integration time
            raise RuntimeError("We can't restart a simulation and extend the integration time")
        elif sim_config['start_index'] == 0 and sim_config['int_length'] != int_length:
            # The int_length from the config differs to the passed value
            # extend the run
            old_times = sim_config['times']
            log_step = old_times[1] - old_times[0]
            # We start from the last integration time, and step until past the integration year
            new_times = np.arange(old_times[-1]+log_step, (int_length*2*np.pi)+log_step, log_step)
            sim_config['times'] = np.concatenate([old_times, new_times], axis=0)
            # We start at the first time in the new time value array
            sim_config['start_index'] = len(old_times)
            # Set the new time length
            sim_config['int_length'] = int_length
            # We need to match the number of particles from the old log
            particle_dims = sim_config['particle_values'].shape
            new_particle_log = np.zeros((len(new_times), particle_dims[1], vals))
            # Join the arrays
            sim_config['particle_values'] = np.concatenate([sim_config['particle_values'], new_particle_log], axis=0)
            new_name_log = np.zeros((len(new_times), particle_dims[1]), dtype=sim_config['particle_names'].dtype)
            sim_config['particle_names'] = np.concatenate([sim_config['particle_names'], new_name_log], axis=0)
            # Extend the energy array
            sim_config['sim_energy_values'] = np.concatenate([sim_config['sim_energy_values'],
                                                              np.zeros(len(new_times))],
                                                             axis=0)
        # Open the REBOUND file
        sim_file = str(log_dir / f"sim_{sim_desig}_fin.bin")
        sim_config['sim'] = rebound.Simulation(sim_file)
        # The saved sim matches the last logged step (index -1 when the run completed)
        last_names = [n.decode('utf-8') for n in sim_config['particle_names'][sim_config['start_index'] - 1]]
        check_particle_names(sim_config['sim'], sim_desig == 'actives', last_names)

    else:
        # We're starting a new simulation
        sim_file = str(input_dir / f"sim_{sim_desig}.bin")
        sim_config['sim'] = rebound.Simulation(sim_file)
        check_particle_names(sim_config['sim'], sim_desig == 'actives')
        sim_config['sim_desig'] = sim_desig
        sim_config['int_length'] = int_length
        sim_config['start_index'] = 0
        sim_config['clock_time'] = 0

        # record the number of particles. N_active is SIZE_MAX when it hasn't been set
        sim = sim_config['sim']
        if sim.N_active < sim.N:
            n_particles = sim.N - sim.N_active
        else:
            n_particles = sim.N - 1

        # Create evenly spaced integration log times
        exp = floor(log10(int_length))
        if exp >= 6:
            log_time = int(int_length / pow(10, exp-4))
        else:
            log_time = int(int_length / 1.0e3)

        # Integrate for run_length years
        sim_config['times'] = np.linspace(log_time, int_length * 2 * np.pi, log_time)
        sim_config['particle_values'] = np.zeros((log_time, n_particles, vals))
        # Name of the particle in each particle_values row, empty if the row is empty
        name_len = max([len(p.name.encode('utf-8')) for p in sim.particles if p.name] + [1])
        sim_config['particle_names'] = np.zeros((log_time, n_particles), dtype=f'S{name_len}')
        sim_config['sim_energy_values'] = np.zeros(log_time)

    return sim_config


def store_config(base_dir, stop_index, sim_config):
    """
    Store the particle orbital values into an HDF log file
    :param base_dir: project directory
    :param stop_index: last integration step (-1 if completed)
    :param sim_config: simulation configuration values to be stored
    :return: None
    """
    # setup log file
    log_dir = f'{base_dir}results/'
    sim_config['sim'].save_to_file(f"{log_dir}sim_{sim_config['sim_desig']}_fin.bin")
    with h5.File(sim_config['log_file'], 'w') as run_log:
        run_log.attrs['simulation'] = sim_config['sim_desig']
        run_log.attrs['int_length'] = sim_config['int_length']
        run_log.attrs['start_index'] = stop_index + 1  # The next timestep is where we start
        run_log.attrs['clock_time'] = sim_config['clock_time']
        run_log.create_dataset('integration_time_values', data=sim_config['times'])
        run_log.create_dataset('sim_energy_values', data=sim_config['sim_energy_values'])
        run_log.create_dataset('particle_values', data=sim_config['particle_values'])
        run_log.create_dataset('particle_names', data=sim_config['particle_names'])


def first_logged_particle(sim, actives):
    """
    :param sim: REBOUND simulation
    :param actives: True for the planets only simulation
    :return: index of the first particle written to the log
    """
    if actives or sim.N_active >= len(sim.particles):
        # No test particles, so log everything except the Sun
        return 1
    return sim.N_active


def check_particle_names(sim, actives, logged_names=None):
    """
    REBOUND 5 can corrupt particle names when a process loads more than one simulation
    file. Stop rather than log values against the wrong asteroid.
    :param sim: REBOUND simulation loaded from file
    :param actives: True for the planets only simulation
    :param logged_names: names from the last logged step when restarting
    :return: None
    """
    names = [p.name or '' for p in sim.particles[first_logged_particle(sim, actives):]]
    named = [n for n in names if n]
    if logged_names is not None:
        # Rows after the remaining particles are empty in the log
        names = names + [''] * (len(logged_names) - len(names))
    if len(set(named)) != len(named) or (logged_names is not None and names != logged_names):
        raise RuntimeError("Particle names in the simulation file are corrupted. REBOUND 5 can do this when a "
                           "process loads more than one simulation, run each simulation in its own process.")


def particle_simulation(sim_config, actives=False):
    """
    Manage the REBOUND simulation.
    :param sim_config: simulation configuration values
    :param actives: True if there are no particles to be logged.
    :return:
    """
    run_values = sim_config['particle_values']
    run_names = sim_config['particle_names']
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
    start_particle = first_logged_particle(sim, actives)

    # Capture warning messages
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for ti in range(start_index, len(times)):
            sim.integrate(times[ti], exact_finish_time=0)
            sim_energy_values[ti] = sim.energy()
            for i, p in enumerate(sim.particles[start_particle:]):
                # Particles shift rows when one is removed, so record who is in each row
                run_names[ti][i] = p.name.encode('utf-8') if p.name else b''
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
