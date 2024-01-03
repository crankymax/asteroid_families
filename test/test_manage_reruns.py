from unittest import TestCase
from manage_runs import create_run_jobs, rerun_errors


class RerunsTest(TestCase):
    def test_run_array_jobs(self):
        project_dir = '../../asteroid_data/mc_pm6_3'
        walltime = '72'
        integration_time = '2.0e9'
        start_sim = 0
        end_sim = 100
        array_size = 10
        create_run_jobs(start_sim, end_sim, array_size, project_dir, walltime, integration_time, cmd="./qsub")

    def test_run_errors(self):
        project_dir = '/Volumes/fua/asteroid_sim/fawkes/mc_pm6_3'
        error_file = '/Volumes/fua/asteroid_sim/fawkes/mc_pm6_3/rerun_jobs'

        rerun_errors(error_file, project_dir, cmd="./qsub")

