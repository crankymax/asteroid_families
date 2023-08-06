import os
import sys
from pathlib import Path

from subprocess import Popen, PIPE


def create_run_jobs(start_sim, end_sim, array_size, project_dir, cmd='qsub'):
    # ['default', '24'], ['default', '160'],
    queues = [['default', '72']]
    q_i = 0
    q_l = len(queues)

    current_sim = start_sim
    while current_sim < end_sim:
        if (current_sim + array_size-1) < end_sim:
            job_range = f"{current_sim}-{current_sim + array_size-1}"
            current_sim += array_size-1
        else:
            job_range = f"{current_sim}-{end_sim}"
            current_sim = end_sim

        queue = queues[(q_i % q_l)]
        q_i += 1
        create_pbs_job(job_range, project_dir, cmd=cmd, queue=queue[0], walltime=queue[1])


def create_pbs_job(job_range, parent_dir, walltime="72", int_time='3.0e9', queue='default', cmd='qsub'):
    # Open a pipe to the qsub command.
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE)

    # Customize your options here
    job_string = f"""#!/bin/bash -l
        #PBS -N mc_pm6_prod
        
        #PBS -q {queue}
        #PBS -l select=1:ncpus=1:mem=2gb
        #PBS -l walltime={walltime}:00:00
        
        # Set the job array size
        #PBS -J {job_range}
        
        #PBS -P 0201-BWALKER
        #PBS -o asteroid_sim/mc_pm6_3/console/
        #PBS -j oe
        
        # Change to the python rebound module
        module load python/3.9.13-gcc8.3.1-jhn 
        
        # Change to the asteroids directory
        cd {parent_dir}
        
        # python command line
        python rebound_run_sim.py $PBS_ARRAY_INDEX {int_time} ./mc_pm6_3/ {walltime}
        """

    # Send job_string to qsub
    print(f'submitting {job_range} to {queue} for {walltime}')
    p.stdin.write(job_string.encode())
    batch_code = p.communicate()[0]
    print(f"batch_code {batch_code} ")


if __name__ == '__main__':
    print(sys.argv)
    create_run_jobs(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
