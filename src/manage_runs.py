import sys

from subprocess import Popen, PIPE


def create_run_jobs(start_sim, end_sim, array_size, project_dir, cmd='qsub'):
    """
    This function creates a number of PBS array jobs starting at the start_sim number
    and finishing at end_sim. Each array job covers the array_size number. This splits
    the thousands of possible PBS jobs into hundreds of PBS array jobs, which eases the
    administration load of the cluster.

    :param start_sim: lowest number simulation
    :param end_sim: last value simulation
    :param array_size: number of simulations each job will start
    :param project_dir: the directory for the project
    :param cmd: this is used for unit testing without PBS
    :return: None
    """
    # Abandoned concept to allow different queues to be used.
    # ['default', '24'], ['default', '168'],
    queues = [['default', '48']]
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


def rerun_errors(job_numbers, project_dir, cmd='qsub'):
    """
    If the simulations encounter errors (disk full etc.) this function
    will take a list of simulations that required a restart.
    :param job_numbers: List of simulation numbers
    :param project_dir: Directory containing the simulations
    :param cmd: Unit testing parameter
    :return: None
    """
    with open(job_numbers) as jobs_2run:
        for job_no in jobs_2run:
            if job_no.strip():
                job_restart(job_no.strip(), project_dir, cmd=cmd)


def job_restart(job_number, parent_dir, walltime="168", int_time='4.5e9', queue='default', cmd='qsub'):
    """
    Creates a PBS job for a simulation that requires restarting. This function is used when a simulation
    has and error and must restart. It is still 'hard wired' to a couple of values like directory and
    python module.
    :param job_number: simulation number
    :param parent_dir: simulation directory
    :param walltime: Maximum time the simulation will run before saving and exiting
    :param int_time: Time the simulation will integrate over
    :param queue: PBS queue that the simulations will be submitted to
    :param cmd: Unit testing parameter
    :return:
    """
    # Open a pipe to the qsub command.
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE)

    # Customize your options here
    job_string = f"""#!/bin/bash -l
        #PBS -N luthera_45gyr_fix

        #PBS -q {queue}
        #PBS -l select=1:ncpus=1:mem=4gb
        #PBS -l walltime={walltime}:00:00

        #PBS -P 0201-BWALKER
        #PBS -o asteroid_sim/{parent_dir}console/
        #PBS -j oe

        # Change to the python rebound module
        module load python/3.9.13-gcc-jhn 

        # Change to the asteroids directory
        cd asteroid_sim

        # python command line 
        python rebound_run_sim.py {job_number} {int_time} {parent_dir} {walltime}
        """

    # Send job_string to qsub
    print(f'submitting {job_number} to {queue} for {walltime}')
    p.stdin.write(job_string.encode())
    batch_code = p.communicate()[0]
    print(f"batch_code {batch_code} ")


def create_pbs_job(job_range, parent_dir, walltime="72", int_time='4.5e9', queue='default', cmd='qsub'):
    """
    Each of the array jobs created in the 'create_run_jobs' function are submitted to PBS in this
    function.
    :param job_range: The simulations that will be run by this array job
    :param parent_dir: Directory containing simulation
    :param walltime: Maximum time the simulation will run before saving and exiting
    :param int_time: Time the simulation will integrate over
    :param queue: PBS queue that the simulations will be submitted to
    :param cmd: Unit testing parameter
    :return:
    """
    # Open a pipe to the qsub command.
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE)

    # Customize your options here
    job_string = f"""#!/bin/bash -l
        #PBS -N luthera_45gyr_fix
        
        #PBS -q {queue}
        #PBS -l select=1:ncpus=1:mem=4gb
        #PBS -l walltime={walltime}:00:00
        
        # Set the job array size
        #PBS -J {job_range}
        
        #PBS -P 0201-BWALKER
        #PBS -o asteroid_sim/{parent_dir}/console/
        #PBS -j oe
        
        # Change to the python rebound module
        module load python/3.9.13-gcc-jhn 
        
        # Change to the asteroids directory
        cd asteroid_sim
        
        # python command line
        python rebound_run_sim.py $PBS_ARRAY_INDEX {int_time} . {walltime}
        """

    # Send job_string to qsub
    print(f'submitting {job_range} to {queue} for {walltime}')
    p.stdin.write(job_string.encode())
    batch_code = p.communicate()[0]
    print(f"batch_code {batch_code} ")


if __name__ == '__main__':
    print(sys.argv)
    if sys.argv[1].isdigit():
        create_run_jobs(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    else:
        rerun_errors(sys.argv[1], sys.argv[2])
