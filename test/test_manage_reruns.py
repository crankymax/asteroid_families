from unittest import TestCase
from manage_reruns import rerun_jobs


class RerunsTest(TestCase):
    def test_rerun_jobs(self):
        sim_dir = '../../asteroid_data/'
        project_dir = 'mc_pm6_3'
        walltime = '72'
        integration_time = '2.0e9'

        rerun_jobs(sim_dir, project_dir, walltime, integration_time, cmd="./qsub")
