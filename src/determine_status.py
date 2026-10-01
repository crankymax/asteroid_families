import os
import sys
from pathlib import Path

import h5py as h5
import numpy as np
import rebound


def determine_status(project, target_int_length=4.5e9, action=True):
    sim_rerun = list()
    print(f"Target integration length is: {target_int_length:0.4e}")

    inputs = project / 'inputs'
    results = project / 'results'
    for sim_file in inputs.glob(r'*.bin'):
        if not sim_file.name[4:9].isdigit():
            print(f'Skipped {sim_file.name}')
            continue

        # check the length and open the file
        if sim_file.stat().st_size < 1024:
            print(f'Sim file {sim_file.name} has a length of {sim_file.stat().st_size} regenerate config')
            continue

        # Open the file to check
        try:
            sim_config = rebound.Simulation(str(sim_file))
            sim_config = None
        except OSError as prob:
            print(f"We got a problem {prob} with {sim_file.name} regenerate config")
            continue

        # Check the final sim file
        sim_desig = sim_file.name[4:9]
        sim_final_file = results / f'sim_{sim_desig}_fin.bin'
        log_file = results / f'pvals_{sim_desig}.h5'

        if not sim_final_file.exists() or sim_final_file.stat().st_size < 1024:
            print(f'Sim final {sim_final_file.name}  is too small or does not exist delete pvals and rerun')
            sim_rerun.append(sim_desig)
            if action:
                restart_sim(log_file, sim_desig, sim_final_file)
            continue

        # Open the final sim file to check
        try:
            sim_config = rebound.Simulation(str(sim_final_file))
            if sim_config.t / (2 * np.pi) < target_int_length:
                print(f'Sim {sim_final_file.name} has sim time of {sim_config.t / (2 * np.pi)}, rerun')
                sim_rerun.append(sim_desig)
                if action:
                    restart_sim(log_file, sim_desig, sim_final_file)
            sim_config = None
        except OSError as prob:
            print(f"We got a problem {prob} with {sim_final_file.name} rerun")
            sim_rerun.append(sim_desig)
            if action:
                restart_sim(log_file, sim_desig, sim_final_file)
            continue

        try:
            simulation_log = h5.File(log_file, 'r')
            if simulation_log.attrs['int_length'] != -1 and target_int_length != simulation_log.attrs['int_length']:
                print(f'Particle log file  {log_file.name} has a time of {simulation_log.attrs["int_length"]}, rerun')
                sim_rerun.append(sim_desig)
                if action:
                    restart_sim(log_file, sim_desig, sim_final_file)
                continue
            elif simulation_log.attrs['int_length'] == -1:
                print(f'Particle log file  {log_file.name} has not completed, continue to run')
                sim_rerun.append(sim_desig)

        except OSError as prob:
            print(f"We got a problem {prob} with {sim_final_file.name} \n delete pvals and rerun")
            sim_rerun.append(sim_desig)
            if action:
                restart_sim(log_file, sim_desig, sim_final_file)
            continue

    job_nos = open('rerun_jobs', 'w')
    for rerun in sim_rerun:
        job_nos.write(f"{rerun}\n")
    job_nos.close()


def safe_remove(file_name):
    if file_name.exists():
        os.remove(file_name)


def restart_sim(log_file, sim_desig, sim_final_file):
    safe_remove(sim_final_file)
    safe_remove(log_file)


if __name__ == '__main__':
    print(sys.argv)
    project_dir = Path(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == 'report':
        action = False
    else:
        action = True
    determine_status(project_dir, action=action)
