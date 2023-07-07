import sys

from subprocess import Popen, PIPE

import pandas as pd


def rerun_jobs(sim_dir, project_dir, walltime, integration_time, cmd="qsub"):
    # All the sims have been run, we now want to extend the integration time for all the
    # simulations that have been run.
    # The maximum array size cuts down on the number of PBS jobs in the queue and allows
    # for easier management. When we're dropping the simulations that have lost all clones
    # we need to work around those.
    max_array_size = 120
    start_sim = 0
    end_sim = 19050
    queue = 'albus'

    # Setup the jobs to restart
    # Create a list of simulations that have all clones escaped
    dont_run = [int(x) for x in check_lost_clones(sim_dir, project_dir)]
    current_sim = start_sim
    while current_sim < end_sim:
        skip = dont_run[0] if dont_run else None
        if skip and skip == current_sim:
            current_sim = skip+1
            dont_run.pop(0)
            continue
        elif skip and skip < (current_sim + max_array_size-1):
            # Truncate the batch to before the left out one
            job_range = f"{current_sim}-{skip-1}"
            current_sim = skip+1
            dont_run.pop(0)
        elif (current_sim + max_array_size-1) < end_sim:
            job_range = f"{current_sim}-{current_sim + max_array_size-1}"
            current_sim += max_array_size
        else:
            job_range = f"{current_sim}-{end_sim}"
            current_sim = end_sim

        if queue == 'albus':
            queue = 'default'
        else:
            queue = 'albus'

        create_pbs_job(job_range, sim_dir, cmd=cmd, walltime=walltime, int_time=integration_time, queue=queue)


def check_lost_clones(sim_dir, project_dir):
    # Read the escaped asteroids file
    ea_mvc3 = pd.read_hdf(sim_dir + project_dir + '/escaped_asteroids.h5')
    sim_particles = ea_mvc3[['sim_no', 'particle_number']].drop_duplicates()
    # Find which simulations have lost all three clones
    sim_groups = sim_particles.groupby('sim_no').agg(Count_Sim=('sim_no', 'count')).apply(lambda x: x == 3)

    dont_run = sim_groups[sim_groups.Count_Sim].index.values

    return dont_run


def create_pbs_job(job_range, project_dir, cmd="qsub", walltime="72:00:00", int_time='1.0e9', queue='default'):
    # Open a pipe to the qsub command.
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE)

    # Customize your options here
    job_string = f"""#!/bin/bash -l
        #PBS -N mc_pm6_prod
        
        #PBS -q {queue}
        #PBS -l select=1:ncpus=1:mem=2gb
        #PBS -l walltime={walltime}
        
        # Set the job array size
        #PBS -J {job_range}
        
        #PBS -P 0201-BWALKER
        #PBS -o asteroid_sim/mc_pm6_3/console/
        #PBS -j oe
        
        # Change to the python rebound module
        module load python/3.9.13-gcc8.3.1-jhn 
        
        # Change to the asteroids directory
        cd {project_dir}
        
        # python command line
        python rebound_run_sim.py $PBS_ARRAY_INDEX {int_time} ./mc_pm6_3/ {walltime}
        """

    # Send job_string to qsub
    p.stdin.write(job_string.encode())
    batch_code = p.communicate()[0]
    print(f"Simulation range {job_range} is batch_code {batch_code} ")


if __name__ == '__main__':
    print(sys.argv)
    rerun_jobs(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
