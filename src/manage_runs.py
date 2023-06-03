import os
import sys
from pathlib import Path

from subprocess import Popen, PIPE


def create_run_jobs(start_sim, end_sim, array_size, parent_dir):
    current_sim = start_sim
    while current_sim < end_sim:
        if (current_sim + array_size-1) < end_sim:
            job_range = f"{current_sim}-{current_sim + array_size-1}"
            current_sim += array_size-1
        else:
            job_range = f"{current_sim}-{end_sim}"
            current_sim = end_sim
        create_pbs_job(job_range, parent_dir)


def check_input_files(parent_dir):
    input_dir = Path(parent_dir, 'inputs')
    for pv_file in input_dir.glob('sim_*.bin'):
        if 'actives' in str(pv_file):
            print(pv_file)
        else:
            print(f"Groot to go:{pv_file}")


def create_pbs_job(job_range, parent_dir):
    # Open a pipe to the qsub command.
    p = Popen("./qsub", shell=True, stdin=PIPE, stdout=PIPE)

    # Customize your options here
    job_string = f"""#!/bin/bash -l
        #PBS -N mvc3_particles_test
        
        #PBS -q albus
        #PBS -l select=1:ncpus=1:mem=2gb
        #PBS -l walltime=168:00:00
        
        # Set the job array size
        #PBS -J {job_range}
        
        #PBS -P 0201-BWALKER
        #PBS -o asteroid_sim/mvc_3/console/
        #PBS -j oe
        
        # Change to the python rebound module
        module load python/3.9.13-gcc8.3.1-jhn 
        
        # Change to the asteroids directory
        cd {parent_dir}
        
        # python command line
        python rebound_run_sim.py $PBS_ARRAY_INDEX 1.0e9 ./mvc_3/ 168.0
        """

    # Send job_string to qsub
    print('submitting')
    p.stdin.write(job_string.encode())
    batch_code = p.communicate()[0]
    print(f"batch_code {batch_code} cwd {os.getcwd()}")


if __name__ == '__main__':
    print(sys.argv)
    create_run_jobs(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), 'asteroid_sim/')
