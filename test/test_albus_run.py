import unittest

import manage_runs


class AlbusRun(unittest.TestCase):
    test_dir = '../../asteroid_data/sim_data/mvc_3/'
    def test_find_input_files(self):
        manage_runs.create_pbs_job(self.test_dir)

    def test_create_run_jobs(self):
        start_sim = 0
        end_sim = 19044
        array_size = 120
        parent_dir = self.test_dir
        manage_runs.create_run_jobs(start_sim, end_sim, array_size, parent_dir, cmd='./qsub')


if __name__ == '__main__':
    unittest.main()
